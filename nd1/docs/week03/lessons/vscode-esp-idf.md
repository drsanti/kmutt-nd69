# Build with the VS Code ESP-IDF extension

> [!NOTE]
> Optional. If you build with `idf.py` in the activated terminal ([esp32-s3/README.md](esp32-s3/README.md)), you can skip this entire file.

Use this guide after [installing ESP-IDF](install-esp-idf.md). The terminal and the VS Code extension are **separate** environments. A successful `idf.py build` in a launcher terminal does not configure the extension’s Build button.

Official reference: [Manual configuration of ESP-IDF and tools in the VS Code extension](https://docs.espressif.com/projects/vscode-esp-idf-extension/en/latest/installation.html#manual-configuration-of-esp-idf-and-tools-in-the-esp-idf-extension-for-vs-code).

## 1. Open the firmware project

**File → Open Folder** and open the firmware project root (has `CMakeLists.txt` and `main/`), for example:

| Platform | Example path |
|---|---|
| Windows | `D:\CODE\2027\kmutt-nd69\nd1\docs\week03\lessons\esp32-s3` |
| macOS / Linux | `~/kmutt-nd69/nd1/docs/week03/lessons/esp32-s3` |

Do not open the repository root as the firmware project. Match the VS Code window to the toolchain: Windows VS Code ↔ Windows ESP-IDF; VS Code WSL ↔ Linux ESP-IDF inside WSL.

Install **ESP-IDF** by Espressif from the Extensions view. All terminal commands below assume you are already in the firmware project root.

## 2. Configure the extension environment once

Choose the route matching your installation.

### Installation managed by EIM

1. Open the Command Palette with **Ctrl+Shift+P**.
2. Run **ESP-IDF: Select Current ESP-IDF Version**.
3. Select your v6.1 installation.
4. Run **ESP-IDF: Doctor Command** and check the framework, Python, CMake, and Ninja paths.

The selection configures the extension's environment. If no installation is listed, check EIM's installation registration as explained in the [official extension setup guide](https://docs.espressif.com/projects/vscode-esp-idf-extension/en/latest/installation.html).

### Existing installation prepared with the course scripts

For the script-based installation, configure `idf.customExtraVars` in the project's `.vscode/settings.json`. These values belong to the extension's child processes; they do not change the system environment. The checked-in settings demonstrate a working Windows setup and must be regenerated on another computer.

1. In **Windows PowerShell** (not Git Bash), from the project root, activate the existing installation:

   ```powershell
   ..\scripts\start-esp-idf.cmd
   ```

   Or: `. ..\scripts\start-esp-idf.ps1`

2. At the **PowerShell** prompt, verify the tools:

   ```powershell
   idf.py --version
   cmake --version
   ninja --version
   (Get-Command xtensa-esp32s3-elf-gcc).Source
   ```

   Continue only when all commands succeed. Follow the [launcher guide](scripts/README.md) if the framework is elsewhere or tools are not installed.

3. Generate extension settings from the installed tools in that same PowerShell session:

   ```powershell
   $toolLines = python "$env:IDF_PATH\tools\idf_tools.py" export --format key-value
   if ($LASTEXITCODE -ne 0) { throw 'Could not export the ESP-IDF tool environment.' }
   $extra = @{
       IDF_PATH = $env:IDF_PATH
       IDF_TOOLS_PATH = $env:IDF_TOOLS_PATH
       ESP_IDF_VERSION = '6.1'
   }
   if (-not $extra.IDF_TOOLS_PATH) {
       $extra.IDF_TOOLS_PATH = Join-Path $env:USERPROFILE '.espressif'
   }
   foreach ($line in $toolLines) {
       if ($line -match '^(OPENOCD_SCRIPTS|ESP_ROM_ELF_DIR|IDF_PYTHON_ENV_PATH|IDF_CCACHE_ENABLE|ESP_IDF_VERSION|PATH)=(.*)$') {
           $key = $Matches[1]
           $value = $Matches[2]
           if ($key -eq 'PATH') {
               $key = 'Path'
               $value = $value -replace ';%PATH%$', ''
           }
           $extra[$key] = $value
       }
   }
   if (-not $extra.Path -or -not $extra.IDF_PYTHON_ENV_PATH) {
       throw 'The exported environment is incomplete. Resolve activation before continuing.'
   }
   New-Item -ItemType Directory -Force .vscode | Out-Null
   $settingsFile = Join-Path $PWD '.vscode\settings.json'
   $settings = if (Test-Path $settingsFile) {
       Get-Content $settingsFile -Raw | ConvertFrom-Json
   } else { [PSCustomObject]@{} }
   $settings | Add-Member -MemberType NoteProperty -Name 'idf.customExtraVars' -Value $extra -Force
   $settings | ConvertTo-Json -Depth 20 | Set-Content $settingsFile -Encoding UTF8
   ```

   This preserves other top-level settings, including clangd settings, and replaces the extension environment with exports for this installation. The existing settings file must use standard JSON, as the course file does. If it contains comments or trailing commas, merge the exported values through VS Code's settings editor instead.

4. Review `.vscode/settings.json`. Its paths are specific to your operating system, user account, and installed tools. Regenerate them after moving the installation or changing tool versions. Do not copy another student's Python or tool paths.
5. Run **Developer: Reload Window**, then **ESP-IDF: Doctor Command**.

The environment must identify the intended framework, its Python environment, and the installed CMake and Ninja tools. Setting `idf.currentSetup` to a directory string alone does not configure an unregistered script-based installation. See [Espressif's manual configuration instructions](https://docs.espressif.com/projects/vscode-esp-idf-extension/en/latest/installation.html#manual-configuration-of-esp-idf-and-tools-in-the-esp-idf-extension-for-vs-code).

### What belongs in the settings file

| Setting | Purpose |
| --- | --- |
| `clangd.arguments` | Enables indexing and lets clangd query the ESP32-S3 compiler for system headers. |
| `idf.customExtraVars.IDF_PATH` | Framework directory containing the ESP-IDF build scripts. |
| `idf.customExtraVars.IDF_TOOLS_PATH` | Installed tool storage, normally the user's `.espressif` directory. |
| `idf.customExtraVars.IDF_PYTHON_ENV_PATH` | Python virtual environment created for this ESP-IDF version. |
| `idf.customExtraVars.ESP_IDF_VERSION` | Version expected by tooling such as the component manager. |
| `idf.customExtraVars.Path` | Windows tool directories needed by extension processes. |
| `OPENOCD_SCRIPTS` and `ESP_ROM_ELF_DIR` | Resources used by debugging and chip tooling. |
| `IDF_CCACHE_ENABLE` | Enables the installed compiler cache. |

Windows `Path` is one semicolon-separated string, not a JSON array. Forward slashes in the checked-in Windows paths are intentional and avoid doubled backslashes in JSON. The cleaned course settings omit unrelated `idf-exe`, DFU, and clangd directories from the build path; a fresh full tool export may include them. Do not remove compiler, Python, CMake, or Ninja paths merely to shorten the string.

Settings are specific to the host operating system.

- **Windows script install:** use the PowerShell export block above.
- **macOS / Linux:** prefer **ESP-IDF: Select Current ESP-IDF Version** if EIM registered the install. Otherwise activate with `bash ../scripts/start-esp-idf.sh`, then follow Espressif’s [manual configuration workflow](https://docs.espressif.com/projects/vscode-esp-idf-extension/en/latest/installation.html#manual-configuration-of-esp-idf-and-tools-in-the-esp-idf-extension-for-vs-code) using `python "$IDF_PATH/tools/idf_tools.py" export --format key-value` in that Bash session. Do not paste Windows `Path` / `%USERPROFILE%` values into a macOS or Linux `settings.json`.

## 3. Build and verify

1. For a new project, run **ESP-IDF: Set Espressif Device Target** and select `esp32s3`.
2. Run **ESP-IDF: Build your project**.
3. Wait for the current build to finish before starting another.
4. Check the ESP-IDF output for `Project build complete`.

The generated application is `build/hello_world.bin`. Continue with the [project's flash and monitor instructions](esp32-s3/README.md) when the board is connected.

## 4. Daily use

Reopen the same project folder and use the extension's Build command. The saved extension settings persist; you do not need to rerun the export procedure each session. To use `idf.py` manually in a new terminal, run the terminal launcher again.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `cmake was not found` | Check Doctor output and the extension's tool `Path`. A terminal activation does not update the extension host. Regenerate the environment or select the registered EIM setup, then reload VS Code. |
| Old macOS paths or another ESP-IDF release appear | Inspect workspace and user settings for stale `idf.customExtraVars`. Configure the intended installation for this project. |
| Version selection lists no setups | A script-based checkout may not be registered with EIM. Use the manual route above. |
| Missing `sdkconfig` or top-level `CMakeLists.txt` | Open the firmware project folder rather than the repository root. A first configuration/build generates `sdkconfig`. |
| `Wait for ESP-IDF build to finish` | Let the current build finish. If a failed build left the extension busy, reload the window before retrying. |
| Full clean reports missing `CMakeCache.txt` | The build folder may already be empty or deleted. Run Build to configure it again. |
| Component manager reports a missing version value | Ensure the exported `ESP_IDF_VERSION` is included with the manual environment. |
| `MSys/Mingw is not supported` or `idf.py` missing in Git Bash | Close Git Bash. Open **PowerShell**, run the launcher (§ Existing installation), and use that session. |
| GCC-option diagnostics appear in the editor | Follow the project's [clangd instructions](esp32-s3/README.md#editor-diagnostics-vs-code-with-clangd); this is separate from the extension's build environment. |

## Verification record

On 19 October 2026, CMake 4.0.3, Ninja 1.12.1, Python 3.11.9, and the ESP32-S3 compiler resolved from the saved Windows extension environment. A PowerShell process using those settings, without calling the activation launcher, built the course project successfully. The extension's Build button and Doctor UI were not exercised automatically; verify them in VS Code using Steps 2 and 3. Flashing remains pending hardware verification.

The settings-generation example follows the same environment-export and JSON-merge procedure. Its PowerShell syntax is checked as documentation; it does not establish that every installation branch was tested on every student's computer.
