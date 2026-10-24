# Hello World on ESP32-S3

```
┌──────────────────┐           ┌──────────────────┐           ┌───────────┐
│ hello_world_main │ ──build─► │ hello_world.bin  │ ──flash─► │ ESP32-S3  │
│ .c               │           │                  │           │ board     │
└──────────────────┘           └──────────────────┘           └─────┬─────┘
                                                                    │
                                                                    ▼
                                                          ┌───────────────────┐
                                                          │ serial monitor:   │
                                                          │ "Hello world!"    │
                                                          └───────────────────┘
```

An ESP-IDF v6.1 project based on Espressif's `examples/get-started/hello_world`. The application prints `Hello world!`, chip and flash information, and minimum free heap, then counts down and restarts. This cycle repeats; it does not blink an LED.

## Before starting from a fresh clone

Use ESP-IDF v6.1 with ESP32-S3 tools installed ([setup guide](../install-esp-idf.md)). The project path may differ after you clone; no source depends on a fixed drive letter.

> [!NOTE]
> **Terminal-only students:** follow sections 1–3 below. Skip [vscode-esp-idf.md](../vscode-esp-idf.md) until you want the VS Code Build button.
> **VS Code Build button:** configure once with [vscode-esp-idf.md](../vscode-esp-idf.md), then return here for flash/monitor.

## 1. Open the development terminal

Open a terminal **in this project root** (folder that contains `CMakeLists.txt` and `main/`). Examples after cloning:

| Platform | Example project path |
|---|---|
| Windows | `D:\CODE\2027\kmutt-nd69\nd1\docs\week03\lessons\esp32-s3` |
| macOS / Linux | `~/kmutt-nd69/nd1/docs/week03/lessons/esp32-s3` |

**Recommended (all platforms)** — from that folder:

```bash
bash ../scripts/start-esp-idf.sh
```

Wait for **ESP-IDF ready**.

| Platform | Where to type `idf.py` after the launcher |
|---|---|
| Windows | The **PowerShell** child prompt (not the parent Git Bash) |
| macOS / Linux | The **Bash** child session the launcher opened |

Custom framework path: `--idf-path` / `-IdfPath` — see [scripts/README.md](../scripts/README.md). Advanced: Windows PowerShell can also run `. ..\scripts\start-esp-idf.ps1` from this folder.

## 2. Build

For the first build:

```text
idf.py set-target esp32s3
idf.py build
```

Expect `Project build complete`. The generated application is `build/hello_world.bin`. For later edits, run only `idf.py build`. Selecting the target again can reset configuration.

The project targets ESP32-S3. Flash size, PSRAM, and console settings use ESP-IDF defaults; use `idf.py menuconfig` to match your board when necessary. Generated `build/` files and local `sdkconfig` are excluded from Git; `sdkconfig.defaults` records the portable target setting.

## 3. Connect, flash, and monitor

Connect the board with a USB data cable. Close other serial monitors. Find the port, then flash (replace the port with yours).

| Platform | Find the port | Flash and monitor |
|---|---|---|
| Windows | Device Manager → Ports (COM & LPT) | `idf.py -p COM5 flash monitor` |
| macOS | `ls /dev/cu.*` | `idf.py -p /dev/cu.usbserial-XXXX flash monitor` |
| Linux | `ls /dev/ttyUSB* /dev/ttyACM*` | `idf.py -p /dev/ttyUSB0 flash monitor` |

On Linux you may need membership in `dialout` or `uucp`. On **WSL2**, USB serial often needs passthrough (for example `usbipd` on Windows) or flash from native Windows instead.

Flashing replaces the board's current application. Use the programming connector and boot procedure from your board manual.

Look for output similar to:

```text
Hello world!
This is esp32s3 chip with 2 CPU core(s), ...
Minimum free heap size: ... bytes
Restarting in 10 seconds...
```

Values depend on the board and configuration. Press **Ctrl+]** to exit the monitor. If output is absent, check the selected console interface and USB connector, then reset the board.

## Files

| File | Purpose |
| --- | --- |
| `CMakeLists.txt` | Defines the `hello_world` ESP-IDF project and minimal component build. |
| `main/CMakeLists.txt` | Registers the application source and its dependencies. |
| `main/hello_world_main.c` | Contains `app_main()` and the demonstration output. |
| `sdkconfig.defaults` | Selects ESP32-S3 for a new configuration. |

The application source retains Espressif's CC0-1.0 license header.

## Build with the VS Code ESP-IDF extension

Follow the [step-by-step extension guide](../vscode-esp-idf.md). Open this project folder in VS Code, configure the installation once, run **Developer: Reload Window**, then check **ESP-IDF: Doctor Command** and use **ESP-IDF: Build your project**.

The saved Windows environment is specific to this computer. Other users must select their EIM installation or export their own script-based installation. Activating PowerShell alone does not configure extension builds.

## Clean the project

From the project root in the activated terminal:

```text
idf.py clean
```

This cleans compiled outputs while keeping CMake configuration. For a complete build-directory cleanup:

```text
idf.py fullclean
idf.py build
```

`fullclean` removes generated build contents and preserves source files and `sdkconfig`. To delete the entire `build` folder explicitly, use the command for your current shell instead of `fullclean`:

```powershell
# Windows PowerShell
Remove-Item -Recurse -Force .\build
```

```bash
# macOS/Linux Bash, or Windows Git Bash
rm -rf -- ./build
```

Confirm you are in the project root and wait for any running build to finish before deleting its files. The next build regenerates the directory. Until then, clangd may report missing generated headers or a missing compilation database. Rebuild, then restart the language server. Use the extension's **ESP-IDF: Full Clean Project** command for the equivalent IDE operation when a configured build directory exists.

## Editor diagnostics (VS Code with clangd)

Open either the repository root or this project root in VS Code. Build the project once so `build/compile_commands.json` and `build/config/sdkconfig.h` exist. Then run **clangd: Restart language server** from the Command Palette if old diagnostics remain.

The project `.clangd` selects the generated compilation database and removes six GCC-only code-generation options from clangd analysis. The real GCC build retains these options. Workspace settings allow clangd to query the ESP32-S3 GCC driver for the target and standard-library include paths, preventing missing-header diagnostics. The matching compiler must already be installed and the compilation database must be generated on the same operating system as the editor.

Both repository and project workspace settings contain the driver-query configuration for source analysis. Open the firmware project root when using the ESP-IDF extension to build. They use compiler-name patterns rather than a specific user's tool path. See [Espressif's editor configuration guidance](https://docs.espressif.com/projects/vscode-esp-idf-extension/en/latest/configureproject.html).

### Why `FreeRTOS.h` has an IWYU comment

**IWYU** means **Include What You Use**. clangd normally flags headers that do not directly provide symbols used in the source file. Here, FreeRTOS `task.h` explicitly requires `FreeRTOS.h` to be included first, so the source records that dependency:

```c
// task.h requires FreeRTOS.h to be included first.
#include "freertos/FreeRTOS.h" // IWYU pragma: keep
#include "freertos/task.h"
```

The comment tells include-analysis tools to retain this required header. It does not change compiled behavior. See [clangd's include-cleaner guidance](https://clangd.llvm.org/guides/include-cleaner).

## Verification

On 19 October 2026, `idf.py set-target esp32s3` and `idf.py build` passed using ESP-IDF v6.1 in Windows PowerShell for this project directory. Flashing and serial output have not been verified on hardware.

The configured Windows clangd 21.1.0 checked `main/hello_world_main.c` with zero errors and no warning diagnostics after the editor configuration fix. The Windows ESP-IDF build also passed again.
