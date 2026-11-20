# audio-logger — Board Microphone to PC

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-firmware-2e8b57?style=flat-square)

[Labs index](../../README.md) · [Lesson 02](../../../lessons/02-data-collection.md)

An ESP-IDF v6.1 project for the ES3C28P. It captures the onboard MEMS microphone through the ES8311 codec and sends 1.5 s clips to `labs/python/collect.py` over the native USB Serial/JTAG port.

## Build and flash

```bash
cd nd1/docs/week08/labs/firmware/audio-logger
idf.py set-target esp32s3
idf.py build flash            # -p <port> if needed; do not leave idf.py monitor running
```

The first build downloads `espressif/esp_codec_dev` from the ESP Component Registry (declared in `../components/es3c28p_audio/idf_component.yml`).

## Protocol

| Host sends | Board answers |
|---|---|
| `p` | `PONG KWS-LOGGER v1\n` |
| `i` | `INFO slot0_dbfs=… slot1_dbfs=… mic_slot=0 gain_db=30.0\n` (0.5 s level per I2S slot) |
| `r` | `"KWS1"` · uint32 n_samples (24000) · uint32 sample_rate (16000) · int16 pcm[n] · uint32 checksum |

All binary fields are little-endian; the checksum is the sum of the PCM bytes modulo 2³². Log level is set to WARN in `sdkconfig.defaults` so log text rarely mixes with frames; `collect.py` skips any text before `KWS1` and retries on a checksum error.

## Settings (`main/audio_logger_main.c`)

| Macro | Default | Note |
|---|---|---|
| `MIC_GAIN_DB` | 30.0 | ES8311 PGA gain. Keep it identical to `KWS_MIC_GAIN_DB` in kws-inference |
| `MIC_SLOT` | 0 | I2S slot that carries the mic; check with `python collect.py --port … --info` |

## Hardware used

| Function | Pins (Week 02, Lesson 10) |
|---|---|
| I2C (codec control, shared with touch) | SDA GPIO16, SCL GPIO15, ES8311 at 7-bit 0x18 (`ES8311_CODEC_DEFAULT_ADDR` = 0x30 is the same address shifted left by one bit) |
| I2S | MCLK GPIO4, BCLK GPIO5, WS GPIO7, DIN GPIO6 (DOUT GPIO8 unused) |
| Amplifier FM8002E | enable GPIO1, active-low, held **off** (recording only) |
| USB | native USB Serial/JTAG, GPIO19/20 |

## Status

Written against ESP-IDF v6.1 and esp_codec_dev 1.6.2. The API calls were checked against those sources, and the serial protocol was tested with a simulated board. It has **not** been built with `idf.py` or run on hardware yet. Record your results separately: build passes, then flash, then `--ping`, then `--info` levels.
