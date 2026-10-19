# Week 02 — Hardware and Embedded Fundamentals: English Edition

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-02-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-lessons-2e8b57?style=flat-square)

These 15 lessons expand and refine the original course materials for the ES3C28P board, using professional technical English. They progress from processor architecture and memory to onboard peripherals, development tools, and concurrent firmware design.

## Reading guide

Lessons 01–05 establish the processor, memory, and framework model. Lessons 06–13 cover board interfaces and resource constraints. Lessons 14–15 establish the development workflow and programming fundamentals. For a first hardware session, use Lesson 14 to establish a working environment, then return to the numbered sequence.

Each lesson includes learning objectives, engineering explanations, and practical verification or review exercises. Code fragments illustrate the stated concept and are not complete firmware projects unless explicitly identified as such.

## Table of contents

- [Presentation](web/README.md)
- [Open the deck](web/index.html)
- [Illustrations](images/README.md)
- [Thai lessons](../README.md)
- [Week 02 index](../../README.md)

## Lessons

| Number | Topic |
|---|---|
| 01 | [The ESP32-S3R8 on the ES3C28P Board](01-esp32s3r8-the-chip.md) |
| 02 | [ESP32 Evolution and Platform Selection](02-esp32-history.md) |
| 03 | [Memory Technologies: SRAM, PSRAM, Flash, ROM, and eFuse](03-memory-types.md) |
| 04 | [Firmware Memory: Sections, Stacks, Heaps, Partitions, and NVS](04-memory-firmware-view.md) |
| 05 | [ESP-IDF and the Embedded Development Toolchain](05-esp-idf-toolchain.md) |
| 06 | [Native USB, Serial Communication, and Recovery](06-usb-serial-caveat.md) |
| 07 | [Power Supply, Battery Charging, and Voltage Measurement](07-power-battery.md) |
| 08 | [ILI9341 Display Control over SPI](08-ili9341-display.md) |
| 09 | [FT6336G Capacitive Touch and Input Events](09-ft6336-touch.md) |
| 10 | [Audio: ES8311 Codec, Amplifier, and Microphone](10-audio-chain.md) |
| 11 | [WS2812 RGB LED Control with RMT](11-ws2812-rmt-led.md) |
| 12 | [microSD Storage over the SDMMC Host](12-microsd-sdio.md) |
| 13 | [Expansion Interfaces and GPIO Resource Planning](13-expansion-pins.md) |
| 14 | [Installing ESP-IDF and Verifying the Board](14-esp-idf-setup.md) |
| 15 | [Embedded C and FreeRTOS Engineering Fundamentals](15-embedded-c-freertos-review.md) |

## Technical scope and evidence

Board-specific GPIO assignments, component identities, signal polarity, and historical firmware observations are inherited from the corresponding original lessons. No schematic, board-revision record, or hardware test accompanies this English conversion. Check the actual board documentation before adapting the wiring to another revision.

General ESP32-S3 and ESP-IDF behavior has been refined using the official references linked in the lessons. Versioned ESP-IDF links explain the referenced behavior; they do not prescribe a single supported release for the course project. Install the release required by that project's dependencies. Live installation documentation may change its interface labels.

Historical heap measurements and reported fixes are identified as observations from the source notes. They are not new measurements performed for this edition. Likewise, exercises and acceptance criteria describe checks to perform, not completed hardware validation.

Technical refinements include native USB versus bridge reset behavior; capability allocation versus size-based preference; conditional PSRAM/DMA support; SDMMC GPIO routing versus fixed PCB wiring; RGB565 channel widths and byte order; GPIO3 boot strapping; and synchronization beyond `volatile`.

The illustrations for this edition are in [`images/`](images/README.md). Embedded Thai labels and any source-image inaccuracies have not been edited. Refer to the English prose for the revised technical explanation.

[Original Week 02 index](../../README.md)
