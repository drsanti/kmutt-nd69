# ND01 — Week 03: ESP-IDF Setup (Windows, macOS, Linux) and ESP32-S3 Hello World

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-03-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-index-2e8b57?style=flat-square)

Install Git, Python, and ESP-IDF on Windows, macOS, or Linux, then build the included ESP32-S3 Hello World project using a terminal or the VS Code ESP-IDF extension. The Windows path is verified in detail; macOS and Linux follow the same course steps with Espressif’s OS guides linked for prerequisites.

**Windows:** use **PowerShell** for all ESP-IDF commands (`idf.py`, `export.ps1`, build, flash). Do **not** use Git Bash — MSYS/MinGW breaks Espressif’s toolchain.

## Table of contents

- [Lessons](lessons/README.md)
- [Week 02](../week02/README.md)
- [Week 01](../week01/README.md)
- [Documents](../README.md)
- [Track index](../../README.md)

## Learning outcomes

- Distinguish the ESP-IDF framework, compiler toolchain, Python environment, and firmware project.
- Open an activated development terminal from the firmware project root.
- Configure the VS Code extension independently of terminal activation.
- Build, clean, and inspect the Hello World project.
- Flash and monitor a board, recording hardware results separately from build results.

Start with the [lesson sequence](lessons/README.md): install until `idf.py --version` works, then use the [project README](lessons/esp32-s3/README.md) for launcher, build, and flash.
