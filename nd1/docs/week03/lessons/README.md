# Week 03 lessons

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-03-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-lessons-2e8b57?style=flat-square)

## Table of contents

- [Week 03 index](../README.md)
- [Week 02 lessons](../../week02/lessons/README.md)
- [Install and Verify ESP-IDF (Windows, macOS, Linux)](install-esp-idf.md)
- [Hello World on ESP32-S3](esp32-s3/README.md)
- [ESP-IDF terminal launchers (reference)](scripts/README.md)
- [Build with the VS Code ESP-IDF extension (optional)](vscode-esp-idf.md)

## Read in this order

1. This page — paths and which track to pick  
2. [install-esp-idf.md](install-esp-idf.md) — until `idf.py --version` works  
3. [esp32-s3/README.md](esp32-s3/README.md) — launcher, build, flash (main lab)  
4. Only if needed: [scripts/README.md](scripts/README.md) (custom paths) or [vscode-esp-idf.md](vscode-esp-idf.md) (Build button)

Pick **one** daily method: **terminal** (default for this course) **or** **VS Code Build button**. Do not mix them until both work separately.

## Paths used in these lessons

| Name | What it is |
|---|---|
| Repository root | Folder containing `nd1/`, `nd2/`, and `nd3/` |
| Firmware project root | `nd1/docs/week03/lessons/esp32-s3` — has `CMakeLists.txt` and `main/` |
| Framework (`IDF_PATH`) | Separate ESP-IDF install on your machine — has `export.ps1` / `export.sh` and `tools/idf.py` |

> [!NOTE]
> Example paths (launcher defaults when `IDF_PATH` is unset). Use **your** paths.
>
> | Platform | Parent directory | Actual framework (`IDF_PATH`) |
> |---|---|---|
> | Windows | `D:\dev\esp` | `D:\dev\esp\v6.1\esp-idf` |
> | macOS | `~/esp` | `~/esp/esp-idf` |
> | Linux | `~/esp` | `~/esp/esp-idf` |
>
> Activate the **framework** directory, not the parent. Pass `-IdfPath` (Windows) or `--idf-path` (macOS/Linux) if your install is elsewhere.

## Choose one install track

| Track | Who it is for | Follow | Skip |
|---|---|---|---|
| **A — Course scripts (recommended)** | Students who want copy-paste steps matching this repo’s launchers | [install-esp-idf.md](install-esp-idf.md) Windows W1–W6 or macOS/Linux U1–U4 (script path) | EIM “Easy Install” blocks |
| **B — EIM** | Students who prefer Espressif Installation Manager | Official OS guide + EIM **Open IDF Terminal**, then continue at [esp32-s3/README.md](esp32-s3/README.md) | Manual `git clone` / `install.ps1` / `install.sh` steps |

## Suggested workflow

| Order | What to do | Where |
|---|---|---|
| 1 | Install prerequisites + ESP-IDF v6.1 + ESP32-S3 tools for your OS (skip if `idf.py --version` already works) | [install-esp-idf.md](install-esp-idf.md) |
| 2 | Open a terminal in `esp32-s3`, activate with the launcher, build, then flash when you have a board | [esp32-s3/README.md](esp32-s3/README.md) |
| — | Custom framework path, `-InstallTools`, `.cmd` / `.ps1` | [scripts/README.md](scripts/README.md) (reference) |
| — | VS Code Build button instead of terminal `idf.py` | [vscode-esp-idf.md](vscode-esp-idf.md) (optional) |

Step 2 is the main student lab. The FreeRTOS PC lab is separate: [free-rtos/README.md](free-rtos/README.md).

Windows command-line builds and clangd checks were recorded on the course machine. Extension UI and hardware flash remain separate checks. Native macOS/Linux toolchain activation follows the same steps but was not re-verified on every host.

## Using these files from GitHub

Checked-in `.vscode/settings.json` may contain another computer’s tool paths. Regenerate them with [vscode-esp-idf.md](vscode-esp-idf.md) on your machine.

Generated `build/`, `sdkconfig`, `sdkconfig.old`, and editor caches are local. Keep `sdkconfig.defaults`. After cloning, build once so the editor can see generated headers.
