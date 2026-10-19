# Install and Verify ESP-IDF on Windows

Follow these steps in order. This guide starts with Git Bash and uses Windows PowerShell for ESP-IDF installation, builds, and flashing on an ESP32-S3 board. Complete each verification before continuing.

You need internet access, disk space for the framework and tools, and an ESP32-S3 board with a USB data cable for the final hardware steps. Software installation and building can be completed without a board.

## Automated terminal launcher

After preparing the framework and prerequisites, use the [cross-platform launchers](scripts/README.md) instead of repeating the environment commands manually. From Git Bash at the repository root:

```bash
bash nd1/docs/week03/lessons/scripts/start-esp-idf.sh
```

For first-time ESP32-S3 tool installation, add `-InstallTools`. Wait for **ESP-IDF ready** and continue in the PowerShell window. On macOS and Linux, the same launcher opens Bash; see the script README for paths and installation options. The numbered steps below explain the setup and provide a manual fallback.

## 1. Install Git for Windows, including Git Bash

1. Download Git for Windows from the official [Windows download page](https://git-scm.com/install/windows).
2. Run the installer. Include Git Bash and select **Git from the command line and also from 3rd-party software** when choosing the `PATH` option.
3. Complete installation and close any terminals that were already open.
4. Open **Git Bash** from Start and run:

   ```bash
   git --version
   bash --version
   ```

Both commands must print version information. If already installed, perform these checks and continue.

## 2. Open PowerShell from Git Bash

In **Git Bash**, run:

```bash
env -u MSYSTEM powershell.exe -NoLogo -NoExit
```

Wait for a prompt beginning with `PS`. **All subsequent commands use PowerShell**, unless explicitly labeled otherwise. Keep this session open throughout setup.

Git Bash uses MSYS/MinGW, which the installed ESP-IDF tool manager rejects. The command above opens Windows PowerShell and removes the inherited `MSYSTEM` marker from that child process. Do not run `install.sh` or source `export.sh` in Git Bash for this Windows setup.

Git Bash uses paths such as `/d/dev/esp`; PowerShell uses `D:\dev\esp`. WSL is a separate Linux environment and requires a separate Linux toolchain.

## 3. Verify Python and Git in PowerShell

Run:

```powershell
Remove-Item Env:MSYSTEM -ErrorAction SilentlyContinue
python --version
git --version
```

The first command clears any remaining MSYS marker in the Windows PowerShell session; it prints nothing. Expect Python 3.10 or newer and a Git version from the next two commands. Python 3.11.9 was used for the command verification on this computer. Supported versions are listed in [Espressif's prerequisites](https://docs.espressif.com/projects/idf-im-ui/en/latest/prerequisites.html).

### If Python or Git is not recognized

First refresh the current session from the saved Windows environment. This also handles a child PowerShell process inheriting incomplete settings from another shell:

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

After installing Python or Git, close PowerShell and its parent Git Bash, reopen Git Bash, repeat Step 2, and verify both version commands. If Python opens Microsoft Store, check Windows **App execution aliases** and ensure `PATH` selects the installed interpreter.

**Continue only when both `python --version` and `git --version` succeed.**

## 4. Prepare the ESP-IDF v6.1 source

Use these paths or substitute your own consistently. Avoid spaces in framework and project paths.

| Purpose | Path |
| --- | --- |
| Framework | `D:\dev\esp\v6.1\esp-idf` |
| Practice projects | `D:\dev\projects` |

### If the framework is already downloaded

Check it in PowerShell:

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

### If the framework directory does not exist

Run these commands only for a new destination:

```powershell
New-Item -ItemType Directory -Force D:\dev\esp\v6.1 | Out-Null
git clone --branch v6.1 --recursive https://github.com/espressif/esp-idf.git D:\dev\esp\v6.1\esp-idf
Set-Location D:\dev\esp\v6.1\esp-idf
git describe --tags --always
```

Expect `v6.1`. Do not clone over an existing source directory.

## 5. Install the ESP32-S3 tools

Downloading source files does not install the compiler or ESP-IDF Python environment. In the same PowerShell session, run:

```powershell
Set-Location D:\dev\esp\v6.1\esp-idf
.\install.ps1 esp32s3
```

Wait for the script to finish successfully and print `All done!`. The initial tool downloads can exceed 1 GB, and extracted tools need additional space. Keep the terminal open while downloads, extraction, and Python package installation run. It downloads Windows tools and creates the ESP-IDF Python environment, normally under your Windows user profile's `.espressif` directory. The framework and tools can be stored separately. Do not move tool folders after installation.

If PowerShell blocks a trusted installation script, run this session-scoped command and retry:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

If institutional policy prevents this change, contact your IT administrator. If installation reports a download or Python dependency error, resolve it before activation.

### Alternative: use Espressif Installation Manager (EIM)

EIM is Espressif's recommended installer for v6.1. Use this alternative if you prefer a managed installation rather than the source-and-script route above:

1. Follow the official [Windows installation guide](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/windows-setup.html).
2. Install prerequisites when prompted. Select v6.1 through the custom installation options; Easy Installation may select a different release.
3. Select ESP32-S3 support when offered and wait for completion.
4. Open **Manage Installations → Open Dashboard**, select the installed environment, and choose **Open IDF Terminal**.
5. Continue with the verification commands in Step 6. Use the framework path configured by EIM, which may differ from this guide.

## 6. Activate and verify ESP-IDF

For the script-based installation, run in the same PowerShell session:

```powershell
$env:PYTHONUTF8 = '1'
Set-Location D:\dev\esp\v6.1\esp-idf
. .\export.ps1
```

`PYTHONUTF8` enables Python UTF-8 mode for this session and avoids the console encoding warning observed during verification. The first dot followed by a space loads the activation script into the current session. For EIM, use its activated IDF terminal instead.

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

If activation reports `python` is not recognized followed by an invalid expression after `.`, return to Step 3. The second error follows from the missing Python command. If activation reports a missing Python environment or compiler, complete Step 5 first.

Activation affects this terminal only. Running a short-lived `powershell.exe -Command ...` does not activate the parent Git Bash session. Keep PowerShell open; type `exit` when you want to return to Git Bash.

## 7. Create a practice project

Copy the official example into a separate project directory. This keeps practice changes outside the framework installation. First check the destination:

```powershell
Test-Path D:\dev\projects\hello_world
```

Continue with the copy only if this prints `False`. If it prints `True`, use a new project name consistently in the commands below, or use your existing project if it is already your practice copy.

```powershell
New-Item -ItemType Directory -Force D:\dev\projects | Out-Null
Copy-Item -Recurse "$env:IDF_PATH\examples\get-started\hello_world" D:\dev\projects\hello_world
Set-Location D:\dev\projects\hello_world
```

Verify the copied project:

```powershell
Test-Path .\CMakeLists.txt
Test-Path .\main
```

Both checks must print `True`.

## 8. Select the target and build

For the ESP32-S3 board used in this guide:

```powershell
idf.py set-target esp32s3
idf.py build
```

Use the actual chip target if your board is different. For example, an original ESP32 uses `esp32`. The target identifies the chip family, not the board's product name.

`set-target` reconfigures the project and can reset existing configuration. Run it when creating the practice project or intentionally changing targets.

The first invocation of `idf.py` and the first build can take time while Python modules load, ESP-IDF configures the project, and components compile. Wait for the PowerShell prompt to return; do not start a second build in the same directory. A successful build ends with a completion message and flashing instructions. Resolve build errors before connecting the result to a hardware test.

## 9. Connect the board and identify its port

1. Connect the board using a USB data cable.
2. Open **Windows Device Manager → Ports (COM & LPT)**.
3. Note the port that appears when the board is connected, for example `COM5`.
4. If the board has multiple USB connectors, use the connector recommended by its manual for programming and serial output.

If no port appears, try another data cable or USB port and check the board documentation. A USB-to-UART bridge may require the matching driver from its manufacturer. Native USB connections can appear differently and may receive another COM number after reset.

Close other serial monitors before flashing or opening the ESP-IDF monitor.

## 10. Flash and monitor

Replace `COM5` with your board's port:

```powershell
idf.py -p COM5 flash monitor
```

Flashing writes the application to the board and replaces its current firmware. The monitor then displays serial output. Look for `Hello world!` and the example's runtime messages. Press **Ctrl+]** to exit the monitor.

If flashing cannot connect, follow your board's download-mode procedure. On many boards, this means holding **BOOT**, pressing and releasing **RESET/EN**, then releasing **BOOT** before retrying. Button names and timing depend on the board.

A successful build verifies the software toolchain. Successful flashing and readable application output verify the programming and serial connection as well. The `hello_world` example does not provide an LED test.

## 11. Daily workflow

For each new development session:

1. Run the [terminal launcher](scripts/README.md) from the repository root (`bash nd1/docs/week03/lessons/scripts/start-esp-idf.sh` in Git Bash). Alternatively, open the EIM IDF terminal or follow Steps 2, 3, and 6 manually. Tool installation is normally needed only once.
2. Change to your project directory.
3. Build and, when ready, flash and monitor:

   ```powershell
   Set-Location D:\dev\projects\hello_world
   idf.py build
   idf.py -p COM5 flash monitor
   ```

You do not need to reinstall the tools or run `set-target` every session. To open the project's configuration menu, use `idf.py menuconfig` from the project directory.

## 12. Troubleshooting

| Symptom | What to check or do |
| --- | --- |
| `MSys/Mingw is not supported` | You are using Git Bash/MSYS or a child shell inheriting `MSYSTEM`. Follow the Git Bash instructions in Step 2, or open the EIM IDF terminal directly. |
| `python` is not recognized, followed by a dot-sourcing error | Complete the Python prerequisite check in Step 3. Verify `python --version`, install the tools if needed, and retry activation. |
| `idf.py` is not recognized | Open the matching EIM IDF terminal or activate the script-based environment in this terminal. |
| Wrong ESP-IDF version is reported | Close the terminal and activate the intended installation. Check `$env:IDF_PATH` and `Get-Command idf.py`. |
| Python environment or compiler is missing | Confirm the installation completed. Repair the selected installation with EIM, or rerun `install.ps1 esp32s3` for the script-based setup, then activate it. |
| Script execution is disabled | Use the session-scoped policy command in Step 5; check institutional policy if it remains blocked. |
| Missing submodule files | For a Git checkout, run `git submodule update --init --recursive` in the framework directory. For an incomplete ZIP, use a complete official package or EIM. |
| `CMakeLists.txt` cannot be found | Run project commands from `D:\dev\projects\hello_world`, where the top-level `CMakeLists.txt` exists. |
| COM port is absent or access is denied | Check the cable, connector, driver, and Device Manager; close any other program using the port. |
| Flashing stays at `Connecting...` | Verify the port and chip target, then follow the board's download-mode procedure. |
| Serial output is unreadable or absent | Check the monitor port and configured console interface. Press RESET/EN after opening the monitor; the example normally uses 115200 baud. |
| Build errors after moving a project or changing ESP-IDF versions | Reactivate the intended environment and run `idf.py fullclean`, then rebuild. This removes generated build files; preserve any project work before changing configuration. |

## 13. Completion checklist

Record the following evidence before proceeding to the next lesson:

- [ ] Git for Windows is installed, and `git --version` works in Git Bash and PowerShell.
- [ ] `idf.py --version` reports the course's v6.1 release.
- [ ] `$env:IDF_PATH` identifies the intended installation.
- [ ] The practice project is outside the ESP-IDF framework directory.
- [ ] The project uses the correct chip target.
- [ ] `idf.py build` completes successfully.
- [ ] Flashing completes successfully on the selected COM port.
- [ ] The serial monitor displays `Hello world!` from the connected board.
- [ ] You can close the terminal, open a fresh activated terminal, and build again.

Save the version output, build result, COM port, and a screenshot or copy of the serial output in your lab notes. If hardware is unavailable, record the build result and mark flashing and runtime verification as pending.

## Verification record

Software setup was exercised on this Windows computer on **19 October 2026**, using Windows PowerShell launched from the workspace environment. Existing Git and Python installations were reused. The Git Bash version commands were also run using the installed Windows Git Bash executable.

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
| Practice project | `D:\dev\projects\hello_world` |
| Target and build | `esp32s3`; build completed successfully and generated application and bootloader binaries |
| Fresh-session activation and rebuild | Passed in a new PowerShell process |
| Flashing and serial output | Pending hardware verification |

Different Git versions can appear when shells select different installed copies. The important prerequisite is that Git resolves successfully; record the version you actually use. Installation GUI steps and the Python/Git installation branches were documented from official instructions; those installers were not rerun because the prerequisites were already present.

## References

- [Git for Windows download and installation](https://git-scm.com/install/windows)
- [ESP-IDF v6.1: Windows installation](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/windows-setup.html)
- [ESP-IDF v6.1: Start a project on Windows](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/windows-start-project.html)
- [ESP-IDF v6.1: Script-based tool setup](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/windows-setup-update.html)
- [ESP-IDF Installation Manager: After installing](https://docs.espressif.com/projects/idf-im-ui/en/latest/after_installing.html)
- [ESP-IDF tool manager source: MSYS/MinGW environment check](https://github.com/espressif/esp-idf/blob/v6.1/tools/idf_tools.py)
