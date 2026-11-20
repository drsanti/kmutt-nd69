/*
 * ES3C28P microphone capture: ES8311 codec (ADC) over I2C + I2S.
 *
 * Pin facts from Week 02, Lesson 10 (audio chain) and Lesson 09 (touch):
 *   I2C  SDA GPIO16, SCL GPIO15, ES8311 at 7-bit 0x18 (shared with FT6336G at 0x38)
 *   I2S  MCLK GPIO4, BCLK GPIO5, WS GPIO7, DOUT GPIO8 (to codec), DIN GPIO6 (from codec)
 *   FM8002E amplifier enable GPIO1, active-low (kept OFF here: we only record)
 */
#pragma once

#include <stddef.h>
#include <stdint.h>
#include "esp_err.h"
#include "driver/i2c_master.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ES3C28P_I2C_SDA      16
#define ES3C28P_I2C_SCL      15
#define ES3C28P_I2S_MCLK     4
#define ES3C28P_I2S_BCLK     5
#define ES3C28P_I2S_WS       7
#define ES3C28P_I2S_DOUT     8
#define ES3C28P_I2S_DIN      6
#define ES3C28P_AMP_EN       1      /* active-low */

#define ES3C28P_SAMPLE_RATE  16000

typedef struct {
    float gain_db;   /* ES8311 microphone PGA gain. Use the SAME value for data collection and inference. */
    int mic_slot;    /* 0 = left slot, 1 = right slot of the stereo I2S frame (check with the logger 'i' command) */
} es3c28p_audio_config_t;

/* Create the shared I2C bus, the I2S RX channel and the ES8311 ADC path, then start capture. */
esp_err_t es3c28p_audio_init(const es3c28p_audio_config_t *cfg);

/* Blocking read of n_frames stereo frames (interleaved L,R int16). */
esp_err_t es3c28p_audio_read_stereo(int16_t *interleaved, size_t n_frames);

/* Blocking read of n mono samples taken from cfg->mic_slot. */
esp_err_t es3c28p_audio_read_mono(int16_t *mono, size_t n);

/* The I2C bus created by es3c28p_audio_init(), for other devices on SDA16/SCL15 (e.g. touch). */
i2c_master_bus_handle_t es3c28p_audio_i2c_bus(void);

#ifdef __cplusplus
}
#endif
