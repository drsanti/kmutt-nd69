# Week 03 lessons

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-03-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-lessons-2e8b57?style=flat-square)

## Table of contents

- [Week 03 index](../README.md)
- [Week 02 lessons](../../week02/lessons/README.md)
- [Install and Verify ESP-IDF on Windows](install-esp-idf.md)
- [ESP-IDF terminal launchers for Windows, macOS, and Linux](scripts/README.md)
- [Build with the VS Code ESP-IDF extension](vscode-esp-idf.md)
- [Hello World on ESP32-S3](esp32-s3/README.md)

## Paths used in these lessons

The **repository root** contains `nd1/`, `nd2/`, and `nd3/`. The **firmware project root** is `nd1/docs/week03/lessons/esp32-s3`, containing `CMakeLists.txt` and `main/`. The **framework directory** is a separate ESP-IDF installation, for example `D:\dev\esp\v6.1\esp-idf`.

After cloning the repository, open a terminal in the firmware project root before following build, launcher, or cleanup commands. Replace example drive letters, user directories, framework locations, and serial ports with your own.

## Suggested workflow

1. Install Git Bash, Python, ESP-IDF, and the ESP32-S3 tools using the setup lesson.
2. Open the `esp32-s3` project directory. Project commands assume you are already in that directory.
3. Choose the terminal launcher or configure the VS Code ESP-IDF extension once.
4. Build Hello World, then flash and monitor when hardware is available.
5. Use the project guide for cleanup and editor-diagnostic troubleshooting.

The recorded Windows command-line builds and clangd checks passed. The extension UI and hardware output remain separate verification steps; native macOS/Linux toolchain activation has not been validated here.

## Using these files from GitHub

The source project, default target settings, launchers, and clangd configuration are reusable. The current `.vscode/settings.json` files contain Windows tool locations from the verified setup. Regenerate the extension environment for your computer using the [VS Code guide](vscode-esp-idf.md); do not assume a contributor's user-directory paths exist on your machine.

Generated `build/`, `sdkconfig`, `sdkconfig.old`, and editor caches are local artifacts, not lesson source. Preserve `sdkconfig.defaults` when cleaning or sharing a project. After cloning, build once to generate the configuration headers and compilation database used by the editor.

The [FreeRTOS folder](free-rtos/README.md) is reserved for a later exercise; it does not yet contain a standalone lab.
