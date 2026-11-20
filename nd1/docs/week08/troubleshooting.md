# Week 08 troubleshooting

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-guide-2e8b57?style=flat-square)

[Week 08 index](README.md) · [Week 03 setup](../week03/lessons/README.md)

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

## Board, serial port, and logger

| Symptom | Likely cause → fix |
|---|---|
| `collect.py`: `no 'PONG' line` | Logger not flashed, wrong port, or `idf.py monitor` still open. Close the monitor and check the port with `python -m serial.tools.list_ports` |
| Port busy / access denied | Another program owns it (monitor, Arduino IDE, a second script). **Linux:** add yourself to `dialout` (or `uucp`), then log out and in. **macOS:** use `/dev/cu.usbmodem…`, not `/dev/tty.…` |
| `checksum mismatch` now and then | Log text mixed into the stream or USB hiccups; the script retries. If it is constant, keep the log level at WARN and do not print from other tasks |
| Board resets when the port opens | Some hosts toggle DTR/RTS. `collect.py` opens with DTR/RTS low; if it still resets, wait 2 s and run again |
| `--info` shows both slots at −90 dBFS | Codec not running: check `es8311_codec_new` errors in the boot log (no I2C ACK at 0x18 means wiring, pull-ups, or power), and the I2S pins (MCLK 4, BCLK 5, WS 7, DIN 6) |
| The level never changes when you speak | Wrong slot: set `MIC_SLOT` / `KWS_MIC_SLOT` to the slot that moves |
| Clips are clipped (peak 32767) | Lower `MIC_GAIN_DB` in **both** projects and re-record |
| Board stops responding after flashing | Native USB re-enumerates after reset. Unplug and replug, or hold BOOT while pressing RESET to enter download mode (Week 02, Lesson 06) |

## Training and testing

| Symptom | Likely cause → fix |
|---|---|
| `no clips for ['_unknown_']` | Every label needs data. Record `_silence_` and `_unknown_` too |
| `[skip] … does not match` | File names must be `<session>_<speaker>_<device>_<index>.wav`, for example `s01_alice_pc_0003.wav` |
| `only 1 group(s): falling back to a random clip split` | Record more sessions or speakers; until then, the test score is optimistic |
| Validation accuracy stuck at chance | Too little data or a label mix-up. Listen to a few clips per label; check that every class has clips in train **and** val |
| Great on PC, poor on board | Domain shift (Lesson 02): add board clips, test with `--device board`, check that gain and slot match, run `verify_c_features.py` |
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
| LED never lights | GPIO42, WS2812 model, and colour order (GRB) — Week 02, Lesson 11. Also check whether the score ever reaches `KWS_THRESHOLD` in the log |
| Always detects the same word | Placeholder model still in use (it was trained on synthetic tones). Export your own model |
