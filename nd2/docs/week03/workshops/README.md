# ND02 — Week 03: Hands-on Workshops

> From concepts to code — a browser app that talks to hardware.
> Each workshop is a step-by-step guide; all code lives in one
> Vite + TypeScript project, [`week03-app/`](week03-app/).

All workshops run **entirely on your laptop** — the ESP32 board
arrives next week. The device is simulated: a Python script on a
virtual serial port, and (for BLE) your phone.

## 📚 Workshop list

| # | Workshop | What you get |
|---|---|---|
| 01 | [Getting started — Vite+ environment](01-getting-started.md) | `vp` toolchain + app running on localhost |
| 02 | [DOM + state — the control panel](02-dom-basics.md) | a working dashboard UI, no device |
| 03 | [Serial plumbing — the fake device](03-serial-plumbing.md) | virtual serial pair + `fake_device.py` + raw console |
| 04 | [Web Serial read — telemetry](04-serial-read.md) | `requestPort` → streams → live gauge |
| 05 | [Web Serial write — commands](05-serial-cmd.md) | LED color + rate control — full loop |
| 06 | [Web Bluetooth — phone as peripheral](06-web-bluetooth.md) | real BLE: scan → connect → read |
| 07 | [Capstone — device dashboard](07-dashboard.md) | the full monitor + control app |

## ⚙️ Prerequisites

| Item | Why | Where |
|---|---|---|
| Vite+ (`vp` CLI) | dev server + toolchain | `curl -fsSL https://vite.plus \| bash` |
| Chrome or Edge | Web Serial + Web Bluetooth are **Chromium-only** | — |
| Python ≥ 3.10 + pyserial | the fake device | `pip install pyserial` |
| socat (mac/Linux) or com0com (Win) | virtual serial port pair | `brew install socat` / `apt install socat` / com0com setup |
| Smartphone + nRF Connect | BLE peripheral for w06 | app store |

> [!IMPORTANT]
> **No board needed this week.** The "device" is simulated —
> `device/fake_device.py` speaks the same JSON-lines protocol
> the real board will use next week, so nothing you build is wasted.

## 🗂️ The project — one app, all workshops

[`week03-app/`](week03-app/) contains every workshop as a module.
You switch between them with **one import line** in `src/main.ts`:

```ts
import { run } from "./workshops/w04_serial_read";   // ← pick one
run();
```

Workshops 03–07 share `src/lib/` helpers (serial connect, protocol
codec, UI components) — so each workshop file shows only the new
concept, not boilerplate.

<sub>[← Week 03](../README.md)</sub>
