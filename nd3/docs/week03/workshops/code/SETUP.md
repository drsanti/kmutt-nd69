# Every new terminal — copy/paste

Run these from this folder (`code/`). A new terminal forgets
PATH and the Python venv.

**Two different installs (do not mix them up):**

| What | Role | Windows | macOS |
|---|---|---|---|
| `robotos-v0.3.0-…/` zip | CLI (`robotos` on PATH) | `…-windows-x64` | `…-macos-arm64` (or linux) |
| `robotos-0.3.0-*.whl` | Python `import robotos` | `…-win_amd64.whl` | `…-py3-none-any.whl` |

Each wheel embeds that OS’s native library (`.dll` / `.dylib`). Install only the one for your machine (`pip install` once in the venv; see workshop 02).

## Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
$env:PATH = "$PWD\robotos-v0.3.0-windows-x64\bin;$env:PATH"
```

Or one shot:

```powershell
. .\env.ps1
```

Check: `python -c "import robotos; print(robotos.Node.version())"` and `robotos version` → `0.3.0`.

Use **`python`**, not `python3`. Use **PowerShell**, not Git Bash
(for robotos **and** for ESP-IDF: `idf.py` / `export.ps1` — Git Bash
sets `MSYSTEM` and breaks the Espressif toolchain).

## macOS / Linux

```bash
source .venv/bin/activate
export PATH="$PWD/robotos-v0.3.0-macos-arm64/bin:$PATH"   # or …-linux-x64/bin
```

Or one shot:

```bash
source ./env.sh
```

Check: `python3 -c "import robotos; print(robotos.Node.version())"` and `robotos version`.

## Simulator coordinate compatibility (2026-11-15)

The separate warehouse simulator uses Y-up (XZ floor). Its odometry topics
retain ROS-style XY floor coordinates: odom x = sim x, odom y = -sim z;
yaw is about message +Z. Keep Twist.linear.x and Twist.angular.z.
See [coordinate frames](coordinate-frames.md). The Windows CLI/library and
both Windows/macOS Python wheels were refreshed from the current workshop
bundles; these wheels now include geometry, nav, laser, tf and viz messages.
Linux/macOS native CLI binaries were not rebuilt on Windows.
