# Hello World on ESP32-S3

An ESP-IDF v6.1 project based on Espressif's `examples/get-started/hello_world`. The application prints `Hello world!`, chip and flash information, and minimum free heap, then counts down and restarts. This cycle repeats; it does not blink an LED.

## 1. Open the development terminal

Install the prerequisites and ESP-IDF using the [setup guide](../install-esp-idf.md). These instructions assume your terminal is already in this project's root directory, for example:

```text
D:\CODE\2027\kmutt-nd69\nd1\docs\week03\lessons\esp32-s3
```

On Windows, from **Git Bash**, run:

```bash
bash ../scripts/start-esp-idf.sh
```

Wait for **ESP-IDF ready**. The launcher keeps this project as the working directory. Enter the remaining commands at the **PowerShell** prompt.

If you are already using Windows PowerShell, run:

```powershell
. ..\scripts\start-esp-idf.ps1
```

On macOS or Linux, from the same project root:

```bash
bash ../scripts/start-esp-idf.sh
```

The Unix launcher opens an activated Bash session in this project directory. It uses `IDF_PATH` if set, otherwise `~/esp/esp-idf`. For another framework location, pass `--idf-path /path/to/esp-idf`. See the [launcher instructions](../scripts/README.md) for Windows custom paths and first-time tool installation.

## 2. Build

For the first build:

```text
idf.py set-target esp32s3
idf.py build
```

Expect `Project build complete`. The generated application is `build/hello_world.bin`. For later edits, run only `idf.py build`. Selecting the target again can reset configuration.

The project targets ESP32-S3. Flash size, PSRAM, and console settings use ESP-IDF defaults; use `idf.py menuconfig` to match your board when necessary. Generated `build/` files and local `sdkconfig` are excluded from Git; `sdkconfig.defaults` records the portable target setting.

## 3. Connect, flash, and monitor

Connect the board with a USB data cable. On Windows, find its COM port in Device Manager and close other serial monitors. Replace `COM5` with the actual port:

```text
idf.py -p COM5 flash monitor
```

Flashing replaces the board's current application. Use the programming connector and boot procedure documented for your board. On macOS/Linux, replace `COM5` with the actual device path; Linux may also require serial-port permissions.

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

## Editor diagnostics (VS Code with clangd)

Open either the repository root or this project root in VS Code. Build the project once so `build/compile_commands.json` and `build/config/sdkconfig.h` exist. Then run **clangd: Restart language server** from the Command Palette if old diagnostics remain.

The project `.clangd` selects the generated compilation database and removes six GCC-only code-generation options from clangd analysis. The real GCC build retains these options. Workspace settings allow clangd to query the ESP32-S3 GCC driver for the target and standard-library include paths, preventing missing-header diagnostics. The matching compiler must already be installed and the compilation database must be generated on the same operating system as the editor.

Both repository and project workspace settings contain the driver-query configuration so either folder can be opened independently. They use compiler-name patterns rather than a specific user's tool path. See [Espressif's editor configuration guidance](https://docs.espressif.com/projects/vscode-esp-idf-extension/en/latest/configureproject.html).

## Verification

On 19 October 2026, `idf.py set-target esp32s3` and `idf.py build` passed using ESP-IDF v6.1 in Windows PowerShell for this project directory. Flashing and serial output have not been verified on hardware.

The configured Windows clangd 21.1.0 checked `main/hello_world_main.c` with zero errors and no warning diagnostics after the editor configuration fix. The Windows ESP-IDF build also passed again.
