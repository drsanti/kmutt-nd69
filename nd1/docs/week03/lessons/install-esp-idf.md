# Install and Verify ESP-IDF

Follow these steps for **Windows**, **macOS**, or **Linux**. Install ESP-IDF v6.1 with ESP32-S3 tools, then build (and optionally flash) on an ESP32-S3 board. Complete each verification before continuing.

You need internet access, disk space for the framework and tools, and an ESP32-S3 board with a USB data cable for the final hardware steps. Software installation and building can be completed without a board.

## Which section to follow

| Platform | Install and activate (this file) | Then go to |
|---|---|---|
| Windows | [Windows setup](#windows-setup) | [esp32-s3/README.md](esp32-s3/README.md) |
| macOS | [macOS and Linux setup](#macos-and-linux-setup) | [esp32-s3/README.md](esp32-s3/README.md) |
| Linux (including WSL) | [macOS and Linux setup](#macos-and-linux-setup) | [esp32-s3/README.md](esp32-s3/README.md) |

**Stop this guide** when `idf.py --version` reports ESP-IDF v6.1 in an activated terminal. Build, flash, and daily launcher steps live in the project README — do not search for a second full lab inside this file.

WSL is a **Linux** environment. Install a Linux ESP-IDF toolchain inside WSL; do not reuse a Windows compiler from WSL Bash. Flashing a USB board from WSL2 often needs extra USB passthrough (`usbipd` on Windows, or flash from native Windows/macOS/Linux instead).

For optional VS Code Build-button setup, see [vscode-esp-idf.md](vscode-esp-idf.md) after install. Launcher flags and custom paths: [scripts/README.md](scripts/README.md).

## Example paths (all platforms)

Activate the **framework** directory — the folder that contains `export.ps1` / `export.sh` and `tools/idf.py`. Do not stop at the parent directory.

> [!NOTE]
> Examples used in these lessons and launchers (when `IDF_PATH` is unset). Use the paths on **your** computer.
>
> | Platform | Parent directory | Actual framework (`IDF_PATH`) | Tools (typical default) |
> |---|---|---|---|
> | Windows | `D:\dev\esp` | `D:\dev\esp\v6.1\esp-idf` | `%USERPROFILE%\.espressif` |
> | macOS | `~/esp` | `~/esp/esp-idf` | `~/.espressif` |
> | Linux | `~/esp` | `~/esp/esp-idf` | `~/.espressif` |
>
> On Windows, PowerShell `D:\dev\esp\v6.1\esp-idf` is Git Bash `/d/dev/esp/v6.1/esp-idf` (same folder, different spelling). Avoid spaces in framework and project paths.

---

## Windows setup

> [!IMPORTANT]
> Pick **one** Windows track and stay on it.
>
> | Track | Steps | Skip |
> |---|---|---|
> | **A — Course scripts (recommended)** | W1 → W6 below (`git clone`, `install.ps1`, `export.ps1`) | W5 EIM alternative |
> | **B — EIM only** | Official Windows guide + EIM **Open IDF Terminal**, then [esp32-s3/README.md](esp32-s3/README.md) | W4–W6 script commands |
>
> W2 PowerShell is for **install and first activation only**. Daily lab work uses the launcher from the `esp32-s3` folder (see the project README).

### W1. Install Git for Windows, including Git Bash

1. Download Git for Windows from the official [Windows download page](https://git-scm.com/install/windows).
2. Run the installer. Include Git Bash and select **Git from the command line and also from 3rd-party software** when choosing the `PATH` option.
3. Complete installation and close any terminals that were already open.
4. Open **Git Bash** from Start and run:

   ```bash
   git --version
   bash --version
   ```

Both commands must print version information. If already installed, perform these checks and continue.

### W2. Open PowerShell from Git Bash

In **Git Bash**, run:

```bash
env -u MSYSTEM powershell.exe -NoLogo -NoExit
```

Wait for a prompt beginning with `PS`. **All subsequent Windows setup commands use PowerShell**, unless explicitly labeled otherwise. Keep this session open throughout setup.

Git Bash uses MSYS/MinGW, which the installed ESP-IDF tool manager rejects. The command above opens Windows PowerShell and removes the inherited `MSYSTEM` marker from that child process. Do not run `install.sh` or source `export.sh` in Git Bash for this Windows setup.

### W3. Verify Python and Git in PowerShell

Run:

```powershell
Remove-Item Env:MSYSTEM -ErrorAction SilentlyContinue
python --version
git --version
```

The first command clears any remaining MSYS marker in the Windows PowerShell session; it prints nothing. Expect Python 3.10 or newer and a Git version from the next two commands. Python 3.11.9 was used for the command verification on this computer. Supported versions are listed in [Espressif's prerequisites](https://docs.espressif.com/projects/idf-im-ui/en/latest/prerequisites.html).

#### If Python or Git is not recognized

First refresh the current session from the saved Windows environment:

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
$env:PATHEXT = [Environment]::GetEnvironmentVariable('PATHEXT', 'Machine')
python --version
git --version
```

This changes only the current session. It does not install software or modify saved Windows settings.

If `python` is still unavailable, try:

```powershell
py --version
```

If that reports a supported version, expose that interpreter in this session:

```powershell
$pythonExe = py -c "import sys; print(sys.executable)"
$env:Path = (Split-Path -Parent $pythonExe) + ';' + $env:Path
python --version
```

If neither command works, install a supported Python release from [python.org](https://www.python.org/downloads/windows/). In the traditional installer, enable **Add python.exe to PATH**. An existing installation can be modified to enable this option; see [Python's Windows instructions](https://docs.python.org/3.11/using/windows.html#finding-the-python-executable). Alternatively, EIM can install missing prerequisites as described below.

After installing Python or Git, close PowerShell and its parent Git Bash, reopen Git Bash, repeat Step W2, and verify both version commands. If Python opens Microsoft Store, check Windows **App execution aliases** and ensure `PATH` selects the installed interpreter.

**Continue only when both `python --version` and `git --version` succeed.**

### W4. Prepare the ESP-IDF v6.1 source

| Purpose | Example path | Notes |
| --- | --- | --- |
| Parent directory | `D:\dev\esp` | Holds version folders such as `v6.1`. Not `IDF_PATH`. |
| Framework (`IDF_PATH`) | `D:\dev\esp\v6.1\esp-idf` | Actual ESP-IDF source. Contains `export.ps1` and `tools/idf.py`. |
| Practice projects | `D:\dev\projects` | Outside the framework tree. |

All clone, activate, and build commands use the **framework** path, not the parent directory.

#### If the framework is already downloaded

```powershell
Set-Location D:\dev\esp\v6.1\esp-idf
Test-Path .\tools\idf.py
Test-Path .\install.ps1
Test-Path .\examples\get-started\hello_world\CMakeLists.txt
```

All three checks must print `True`. For a Git checkout, verify the version and submodules:

```powershell
git describe --tags --always
git submodule update --init --recursive
```

Expect `v6.1` for the course checkout. If you extracted an archive without Git metadata, skip the Git commands; use a complete official package containing submodules. An automatically generated GitHub ZIP may omit them.

#### If the framework directory does not exist

```powershell
New-Item -ItemType Directory -Force D:\dev\esp\v6.1 | Out-Null
git clone --branch v6.1 --recursive https://github.com/espressif/esp-idf.git D:\dev\esp\v6.1\esp-idf
Set-Location D:\dev\esp\v6.1\esp-idf
git describe --tags --always
```

Expect `v6.1`. Do not clone over an existing source directory.

#### Framework and compiler are stored separately

The framework directory contains source, examples, and build scripts. The default tools directory on Windows is `%USERPROFILE%\.espressif`, unless `IDF_TOOLS_PATH` selects another location. The compiler is installed below that tools directory; it is not inside the framework checkout.

After activation, inspect your actual locations:

```powershell
$env:IDF_PATH
$env:IDF_TOOLS_PATH
(Get-Command xtensa-esp32s3-elf-gcc).Source
(Get-Command cmake).Source
```

### W5. Install the ESP32-S3 tools

Downloading source files does not install the compiler or ESP-IDF Python environment. In the same PowerShell session, run:

```powershell
Set-Location D:\dev\esp\v6.1\esp-idf
.\install.ps1 esp32s3
```

Wait for the script to finish successfully and print `All done!`. The initial tool downloads can exceed 1 GB. Keep the terminal open while downloads run. Do not move tool folders after installation.

If PowerShell blocks a trusted installation script, run this session-scoped command and retry:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

If institutional policy prevents this change, contact your IT administrator. If installation reports a download or Python dependency error, resolve it before activation.

#### Alternative: Espressif Installation Manager (EIM) on Windows

EIM is Espressif's recommended installer for v6.1:

1. Follow the official [Windows installation guide](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/windows-setup.html).
2. Install prerequisites when prompted. Select v6.1 through the custom installation options; Easy Installation may select a different release.
3. Select ESP32-S3 support when offered and wait for completion.
4. Open **Manage Installations → Open Dashboard**, select the installed environment, and choose **Open IDF Terminal**.
5. Continue with the verification commands in Step W6. Use the framework path configured by EIM, which may differ from this guide.

### W6. Activate and verify ESP-IDF

For the script-based installation, run in the same PowerShell session:

```powershell
$env:PYTHONUTF8 = '1'
Set-Location D:\dev\esp\v6.1\esp-idf
. .\export.ps1
```

`PYTHONUTF8` enables Python UTF-8 mode for this session. The first dot followed by a space loads the activation script into the current session. For EIM, use its activated IDF terminal instead.

Then verify:

```powershell
idf.py --version
$env:IDF_PATH
Get-Command idf.py
python --version
cmake --version
ninja --version
```

Expect the intended ESP-IDF v6.1 release, the correct framework directory, and version output for all tools. Python should now belong to the ESP-IDF environment. Do not continue if any command fails.

Activation affects this terminal only. Keep PowerShell open for verification; type `exit` when finished.

**Windows Track A complete.** Next: [esp32-s3/README.md](esp32-s3/README.md) (open a terminal in that folder, run the launcher, then build).

---

## macOS and Linux setup

Use Bash (or the course launcher, which opens Bash). Do not mix a Windows ESP-IDF install with WSL Bash.

> [!IMPORTANT]
> Pick **one** Unix track and stay on it.
>
> | Track | Steps | Skip |
> |---|---|---|
> | **A — Course scripts (recommended)** | U1 → U4 (`git clone`, `install.sh`, `export.sh`) | U3 EIM alternative |
> | **B — EIM** | Official macOS/Linux guide + managed IDF terminal, then [esp32-s3/README.md](esp32-s3/README.md) | U2–U4 script commands |

### U1. Install prerequisites

**Ordered spine (Track A):** install OS packages from Espressif → verify Git/Python → clone framework (U2) → `./install.sh esp32s3` (U3) → `. ./export.sh` (U4) → open [esp32-s3/README.md](esp32-s3/README.md).

Prerequisites by OS (packages and system tools):

- [macOS setup (ESP-IDF v6.1)](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/macos-setup.html)
- [Linux setup (ESP-IDF v6.1)](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/linux-setup.html)
- Script-based clone details (matches this course’s launcher default): [Linux and macOS legacy setup](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/linux-macos-setup-legacy.html)

Then verify:

```bash
git --version
python3 --version
```

Expect a recent Git and Python 3.10 or newer (see Espressif’s prerequisites for supported versions).

### U2. Prepare the ESP-IDF v6.1 source

| Purpose | Example path | Notes |
| --- | --- | --- |
| Parent directory | `~/esp` | Holds the clone. Not `IDF_PATH` by itself when the clone is nested. |
| Framework (`IDF_PATH`) | `~/esp/esp-idf` | Actual ESP-IDF source. Contains `export.sh` and `tools/idf.py`. |
| Practice projects | `~/esp/projects` (example) | Outside the framework tree, or use the course `esp32-s3` folder. |

#### If the framework is already downloaded

```bash
cd ~/esp/esp-idf
test -f ./tools/idf.py && echo ok
test -f ./install.sh && echo ok
test -f ./examples/get-started/hello_world/CMakeLists.txt && echo ok
git describe --tags --always
git submodule update --init --recursive
```

Expect `v6.1` for the course checkout.

#### If the framework directory does not exist

```bash
mkdir -p ~/esp
cd ~/esp
git clone --branch v6.1 --recursive https://github.com/espressif/esp-idf.git
cd ~/esp/esp-idf
git describe --tags --always
```

Expect `v6.1`. Do not clone over an existing source directory.

#### Framework and compiler are stored separately

Tools normally land under `~/.espressif` unless `IDF_TOOLS_PATH` selects another location. After activation:

```bash
echo "$IDF_PATH"
echo "$IDF_TOOLS_PATH"
command -v xtensa-esp32s3-elf-gcc
command -v cmake
```

### U3. Install the ESP32-S3 tools

```bash
cd ~/esp/esp-idf
./install.sh esp32s3
```

Wait until the installer finishes successfully. Downloads can exceed 1 GB. Do not move tool folders after installation.

#### Alternative: Espressif Installation Manager (EIM) on macOS/Linux

For v6.1, Espressif also documents EIM as the recommended installer on macOS (and supports managed installs on Linux). Follow the official OS page linked in Step U1, select **v6.1** and ESP32-S3 support, then open the IDF terminal or activate the installed environment. Use that framework path for later steps; it may differ from `~/esp/esp-idf`.

### U4. Activate and verify ESP-IDF

```bash
cd ~/esp/esp-idf
. ./export.sh
```

The leading `.` and space matter. Then verify:

```bash
idf.py --version
echo "$IDF_PATH"
command -v idf.py
python --version
cmake --version
ninja --version
```

Expect ESP-IDF v6.1, the correct framework directory, and version output for all tools. Activation affects this shell only.

**macOS / Linux Track A complete.** Next: [esp32-s3/README.md](esp32-s3/README.md) (open a terminal in that folder, run the launcher, then build).

---

## Next lab (all platforms)

When `idf.py --version` works, leave this install guide and follow:

**[Hello World on ESP32-S3](esp32-s3/README.md)** — activate with `bash ../scripts/start-esp-idf.sh`, then `set-target`, `build`, flash, and monitor.

Optional scratch copy of Espressif’s example (not required for the course project):

**Windows (PowerShell, activated):**

```powershell
New-Item -ItemType Directory -Force D:\dev\projects | Out-Null
Copy-Item -Recurse "$env:IDF_PATH\examples\get-started\hello_world" D:\dev\projects\hello_world
```

**macOS / Linux (Bash, activated):**

```bash
mkdir -p ~/esp/projects
cp -r "$IDF_PATH/examples/get-started/hello_world" ~/esp/projects/hello_world
```

---

## Troubleshooting

| Symptom | What to check or do |
| --- | --- |
| `MSys/Mingw is not supported` | Windows: you are in Git Bash/MSYS or a child shell inheriting `MSYSTEM`. Follow Step W2, or open the EIM IDF terminal. |
| `python` / `python3` is not recognized | Complete the prerequisite check for your OS (W3 or U1). |
| Extension reports `cmake was not found` | Configure the extension using the [VS Code guide](vscode-esp-idf.md); terminal activation alone does not configure the extension host. |
| `idf.py` is not recognized | Activate this terminal (launcher, `export.ps1` / `export.sh`, or EIM IDF terminal). |
| Wrong ESP-IDF version | Close the terminal and activate the intended installation. Check `IDF_PATH` and `idf.py --version`. |
| Python environment or compiler is missing | Finish tool install: `install.ps1 esp32s3` (Windows) or `./install.sh esp32s3` (macOS/Linux), then activate. |
| Script execution is disabled (Windows) | Use the session-scoped policy command in Step W5. |
| Missing submodule files | Run `git submodule update --init --recursive` in the framework directory. |
| `CMakeLists.txt` cannot be found | Run commands from the firmware project root (`esp32-s3`). |
| Serial port absent or access denied | Check cable, connector, drivers; on Linux check group permissions; close other programs using the port. |
| Flashing stays at `Connecting...` | Verify port and chip target; follow the board’s download-mode procedure. |
| Serial output unreadable or absent | Check port and console settings; press RESET/EN; example normally uses 115200 baud. |
| Build errors after moving a project or changing ESP-IDF versions | Reactivate the intended environment and run `idf.py fullclean`, then rebuild. |

## Completion checklist

- [ ] Git and Python work in the shell you will use for ESP-IDF.
- [ ] `idf.py --version` reports the course’s v6.1 release.
- [ ] `IDF_PATH` identifies the intended **framework** directory (not only the parent).
- [ ] You opened [esp32-s3/README.md](esp32-s3/README.md) for build and flash (course project path).
- [ ] `idf.py build` completes successfully in that project (record in lab notes).
- [ ] Flashing and `Hello world!` on the serial monitor (when hardware is available).
- [ ] You can close the terminal, open a fresh activated terminal via the launcher, and build again.

Save version output, build result, port name, and serial output in your lab notes. If hardware is unavailable, record the build result and mark flashing as pending.

## Verification record

Software setup was exercised on **Windows** on **19 October 2026**, using Windows PowerShell. Existing Git and Python installations were reused.

| Check | Observed result |
| --- | --- |
| Git Bash | GNU Bash 5.3.9; Git 2.54.0.windows.1 |
| Git resolved in PowerShell | Git 2.43.0 |
| Python prerequisite | Python 3.11.9 |
| Framework | `D:\dev\esp\v6.1\esp-idf`, tag `v6.1` |
| Source-file checks | All three `Test-Path` checks passed; submodule status showed initialized submodules |
| Tool installation | `install.ps1 esp32s3` completed successfully |
| Activation | Python dependency checks passed; `idf.py --version` reported `ESP-IDF v6.1` |
| Build utilities | CMake 4.0.3; Ninja 1.12.1 |
| Course project (primary) | `nd1/docs/week03/lessons/esp32-s3` |
| Optional practice copy | `D:\dev\projects\hello_world` (verifier-only; not required) |
| Target and build | `esp32s3`; build completed successfully |
| Fresh-session activation and rebuild | Passed in a new PowerShell process |
| Flashing and serial output | Pending hardware verification |
| Native macOS / Linux install in this record | Not exercised here; follow the macOS/Linux section and official Espressif guides |
| Git versions | Git Bash reported 2.54.x; PowerShell resolved a different installed Git (2.43.x). Both must resolve; record the version you use. |

## References

- [ESP-IDF terminal launchers (this course)](scripts/README.md)
- [VS Code ESP-IDF extension: Manual configuration](https://docs.espressif.com/projects/vscode-esp-idf-extension/en/latest/installation.html#manual-configuration-of-esp-idf-and-tools-in-the-esp-idf-extension-for-vs-code)
- [Git for Windows](https://git-scm.com/install/windows)
- [ESP-IDF v6.1: Windows installation](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/windows-setup.html)
- [ESP-IDF v6.1: macOS installation](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/macos-setup.html)
- [ESP-IDF v6.1: Linux installation](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/linux-setup.html)
- [ESP-IDF v6.1: Linux and macOS legacy (script-based) setup](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/linux-macos-setup-legacy.html)
- [ESP-IDF v6.1: Start a project on Windows](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/windows-start-project.html)
- [ESP-IDF v6.1: Start a project on Linux and macOS](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/linux-macos-start-project.html)
- [ESP-IDF Installation Manager: After installing](https://docs.espressif.com/projects/idf-im-ui/en/latest/after_installing.html)
