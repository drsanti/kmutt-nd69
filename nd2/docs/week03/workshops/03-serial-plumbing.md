# Workshop 03 — Serial plumbing: the fake device

> **Goal:** create a virtual serial port pair, run `fake_device.py`
> as the "board", and prove bytes flow — before any parsing.

**Requirements:** Python ≥ 3.10 + `pip install pyserial`,
socat (mac/Linux) or com0com (Windows)

---

## Why a virtual port pair

Web Serial talks to real OS serial ports. Without a board we make
two ends of a cable inside the machine:

```
┌─────────────────┐                    ┌──────────────────┐
│  fake_device.py │                    │  Chrome (w03)    │
│  (the "board")  │                    │  Web Serial API  │
└────────┬────────┘                    └────────┬─────────┘
         │ opens                                │ opens
         ▼                                      ▼
┌─────────────────┐                    ┌──────────────────┐
│   /dev/ttys002  │────── linked ──────│   /dev/ttys003   │
│   (device end)  │                    │   (browser end)  │
└─────────────────┘                    └──────────────────┘
        bytes written on either end arrive on the other
```

Bytes written on one end appear on the other — exactly like a
USB cable to a real device. This is a **pty pair** (pseudo-terminal
pair): the kernel presents each end as a normal serial device to
whatever opens it, while internally just shuttling bytes between
the two. Neither program can tell it's not a real cable.

Two properties worth internalizing:

- **The pair is symmetric and full-duplex** — both ends can send
  and receive simultaneously. Commands go browser→device the same
  way telemetry goes device→browser, on the same link.
- **"The other end" is the #1 mistake.** If the script opens
  `ttys002` and the browser also opens `ttys002`, the second open
  either fails or steals the port — the pair only works when each
  side holds a *different* end.

## Step 1 — Create the port pair

**macOS / Linux:**

```bash
socat -d -d pty,raw,echo=0 pty,raw,echo=0
# prints two ports, e.g.
#   ... N PTY is /dev/ttys002
#   ... N PTY is /dev/ttys003
```

Leave socat running — it *is* the cable.

**Windows:** install **com0com** (a virtual serial port driver):

1. Download the **signed** build — search for
   `com0com 3.0.0.0 signed` on SourceForge (the unsigned builds
   fail on Windows 10/11 driver-signature enforcement).
2. Run the installer, then open the **com0com Setup Command Prompt**
   it installs (or `setupc.exe` in the install folder).
3. Create a pair:

   ```powershell
   install PortName=COM5 PortName=COM6
   ```

   → `COM5 ↔ COM6` now exist as a linked pair.

> [!WARNING]
> com0com can be finicky on modern Windows — if the driver won't
> install or ports don't appear in Device Manager, a commercial
> alternative like *Virtual Serial Port Driver* (Eltima) is the
> common fallback. The rest of the workshop is identical either way.

> [!WARNING]
> **Linux caveat:** Chrome on Linux enumerates serial devices by
> sysfs type and can **skip `/dev/pts*` PTYs** on some distros —
> the port exists, `fake_device.py` works, but Chrome's picker
> won't list it. macOS and Windows don't have this problem.
> If your pair doesn't show up in Chrome on Linux, that's the cause —
> not a broken setup.

## Step 2 — Start the device

Run it from inside `week03-app/` (the script lives under `device/`):

```bash
cd week03-app
pip install pyserial                        # once
python3 device/fake_device.py /dev/ttys002  # one end
# Windows: python device\fake_device.py COM5
```

You'll see:

```
fake_device on /dev/ttys002 @ 115200 — telemetry 5.0 Hz, Ctrl-C to stop
```

It's already emitting JSON-lines telemetry — a level waveform,
one JSON object per line.

## Step 3 — Prove bytes arrive (raw console)

Switch `main.ts` to `w03_raw_console` — the simplest possible
Web Serial program: open a port, dump every line.

In Chrome: click **Connect** → the browser's port picker appears →
pick **the other end** (e.g. `/dev/ttys003` or `COM6`).

```
← #1  {"type":"telemetry","seq":0,"level":0.512,"ts_ms":...}
← #2  {"type":"telemetry","seq":1,"level":0.634,"ts_ms":...}
```

**Lines arriving = plumbing works.** If you see JSON in the raw
console, workshop 04 is just a decode step.

## Step 4 — Watch commands go the other way

The device also listens. In `w03_raw_console` there's no write UI —
but you can test the return path already:

```ts
// in the browser console, or add a button:
await dev.write('{"type":"led","r":255,"g":0,"b":0}');
```

Watch `fake_device.py`'s terminal print `led → rgb(255,0,0)`.

## The whole exchange, in time order

```
user            browser          port picker       port pair        device
 |                |                  |                |              |
 |-- Connect ---->|                  |                |              |
 |                |-- requestPort()->|                |              |
 |                |                  |-- OS lists --->|              |
 |                |                  |   real ports   |              |
 |-- pick end --->|<- port handle ---|                |              |
 |                |-- open(115200) ------------------>|              |
 |                |                  |                |              |
 |                |                  |   (telemetry already running) |
 |                |                  |<---- JSON lines ------------- |
 |                |<----------------------------------|              |
 |-- dev.write()->|---------------------------------->|-- led(...)-->|
 |                |                  |                |   terminal   |
```

## ✅ Checkpoint

- [ ] `socat` (or com0com) prints two linked port names
- [ ] `fake_device.py` prints its banner and keeps running
- [ ] Browser's port picker lists **the other end** of the pair
- [ ] Raw JSON lines appear in the log after Connect

## 🔧 Troubleshooting

| Symptom | Try |
|---|---|
| Port missing from the picker | Linux: Chrome may skip `/dev/pts` PTYs — see the caveat above; macOS/Windows: is socat still running? |
| Picker shows the port, open fails | you picked the **same end** the script holds — pick the other one |
| `fake_device.py` exits instantly | port name wrong — copy the exact `/dev/ttysNNN` socat printed |
| `import serial` fails | `pip install pyserial` in the same Python that runs the script |

## ➡️ Next

Workshop 04 — decode those raw lines into a live gauge.

<sub>[← Workshop list](README.md)</sub>
