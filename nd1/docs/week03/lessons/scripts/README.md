# ESP-IDF development terminal launchers

```
 Windows PowerShell              macOS / Linux Terminal
 ┌─────────────────────┐         ┌─────────────────────┐
 │ start-esp-idf.cmd   │         │ start-esp-idf.sh    │
 │   or .ps1           │         │                     │
 └──────────┬──────────┘         └──────────┬──────────┘
            │                               │
            ▼                               ▼
 ┌─────────────────────┐         ┌─────────────────────┐
 │ PowerShell session  │         │ Bash session        │
 │ (export.ps1)        │         │ (export.sh)         │
 └──────────┬──────────┘         └──────────┬──────────┘
            │                               │
            └───────────────┬───────────────┘
                            ▼
                  ┌──────────────────┐
                  │  ESP-IDF ready   │
                  └──────────────────┘
```

The examples below assume your current directory is `nd1/docs/week03/lessons/esp32-s3`, the included firmware project root. If you cloned the repository elsewhere, use the same relative paths.

Run a launcher each time you need a new ESP-IDF terminal. It activates ESP-IDF, prints the version, and opens your chosen working directory. Keep the terminal open for `idf.py` commands and type `exit` when finished.

These scripts reuse an existing ESP-IDF installation. They do not download the framework, install operating-system prerequisites, edit shell profiles, change saved `PATH` settings, or flash a board. Tool installation runs only when explicitly requested.

## 1. Prepare the prerequisites once

- **Windows:** install [Git for Windows](https://git-scm.com/install/windows) (so `git` works in PowerShell) and supported Windows Python with command-line access. Follow the [installation lesson](../install-esp-idf.md) through framework preparation. The launcher can refresh inherited Windows paths and find Python through the `py` launcher if available. **Use PowerShell for ESP-IDF — not Git Bash.**
- **macOS:** install the prerequisites and ESP-IDF source described in the [official macOS setup guide](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/macos-setup.html).
- **Linux:** install the prerequisites and ESP-IDF source described in the [official Linux setup guide](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/linux-setup.html). WSL uses this route and a Linux toolchain; it does not reuse the Windows compiler installation.

Use a complete source checkout, including submodules. Keep framework and project paths free of spaces, as required by the ESP-IDF build system. Change the example paths below to match your computer. The project directory must already exist; it can be the repository directory before you create a firmware project.

If you installed with EIM and it uses custom tools or activation settings, prefer EIM's **Open IDF Terminal**. These launchers use the framework's `export.ps1` or `export.sh`; they are intended for the script-based setup. An intentionally configured `IDF_TOOLS_PATH` is inherited and must match the tool installation.

> [!IMPORTANT]
> **Windows:** run ESP-IDF in **PowerShell** only. Do not type `idf.py` in
> Git Bash — MSYS/MinGW (`MSYSTEM`) is unsupported by Espressif’s tools.

## 2. Windows: launch from PowerShell

Assume you are already in the course firmware project root (`…/nd1/docs/week03/lessons/esp32-s3`). This folder **is** the firmware project. In **Windows PowerShell**, run:

```powershell
..\scripts\start-esp-idf.cmd
```

Or activate in the current PowerShell session:

```powershell
. ..\scripts\start-esp-idf.ps1
```

This activates `D:\dev\esp\v6.1\esp-idf` (or `IDF_PATH` if set) and keeps the current directory as the working directory. Wait for **ESP-IDF ready** and a `PS ...>` prompt. Run all `idf.py` commands in that PowerShell session.

For the first tool installation, run instead:

```powershell
..\scripts\start-esp-idf.cmd -InstallTools
```

Wait for installation and activation to finish. The installation target defaults to `esp32s3`. This installs tools; it does not change a project's chip target.

For a different framework or an existing project:

```powershell
..\scripts\start-esp-idf.cmd -IdfPath 'D:\dev\esp\v6.1\esp-idf' -ProjectPath 'D:\dev\projects\hello_world'
```

You can combine `-InstallTools` with `-Target esp32s3` and the path options.

If Windows blocks a trusted local script, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` in PowerShell, then retry the `.ps1` command in that same session. Institutional policy may require IT assistance. The launchers do not bypass execution policy.

Double-clicking `start-esp-idf.cmd` also opens PowerShell with the default framework path; `cd` to your project before building if the working directory is wrong.

## 3. macOS or Linux: launch from Terminal

From the course firmware project root, assuming the framework is at `~/esp/esp-idf`:

```bash
bash ../scripts/start-esp-idf.sh
```

For a custom location and an existing project:

```bash
bash ../scripts/start-esp-idf.sh \
  --idf-path "$HOME/esp/esp-idf" \
  --project-path "$HOME/esp/hello_world"
```

For first-time tool installation:

```bash
bash ../scripts/start-esp-idf.sh \
  --idf-path "$HOME/esp/esp-idf" --install-tools --target esp32s3
```

The launcher opens **Bash**, including when your normal macOS shell is Zsh. It loads `~/.bashrc` if present, then activates ESP-IDF. It does not load Zsh settings. The framework defaults to `IDF_PATH` when set, otherwise `~/esp/esp-idf`. Windows defaults to `IDF_PATH` when set, otherwise `D:\dev\esp\v6.1\esp-idf`.

Execute the launcher with `bash`; do not `source` it. It opens a child shell, so activation ends when you type `exit`. Do not run `esp-idf-shell.bash` directly; it is the internal initialization file.

## 4. Verify, then open the project guide

Once **ESP-IDF ready** appears, run:

```text
idf.py --version
```

Expect the installed version (v6.1 for this course). For build, ports, and flash on the **course project**, follow [esp32-s3/README.md](../esp32-s3/README.md) — not a separate `hello_world` copy unless you created one for practice in the install guide.

## VS Code extension builds

These launchers activate terminal sessions. They do not configure the ESP-IDF extension's Build button. Follow the [VS Code extension guide](../vscode-esp-idf.md) to select or export the installation environment once. Afterward, the extension reuses its saved settings.

## Troubleshooting

| Problem | Next step |
| --- | --- |
| Framework not found | Pass `-IdfPath` on Windows or `--idf-path` on macOS/Linux; point to the directory containing the export script and `tools/idf.py`. |
| Python or Git missing | Install the prerequisite and reopen the terminal. Installing the framework alone is insufficient. |
| Missing compiler or Python environment | Run once with `-InstallTools` or `--install-tools`, using the same tools path as activation. |
| Project directory does not exist | Create the project first or omit the project-path option to keep the current directory. |
| `MSys/Mingw is not supported` | You launched ESP-IDF from Git Bash. Close it; use **PowerShell** and §2. |
| `idf.py` unavailable after closing the launcher | Activation is per session. Open PowerShell in the project root and run the launcher again. |
| Wrong ESP-IDF version | Pass the intended framework path explicitly. |

## Sharing and regeneration

The launcher files contain no saved personal Python or compiler directory: they discover the installation from the supplied path, `IDF_PATH`, or their documented default. They do not rewrite `.vscode/settings.json`. The VS Code extension environment is a separate per-machine configuration; regenerate it using the [extension guide](../vscode-esp-idf.md) after cloning on another computer.

## Verification limits

The Windows launcher was exercised with the installed ESP-IDF v6.1 on 19 October 2026: activation from PowerShell (`.cmd` / `.ps1`), the optional tool-installation route, and a `hello_world` build passed. `idf.py --version` worked at the activated PowerShell prompt. Missing-framework handling returned a failure status.

On Linux, Bash syntax checks and fixture-based checks passed for activation, installation target forwarding, working-directory selection, activation failure, and invalid or missing paths/arguments. The fixture verifies launcher behavior; it is not a real ESP-IDF toolchain.

See the verification record in the installation lesson for the tested Windows environment. Native macOS activation requires validation on a Mac; Linux launcher control flow can be tested separately from a real Linux ESP-IDF toolchain. A successful build does not establish that flashing or serial output works.
