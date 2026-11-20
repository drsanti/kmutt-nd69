/*
 * Week 08 - audio-logger
 *
 * Waits for one-byte commands from labs/python/collect.py on the native USB
 * Serial/JTAG port and answers with text lines or binary audio frames:
 *
 *   'p'  -> "PONG KWS-LOGGER v1\n"
 *   'i'  -> "INFO slot0_dbfs=<L> slot1_dbfs=<R> mic_slot=<n> gain_db=<g>\n"  (0.5 s level per I2S slot)
 *   'r'  -> b"KWS1" | uint32 n_samples | uint32 sample_rate | int16 pcm[n] | uint32 checksum
 *           (little-endian, 1.5 s mono at 16 kHz, checksum = sum of pcm bytes mod 2^32)
 *
 * The host trims each 1.5 s take to the loudest 1.0 s, so the speaker does not need
 * perfect timing. Keep MIC_GAIN_DB identical in kws-inference: gain is part of the
 * data distribution the model learns.
 */
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "driver/usb_serial_jtag.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "es3c28p_audio.h"

#define MIC_GAIN_DB      30.0f
#define MIC_SLOT         0                       /* change to 1 if 'i' shows the mic on slot 1 */
#define TAKE_SAMPLES     (ES3C28P_SAMPLE_RATE * 3 / 2)   /* 1.5 s */
#define INFO_FRAMES      (ES3C28P_SAMPLE_RATE / 2)       /* 0.5 s */

static const char *TAG = "kws_logger";
static int16_t s_take[TAKE_SAMPLES];             /* 48 KB, static so it never sits on a task stack */

static void usb_write_all(const void *data, size_t len)
{
    const uint8_t *p = data;
    while (len > 0) {
        int n = usb_serial_jtag_write_bytes(p, len, pdMS_TO_TICKS(1000));
        if (n <= 0) {
            return;   /* host not reading: drop rather than block forever */
        }
        p += n;
        len -= (size_t)n;
    }
}

static void usb_print(const char *line)
{
    usb_write_all(line, strlen(line));
}

static void send_take(void)
{
    if (es3c28p_audio_read_mono(s_take, TAKE_SAMPLES) != ESP_OK) {
        usb_print("ERR read\n");
        return;
    }
    uint32_t header[2] = { TAKE_SAMPLES, ES3C28P_SAMPLE_RATE };
    uint32_t checksum = 0;
    const uint8_t *bytes = (const uint8_t *)s_take;
    for (size_t i = 0; i < sizeof(s_take); i++) {
        checksum += bytes[i];
    }
    usb_write_all("KWS1", 4);                      /* ESP32-S3 is little-endian, like the protocol */
    usb_write_all(header, sizeof(header));
    usb_write_all(s_take, sizeof(s_take));
    usb_write_all(&checksum, sizeof(checksum));
}

static void send_info(void)
{
    static int16_t stereo[2 * 160];
    double sum[2] = { 0 };
    for (int done = 0; done < INFO_FRAMES; done += 160) {
        if (es3c28p_audio_read_stereo(stereo, 160) != ESP_OK) {
            usb_print("ERR read\n");
            return;
        }
        for (int i = 0; i < 160; i++) {
            for (int ch = 0; ch < 2; ch++) {
                double x = stereo[2 * i + ch] / 32768.0;
                sum[ch] += x * x;
            }
        }
    }
    char line[128];
    snprintf(line, sizeof(line), "INFO slot0_dbfs=%.1f slot1_dbfs=%.1f mic_slot=%d gain_db=%.1f\n",
             20.0 * log10(sqrt(sum[0] / INFO_FRAMES) + 1e-6), 20.0 * log10(sqrt(sum[1] / INFO_FRAMES) + 1e-6),
             MIC_SLOT, MIC_GAIN_DB);
    usb_print(line);
}

void app_main(void)
{
    usb_serial_jtag_driver_config_t usb_cfg = USB_SERIAL_JTAG_DRIVER_CONFIG_DEFAULT();
    usb_cfg.tx_buffer_size = 4096;
    usb_cfg.rx_buffer_size = 256;
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb_cfg));

    es3c28p_audio_config_t audio_cfg = { .gain_db = MIC_GAIN_DB, .mic_slot = MIC_SLOT };
    ESP_ERROR_CHECK(es3c28p_audio_init(&audio_cfg));
    ESP_LOGW(TAG, "ready: send 'p', 'i' or 'r'");   /* WARN level so it is visible with quiet logs */

    uint8_t cmd;
    for (;;) {
        if (usb_serial_jtag_read_bytes(&cmd, 1, portMAX_DELAY) != 1) {
            continue;
        }
        switch (cmd) {
        case 'p': usb_print("PONG KWS-LOGGER v1\n"); break;
        case 'i': send_info(); break;
        case 'r': send_take(); break;
        default: break;   /* ignore newlines and anything else */
        }
    }
}
