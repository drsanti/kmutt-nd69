# ND01 — Week 02: ES3C28P Hardware & Embedded Fundamentals

> บอร์ด ES3C28P (ESP32-S3R8) ตั้งแต่ชิปถึง firmware — 15 บท
> เรียงจาก silicon → peripherals → toolchain → embedded C

## 📚 Lessons

### สถาปัตยกรรมชิป

| # | Lesson |
|---|---|
| 01 | [ชิป ESP32-S3 บน board ES3C28P](lessons/01-esp32s3r8-the-chip.md) |
| 02 | [ประวัติ ESP32 — จาก ESP8266 ถึง ESP32-S3](lessons/02-esp32-history.md) |
| 03 | [Memory หลายชนิดบน ESP32-S3 — RAM, SRAM, PSRAM, Flash, ROM, eFuse](lessons/03-memory-types.md) |
| 04 | [Memory ในมุม Firmware — heap, stack, partition, NVS](lessons/04-memory-firmware-view.md) |
| 05 | [ESP-IDF — Toolchain ตัวจริงของ ESP32](lessons/05-esp-idf-toolchain.md) |

### อุปกรณ์บน board

| # | Lesson |
|---|---|
| 06 | [USB/Serial บน board นี้ — ไม่มีชิป USB-UART และกับดักที่ตามมา](lessons/06-usb-serial-caveat.md) |
| 07 | [ระบบไฟและแบตเตอรี่ — TP4054, LDO, และการวัดแบตผ่าน ADC](lessons/07-power-battery.md) |
| 08 | [จอ ILI9341V — SPI display 240×320 บน board ES3C28P](lessons/08-ili9341-display.md) |
| 09 | [Touch screen FT6336G — capacitive touch ผ่าน I2C](lessons/09-ft6336-touch.md) |
| 10 | [ระบบเสียง — ES8311 codec + FM8002E amp + MEMS mic](lessons/10-audio-chain.md) |
| 11 | [RGB LED WS2812 — เส้นเดียวต้อง timing เป๊ะ และทำไมต้อง RMT](lessons/11-ws2812-rmt-led.md) |
| 12 | [MicroSD บน ES3C28P — SDIO 4-bit เต็มสปีด](lessons/12-microsd-sdio.md) |
| 13 | [Expansion header และแผนที่ขาทั้ง board — ขาไหนว่าง ขาไหนห้าม](lessons/13-expansion-pins.md) |

### พร้อมเขียน firmware

| # | Lesson |
|---|---|
| 14 | [ติดตั้ง ESP-IDF ผ่าน VS Code — พร้อมทดสอบบน board จริง](lessons/14-esp-idf-setup.md) |
| 15 | [Embedded C + FreeRTOS review — ฐานที่ต้องมีก่อนเขียน firmware จริง](lessons/15-embedded-c-freertos-review.md) |

---

> [!NOTE]
> ภาพประกอบ 16:9 ของแต่ละบทอยู่ใน [`lessons/images/`](lessons/images/)
> ชื่อไฟล์ตรงกับเลขบท

<sub>[← กลับหน้าหลัก](../../../README.md)</sub>
