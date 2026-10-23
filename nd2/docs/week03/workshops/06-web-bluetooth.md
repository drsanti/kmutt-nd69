# Workshop 06 — Web Bluetooth: the cable disappears

> **Goal:** connect the browser to a real BLE peripheral — your
> phone, standing in for the board — and read a value over the air.

**Requirements:** Chrome/Edge, a smartphone with **nRF Connect**
installed (free, iOS + Android)

---

## The honest constraint

Web Bluetooth needs a real BLE device — there's no reliable
in-browser simulation. So the phone plays the peripheral:
**nRF Connect** can run a GATT *server* on the phone, advertising
like real hardware.

The API flow is identical to what the real board will use —
you're learning the real thing, just on a different radio.

## How BLE is shaped — the GATT tree

BLE data isn't a byte stream like serial — it's a **tree of typed
attributes** you address by UUID:

```
┌────────────────────────────────────────────────────┐
│ peripheral (the phone / the board)                 │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ service:  battery_service        (a folder)  │  │
│  │   characteristic: battery_level   (a file)   │  │
│  │   characteristic: ...          (another one) │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ service:  device_information                 │  │
│  │   characteristic: manufacturer_name          │  │
│  │   characteristic: model_number               │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ service:  your custom service ...            │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

Three fixed levels: **service → characteristic → value**.

- A **service** groups related characteristics — Battery, Device
  Info, or your own. Standard services have assigned UUIDs; custom
  ones use 128-bit randoms.
- A **characteristic** is one datum + its *operations* — a
  characteristic can be readable, writable, notifiable, or any
  combination. `battery_level` is read+notify: you can poll it,
  or subscribe and get pushed.
- **Notifications are the pub/sub of BLE** — `startNotifications()`
  is "subscribe", `readValue()` is "poll once". A peripheral that
  pushes sensor data uses notifications exactly like a serial
  device streaming telemetry lines.

## Step 1 — Make the phone a peripheral

In nRF Connect on the phone:

1. Open the app → **Configure GATT server** (or Advertiser tab)
2. Add a service — e.g. **Battery Service** (`battery_service`)
3. Start advertising

Your phone is now a BLE device broadcasting a service UUID.

## Step 2 — Scan and connect

`w06_web_bluetooth` in `main.ts`. Click **Scan & connect**:

```ts
const device = await navigator.bluetooth.requestDevice({
  acceptAllDevices: true,
  optionalServices: ["battery_service", "device_information"],
});
const server = await device.gatt.connect();
```

- **`requestDevice()` shows the browser's BLE picker** — you see
  every nearby advertiser and pick yours (same user-consent model
  as `requestPort`)
- **`gatt.connect()` opens the link** — GATT = the BLE attribute
  protocol; services contain characteristics (like folders and files)

## Step 3 — Read a characteristic

If your peripheral exposes `battery_service`:

```ts
const svc  = await server.getPrimaryService("battery_service");
const ch   = await svc.getCharacteristic("battery_level");
const v    = await ch.readValue();
// v.getUint8(0) → a number 0..100
```

Three hops: **service → characteristic → value**. That traversal is
the heart of every BLE interaction — you'll do it dozens of times
next week.

## The connection, in time order

```
user           browser          phone (BLE)       GATT server
 |               |                  |                 |
 |-- Scan ------>|                  |                 |
 |               |-- requestDevice >|-- advertises -->|
 |               |                  |   (UUIDs + name)|
 |-- pick ------>|                  |                 |
 |               |<-- device -------|                 |
 |               |- gatt.connect()->|-- link -------->|
 |               |                  |   open          |
 |               |-- getPrimarySvc->|                 |-- looks up
 |               |-- getChar ------>|                 |   the service
 |               |-- readValue() -->|-- ATT read ---->|-- reads the
 |               |                  |                 |   battery level
 |<-- battery: 42% -----------------------------------|
```

The expensive part isn't the read — it's the *discovery*:
`getPrimaryService` and `getCharacteristic` trigger attribute
discovery over the air (the peripheral answers "what services do
you have?"). Real BLE apps cache or hardcode UUIDs precisely
because discovery round-trips are slow. Web Bluetooth does the
lookup for you each call — convenient for learning, worth knowing
for production.

## Step 4 — Exercises

- Read `device_information` characteristics — manufacturer, model
- Try `ch.startNotifications()` + `characteristicvaluechanged` —
  BLE's push model (like subscribe, vs `readValue()`'s poll)
- Compare the flow to Web Serial: `requestDevice`/`requestPort`,
  `gatt.connect()`/`port.open()` — same shape, different transport

## ✅ Checkpoint

- [ ] Phone advertises via nRF Connect
- [ ] Browser picker shows the phone, connects on selection
- [ ] `battery_level` (or another characteristic) reads a real value
- [ ] You can name the three levels: service → characteristic → value

## 🔧 Troubleshooting

| Symptom | Try |
|---|---|
| Phone not in the picker | advertising started? BLE enabled? Move phone closer — BLE is short range |
| Connects then drops | nRF Connect must stay in foreground — the OS suspends background peripherals |
| `getPrimaryService` fails | the peripheral doesn't expose that service — add it in the GATT server config |
| macOS asks for permission | grant Chrome Bluetooth permission in System Settings |

## ➡️ Next

Workshop 07 — capstone: the unified dashboard — monitor, control,
and a clean disconnect, ready for the real board.

<sub>[← Workshop list](README.md)</sub>
