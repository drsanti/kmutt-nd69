#include <stdlib.h>
#include "es3c28p_audio.h"

#include <string.h>
#include "driver/gpio.h"
#include "driver/i2s_std.h"
#include "esp_check.h"
#include "esp_log.h"

#include "esp_codec_dev.h"
#include "esp_codec_dev_defaults.h"
#include "es8311_codec.h"

static const char *TAG = "es3c28p_audio";

static i2c_master_bus_handle_t s_i2c_bus;
static i2s_chan_handle_t s_rx;
static esp_codec_dev_handle_t s_mic;
static int s_mic_slot;

#define CHUNK_FRAMES 160   /* 10 ms of stereo frames per internal read */

static esp_err_t init_i2c(void)
{
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = ES3C28P_I2C_SDA,
        .scl_io_num = ES3C28P_I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    return i2c_new_master_bus(&bus_cfg, &s_i2c_bus);
}

static esp_err_t init_i2s_rx(void)
{
    /* ESP32-S3 is the I2S master and drives MCLK/BCLK/WS; the ES8311 is the slave. */
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    chan_cfg.dma_desc_num = 6;
    chan_cfg.dma_frame_num = 240;
    ESP_RETURN_ON_ERROR(i2s_new_channel(&chan_cfg, NULL, &s_rx), TAG, "i2s_new_channel");

    i2s_std_config_t std_cfg = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(ES3C28P_SAMPLE_RATE),           /* MCLK = 256 x fs = 4.096 MHz */
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {
            .mclk = ES3C28P_I2S_MCLK,
            .bclk = ES3C28P_I2S_BCLK,
            .ws = ES3C28P_I2S_WS,
            .dout = I2S_GPIO_UNUSED,       /* playback (GPIO8) not used in these labs */
            .din = ES3C28P_I2S_DIN,
        },
    };
    return i2s_channel_init_std_mode(s_rx, &std_cfg);
}

static esp_err_t amp_off(void)
{
    gpio_config_t io = { .pin_bit_mask = 1ULL << ES3C28P_AMP_EN, .mode = GPIO_MODE_OUTPUT };
    ESP_RETURN_ON_ERROR(gpio_config(&io), TAG, "amp gpio");
    return gpio_set_level(ES3C28P_AMP_EN, 1);   /* active-low enable: 1 = amplifier off */
}

esp_err_t es3c28p_audio_init(const es3c28p_audio_config_t *cfg)
{
    s_mic_slot = cfg->mic_slot < 0 ? -1 : (cfg->mic_slot ? 1 : 0);
    ESP_RETURN_ON_ERROR(amp_off(), TAG, "amp");
    ESP_RETURN_ON_ERROR(init_i2c(), TAG, "i2c bus");
    ESP_RETURN_ON_ERROR(init_i2s_rx(), TAG, "i2s rx");

    audio_codec_i2s_cfg_t i2s_cfg = { .port = I2S_NUM_0, .rx_handle = s_rx, .tx_handle = NULL };
    const audio_codec_data_if_t *data_if = audio_codec_new_i2s_data(&i2s_cfg);

    /* esp_codec_dev takes the 8-bit (shifted) address: 0x30 == 0x18 << 1. */
    audio_codec_i2c_cfg_t i2c_cfg = {
        .port = I2C_NUM_0,
        .addr = ES8311_CODEC_DEFAULT_ADDR,
        .bus_handle = s_i2c_bus,
        .clock_speed_hz = 100000,
    };
    const audio_codec_ctrl_if_t *ctrl_if = audio_codec_new_i2c_ctrl(&i2c_cfg);
    const audio_codec_gpio_if_t *gpio_if = audio_codec_new_gpio();
    ESP_RETURN_ON_FALSE(data_if && ctrl_if && gpio_if, ESP_FAIL, TAG, "codec interfaces");

    es8311_codec_cfg_t es_cfg = {
        .ctrl_if = ctrl_if,
        .gpio_if = gpio_if,
        .codec_mode = ESP_CODEC_DEV_WORK_MODE_ADC,
        .pa_pin = -1,              /* amplifier handled above; not needed for capture */
        .master_mode = false,      /* codec is I2S slave */
        .use_mclk = true,
    };
    const audio_codec_if_t *codec_if = es8311_codec_new(&es_cfg);
    ESP_RETURN_ON_FALSE(codec_if, ESP_FAIL, TAG, "es8311_codec_new (no ACK at 0x18? check I2C wiring)");

    esp_codec_dev_cfg_t dev_cfg = {
        .dev_type = ESP_CODEC_DEV_TYPE_IN,
        .codec_if = codec_if,
        .data_if = data_if,
    };
    s_mic = esp_codec_dev_new(&dev_cfg);
    ESP_RETURN_ON_FALSE(s_mic, ESP_FAIL, TAG, "esp_codec_dev_new");

    esp_codec_dev_sample_info_t fs = {
        .bits_per_sample = 16,
        .channel = 2,
        .sample_rate = ES3C28P_SAMPLE_RATE,
        .mclk_multiple = 256,
    };
    ESP_RETURN_ON_FALSE(esp_codec_dev_open(s_mic, &fs) == ESP_CODEC_DEV_OK, ESP_FAIL, TAG, "codec open");
    ESP_RETURN_ON_FALSE(esp_codec_dev_set_in_gain(s_mic, cfg->gain_db) == ESP_CODEC_DEV_OK, ESP_FAIL, TAG,
                        "set gain");
    ESP_LOGI(TAG, "ES8311 capture: %d Hz, 16-bit stereo, mic slot %d, gain %.1f dB",
             ES3C28P_SAMPLE_RATE, s_mic_slot, cfg->gain_db);
    return ESP_OK;
}

esp_err_t es3c28p_audio_read_stereo(int16_t *interleaved, size_t n_frames)
{
    int ret = esp_codec_dev_read(s_mic, interleaved, (int)(n_frames * 2 * sizeof(int16_t)));
    return ret == ESP_CODEC_DEV_OK ? ESP_OK : ESP_FAIL;
}

/* Not re-entrant (static chunk buffer): call it from ONE capture task only. */
esp_err_t es3c28p_audio_read_mono(int16_t *mono, size_t n)
{
    static int16_t chunk[CHUNK_FRAMES * 2];
    while (n > 0) {
        size_t frames = n < CHUNK_FRAMES ? n : CHUNK_FRAMES;
        ESP_RETURN_ON_ERROR(es3c28p_audio_read_stereo(chunk, frames), TAG, "read");
        for (size_t i = 0; i < frames; i++) {
            if (s_mic_slot >= 0) {
                mono[i] = chunk[2 * i + s_mic_slot];
            } else {
                /* auto: keep the louder of the two slots, as the workshop prebuilt firmware does */
                const int16_t l = chunk[2 * i], r = chunk[2 * i + 1];
                mono[i] = (abs(l) >= abs(r)) ? l : r;
            }
        }
        mono += frames;
        n -= frames;
    }
    return ESP_OK;
}

i2c_master_bus_handle_t es3c28p_audio_i2c_bus(void)
{
    return s_i2c_bus;
}
