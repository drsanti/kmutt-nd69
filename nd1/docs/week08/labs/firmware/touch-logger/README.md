# touch-logger — FT6336G Strokes to PC

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-firmware-2e8b57?style=flat-square)

[Labs index](../../README.md) · [Lesson 07](../../../lessons/07-touch-gesture-alternative.md)

Polls the FT6336G touch controller every 10 ms and prints `D x y t`, `M x y t`, `U t`, or `E err` lines for `labs/python/collect_touch.py`.

```bash
cd nd1/docs/week08/labs/firmware/touch-logger
idf.py set-target esp32s3
idf.py build flash
```

| Function | Pins (Week 02, Lesson 09) |
|---|---|
| I2C | SDA GPIO16, SCL GPIO15, FT6336G at 0x38 (bus shared with ES8311 at 0x18) |
| Reset | GPIO18, active low (10 ms pulse, then 300 ms boot wait) |
| Interrupt | GPIO17 (not used: this logger polls) |

Uses only ESP-IDF drivers (`i2c_master`, `gpio`, `esp_timer`), no extra components. If `i2c_master_probe` fails at boot, check the reset sequence and pull-ups (see [troubleshooting](../../../troubleshooting.md)).

## Status

API names were checked against the ESP-IDF v6.1 headers, and the stroke parser in `collect_touch.py` was tested with simulated lines. The project has **not** been built with `idf.py` or run on hardware yet.
