# week03-app — one project, every workshop

Single Vite + TypeScript app containing all week03 workshops.
Pick which one runs by changing **one import line** in
[`src/main.ts`](src/main.ts).

## Quick start

```bash
npm install        # or: vp install  (Vite+)
npm run dev        # or: vp dev      → http://localhost:5173
```

Open in **Chrome or Edge** — Web Serial and Web Bluetooth are
Chromium-only APIs. `localhost` counts as a secure context, so no
HTTPS setup is needed.

## Layout

```
src/
├── main.ts            ← pick the workshop here (one import)
├── styles.css         ← shared dashboard theme (no per-workshop CSS)
├── workshops/
│   ├── w01_env_check.ts       browser capability check — is my setup right?
│   ├── w02_dom_basics.ts      DOM + state — no device needed
│   ├── w03_raw_console.ts     raw serial lines — plumbing proof
│   ├── w04_serial_read.ts     Web Serial: telemetry read
│   ├── w05_serial_cmd.ts      Web Serial: commands + telemetry
│   ├── w06_web_bluetooth.ts   Web Bluetooth: phone as peripheral
│   └── w07_dashboard.ts       capstone: unified monitor + control
└── lib/
    ├── serial.ts      Web Serial connect + line decoder
    ├── protocol.ts    JSON-lines protocol (shared with the device)
    └── ui.ts          DOM helpers (panels, gauges, log, controls)

device/
└── fake_device.py     the "board" — virtual serial device simulator
                       (next week: the real ESP32 speaks this shape)
```

## The device (this week)

No board needed — `device/fake_device.py` plays the board over a
virtual serial port pair:

```bash
# macOS / Linux — create a linked port pair, note the two /dev/ttys*
socat -d -d pty,raw,echo=0 pty,raw,echo=0
python3 device/fake_device.py /dev/ttysNNN      # one end
# then in the browser, pick the OTHER port in requestPort()

# Windows — com0com virtual pair (COM5 ↔ COM6)
python device/fake_device.py COM5
# browser picks COM6
```
