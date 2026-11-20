# Week 08 troubleshooting

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-guide-2e8b57?style=flat-square)

[Week 08 index](README.md) · [Week 03 setup](../week03/lessons/README.md)

## Python version & installation errors

### `ModuleNotFoundError: No module named 'numpy._core._multiarray_umath'` or NumPy C-extension failure

- **Cause:** Your terminal's default `python` is **Python 3.14** (an unreleased pre-release with experimental free-threading `cp314t`). Pre-compiled C-extensions for NumPy and TensorFlow are binary-incompatible with Python 3.14.
- **Fix:** Use **Python 3.10 to 3.13**. Create your virtual environment specifically pointing to Python 3.11 or 3.12:
  ```powershell
  # Windows PowerShell:
  py -3.11 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
  In Git Bash (`MINGW64`):
  ```bash
  py -3.11 -m venv .venv
  source .venv/Scripts/activate
  pip install -r requirements.txt
  ```

### Which Python command should I use? (`python`, `python3`, `py`, or `py3`)

| Error / Symptom | Cause | Solution |
|---|---|---|
| **`bash: py: command not found`** | `py` is the Windows Python launcher; it does not exist on Linux or macOS. | Use `python3` or `python` instead. |
| **`python: command not found`** | Python is not symlinked to `python` or virtual environment is not activated. | On Linux/macOS: use `python3`. On Windows: use `py`. Or activate your `.venv`. |
| **Windows opens Microsoft Store** | Windows 10/11 "App Execution Aliases" intercepts `python.exe` when no Python path is found. | Run `py` instead, or disable the Microsoft Store alias in *Windows Settings → Apps → Advanced app settings → App execution aliases*. |
| **`ModuleNotFoundError: ... numpy`** (when python 3.14 is installed) | System PATH defaults to Python 3.14 which breaks C-extensions. | On Windows: use `py` or `py -3.11`. |

---

### Windows PowerShell: "running scripts is disabled on this system" (`PSSecurityException`)

- **Cause:** Windows PowerShell default execution policy blocks running downloaded `.ps1` scripts.
- **Fix:** Enable script execution for your current process:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\.venv\Scripts\Activate.ps1
  ```

## PC microphone

### "PortAudio library not found" / `OSError` when importing `sounddevice`

- **Windows / macOS:** `pip install --force-reinstall sounddevice` (the wheel bundles PortAudio).
- **Linux (Debian/Ubuntu):** `sudo apt install libportaudio2`, then reinstall `sounddevice`.

### Recording is silent (all clips around −90 dBFS or lower) — microphone permission

| OS | What to check |
|---|---|
| **macOS** | *System Settings → Privacy & Security → Microphone*: enable the app that runs Python (Terminal, iTerm, or VS Code). macOS asks only once; if you clicked "Don't Allow", enable it here and **restart that app**. |
| **Windows 10/11** | *Settings → Privacy & security → Microphone*: turn on **Microphone access**, **Let apps access your microphone**, and **Let desktop apps access your microphone** (Python is a desktop app). Check that the right input is the default under *Settings → System → Sound → Input*. |
| **Linux** | Check that the input is not muted and is the default (`pavucontrol` → *Input Devices*, or `wpctl status` on PipeWire). Your user may need the `audio` group on some distributions. Sandboxed apps (Flatpak or Snap VS Code) may block the mic: run from a normal terminal. |

Then:

```bash
python collect_pc_mic.py --list-devices               # find the input device index
python collect_pc_mic.py --device 2 --labels red --takes 1
```

### "Invalid sample rate" or an error opening the stream

Some devices do not support 16 kHz directly. Try another device (`--device`), such as the built-in mic instead of a Bluetooth headset (Bluetooth headsets often switch to low-quality "call" mode). A USB microphone usually supports 16 kHz.

### Clips sound processed, or the volume changes by itself

Turn off noise suppression, voice isolation, echo cancellation, and automatic gain:

- **Windows:** Sound settings → your microphone → *Audio enhancements: Off*.
- **macOS:** Control Centre → *Mic Mode: Standard* (shown while an app uses the mic).
- **Meeting apps** (Zoom, Teams, Discord): quit them while recording; they can change the device settings.

### `live_infer_pc.py` prints "no samples for 0.5 s"

Another program owns the microphone, or the device was unplugged. Close other audio apps and select the device explicitly with `--device`.

## Board, serial port, and the workshop protocol

Symptoms for `collect.py`, `collect_imu.py`, `live_infer_board.py`, and `live_infer_imu.py` (board running the workshop prebuilt firmware).

| Symptom | Likely cause → fix |
|---|---|
| `cannot open COM5` / port busy / access denied | **Another program owns the port** — most often the workshop demo tab in Chrome/Edge (Web Serial keeps the port while the tab is connected). Click *Disconnect* or close the tab; also close serial monitors, `idf.py monitor`, Arduino IDE, `rbdev`, and other scripts. **Linux:** add yourself to `dialout` (or `uucp`), then log out and in. **macOS:** use `/dev/cu.usbmodem…`, not `/dev/tty.…`. List ports with `python -m serial.tools.list_ports` |
| `No BoardInfo frame received` | Wrong port, or the board is not running the workshop firmware (for example `kws-inference` is still flashed). Reflash with `esptool`: `cd hardware-interface-workshop/firmware-prebuilt/es3c28p` → `python -m esptool -p <PORT> write-flash "@flash_args"`. BoardInfo comes at boot and about every 10 s, so the script waits up to 12 s |
| `Wrong board for collect.py … needs MIC` | A ws28p (caps `0x3c`) is attached. Use the ES3C28P (caps `0x33`), or record with `collect_pc_mic.py` |
| `Wrong board for collect_imu.py … needs IMU` | An ES3C28P (caps `0x33`, no IMU) is attached. Use the ws28p and its prebuilt image (`cd firmware-prebuilt/ws28p` → `python -m esptool -p <PORT> write-flash "@flash_args"`) |
| `No reply from board - is the workshop prebuilt firmware on the board?` | The `MicCmd` got no `CmdAck` within 2.5 s. Old or different firmware, or the board is rebooting. Reflash the prebuilt image; unplug/replug |
| `board rejected MicCmd (rc=…)` | The firmware refused the command (for example the audio codec did not start). Check the board's screen/log, power-cycle |
| `[retry] … chunk(s) lost on USB (seq gap)` now and then | `MicPcm.seq` jumped: USB dropped a frame. The take is re-recorded automatically. If it happens on every take: close heavy programs, avoid USB hubs, do not run two board scripts at once |
| `[retry] … samples lost (timestamp gaps)` on every IMU take | Same cause for IMU frames. Raise `--max-lost` a little (the window is interpolated), or fix the USB path |
| `mic stream stalled` / no audio | The stream was not started (no `CmdAck`), the board reset (opening USB can reset it — the scripts wait 2.5 s), or another program reads the port |
| Board resets when the port opens | Normal with native USB on some hosts. The scripts wait 2.5 s (`SETTLE_S` in `wire.py`) before trusting data |
| `--info` level stays near −90 dBFS | Microphone muted or gain 0: run with `--gain 60`. If still silent, check the mic in workshop lab ex11/ex28 (browser) |
| Clips are clipped (peak 32767) | Lower `--gain` (for example 40) and re-record that session; keep the same gain for all sessions |
| `esptool` cannot find the port | Close everything that holds the port (see first row). Set it explicitly: `-p COMx` or `-p /dev/ttyACM0` |
| Board stops responding after flashing | Native USB re-enumerates after reset. Unplug and replug, or hold BOOT while pressing RESET to enter download mode (Week 02, Lesson 06) |

## Training and testing

| Symptom | Likely cause → fix |
|---|---|
| `no clips for ['_unknown_']` | Every label needs data. Record `_silence_` and `_unknown_` too |
| `[skip] … does not match` | File names must be `<session>_<speaker>_<device>_<index>.wav`, for example `s01_alice_pc_0003.wav` |
| `only 1 group(s): falling back to a random clip split` | Record more sessions or speakers; until then, the test score is optimistic |
| Validation accuracy stuck at chance | Too little data or a label mix-up. Listen to a few clips per label; check that every class has clips in train **and** val |
| Great on PC, poor on board | Domain shift (Lesson 02): add board clips, test with `--device board` and live with `live_infer_board.py`, keep `--gain` constant |
| int8 much worse than float32 | Representative data too narrow; include all devices and noise levels. Check for inputs saturating at −128/127 |
| `verify_c_features.py`: `MISMATCH` | Python and C constants differ. Make `kws_common.py` and `kws_features.h` identical again |
| No C compiler for `verify_c_features.py` | Linux: `sudo apt install gcc`. macOS: `xcode-select --install`. Windows: use WSL or MSYS2, or run the check in Colab |

## Firmware build and run

| Symptom | Likely cause → fix |
|---|---|
| Component download fails | The first build needs internet access to the ESP Component Registry. Retry, or check your proxy |
| App does not fit the partition | Keep `CONFIG_PARTITION_TABLE_SINGLE_APP_LARGE=y`; delete `sdkconfig` after changing `sdkconfig.defaults`, then rebuild |
| `AllocateTensors failed` | Arena too small (raise `KWS_ARENA_BYTES`) **or** an op is not registered. The log names the missing op; add it to the resolver |
| `model shape/type does not match` | You exported a model with a different input size or label count; re-export and check `kws_labels.h` |
| `dropped` keeps growing | Inference is slower than the hop: increase `KWS_HOP_BLOCKS`, keep `-O2`, and check that the ESP-NN optimisations are on (default in esp-tflite-micro) |
| `kws-inference` works poorly but `live_infer_board.py` was fine | Capture path differs (Lesson 05): compare the dBFS column with your `collect.py` levels and adjust `KWS_MIC_GAIN_DB`; try `KWS_MIC_SLOT` 0 or 1 |
| After `kws-inference`, the board scripts and browser demos no longer connect | Expected: it replaced the workshop firmware. Reflash with `esptool`: `cd firmware-prebuilt/es3c28p` → `python -m esptool -p <PORT> write-flash "@flash_args"` |
| LED never lights | GPIO42, WS2812 model, and colour order (GRB) — Week 02, Lesson 11. Also check whether the score ever reaches `KWS_THRESHOLD` in the log |
| Always detects the same word | Placeholder model still in use (it was trained on synthetic tones). Export your own model |

## IMU gesture track

| Symptom | Likely cause → fix |
|---|---|
| `--check` shows about 25 Hz instead of 50 Hz | Frames are being lost on USB; see the seq/timestamp rows above |
| `|a|` far from 9.8 when still | The board is moving, or the units are wrong (old firmware). Re-check with workshop lab ex20 |
| One person's gestures are never recognised | Person-specific style: add their windows, use more augmentation; check the person-disjoint test accuracy, not the training accuracy |
| Works flat, fails when the board is held upright | Orientation (Lesson 07 §5): agree on a grip, add data in that grip, or increase rotation augmentation |
| `idle` triggers gestures while walking | Add walking / handling windows to `idle` and retrain |
| `train_imu.py`: "Need windows from at least 2 people" | The test set holds out whole people; collect with a classmate or a second `--person` tag for a second session |
