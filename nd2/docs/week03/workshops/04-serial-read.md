# Workshop 04 — Web Serial read: live telemetry

> **Goal:** turn raw serial lines into a live gauge — the read path
> of a monitor app, from `requestPort` to decoded messages.

**Requirements:** workshop 03 running (fake device + port pair)

---

## The read path

`w04_serial_read.ts` does three things the raw console didn't:

```ts
const dev = await connect();              // requestPort + open + streams
dev.onLine((line) => {                    // decoded text, line-by-line
  const t = parseTelemetry(line);         // JSON → Telemetry | null
  if (t) g.set(t.level);                  // update the gauge
});
```

The read side is a pipeline — each stage transforms the data once
and hands it to the next:

```
┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌───────────┐    ┌───────┐
│ device   │    │ serial port  │    │ line     │    │ protocol  │    │ gauge │
│ emits    │───►│ byte stream  │───►│ splitter │───►│ parser    │───►│ + log │
│ JSON     │    │ (Uint8Array) │    │ (on \n)  │    │ (JSON)    │    │       │
└──────────┘    └──────────────┘    └──────────┘    └───────────┘    └───────┘
                 transport layer      framing layer    meaning layer   UI layer
```

Each layer has exactly one job:

- **transport** — moves bytes, knows nothing about content
- **framing** — turns a byte stream into discrete messages
  (here: split on `\n`; real protocols use length prefixes or
  frame markers like COBS)
- **meaning** — parses JSON, validates `type`, drops noise
- **UI** — renders, never touches the wire

When a system misbehaves, ask *which layer* is wrong: no bytes =
transport; bytes but no lines = framing; lines but `null` =
meaning; parsed values but frozen UI = UI. Debugging by layer is
the single most useful habit for any comms work.

## What's inside `lib/serial.ts`

The `connect()` helper is where the real Web Serial API lives —
worth reading once:

```ts
const port = await navigator.serial.requestPort();  // user picks the port
await port.open({ baudRate: 115200 });              // match the device

const decoder = new TextDecoderStream();            // bytes → text
void port.readable.pipeTo(decoder.writable);        // pipe serial through it
const reader = decoder.readable.getReader();        // then read lines
```

Key concepts:

- **`requestPort()` shows the OS device picker** — the user must
  choose (no silent access; that's the security model)
- **serial delivers *bytes*, not messages** — the helper buffers
  text and splits on `\n`, giving you clean lines
- **`baudRate` must match the device** — `fake_device.py` uses
  115200, the standard for this class of hardware

## Step 1 — Run it

Fake device on one end (w03), `w04_serial_read` in `main.ts`,
Connect → pick the port. The gauge starts tracking `level` and the
log shows each decoded line.

## Step 2 — Read the protocol layer

`lib/protocol.ts` defines the wire contract — the *same file* both
sides share conceptually (the Python device emits the same shape):

```ts
export interface Telemetry {
  type: "telemetry";
  seq: number;        // message counter — drops become visible
  level: number;      // 0..1
  ts_ms: number;      // device timestamp
}
```

`parseTelemetry()` returns `null` for non-matching lines — that's
deliberate: real devices emit noise too, and the parser is the
boundary that decides what's a message.

## Why `pipeTo` — streams, not callbacks

`port.readable` is a **ReadableStream** — the browser's back-
pressure-aware abstraction for "data that arrives over time".
Piping it through `TextDecoderStream` means: the OS can deliver
bytes whenever it likes, decode happens incrementally, and your
reader only wakes when there's a chunk to process. Nothing polls;
nothing spins. `seq` exists precisely because this stream is
unreliable in the real world — a dropped line shows up as a gap
in the counter, which is how you'd detect packet loss on a real
board.

```
device          kernel buffer      decoder stream     your reader      gauge
 |                  |                  |                 |              |
 |-- line 1 ------->|                  |                 |              |
 |                  |-- bytes -------->|                 |              |
 |                  |                  |-- "...\n" ----->|              |
 |                  |                  |                 |-- parse ---->|
 |-- line 2 ------->|                  |                 |   set()      |
 |                  |-- bytes -------->|-- "...\n" ----->|-- parse ---->|
 |                  |                  |                 |              |
 |     (half line)->|                  |- "...{" no \n ->|   buffered   |
 |                  |                  |                 |  (waits for  |
 |   (rest + \n) -->|                  |-- "...}\n" ---->|   the rest)  |
```

## ✅ Checkpoint

- [ ] Gauge tracks `level` continuously — not just on click
- [ ] Log shows decoded `rx` lines at the device's telemetry rate
- [ ] You can point at each of the four layers in `lib/serial.ts`
- [ ] A half-line arriving split across chunks still parses correctly

## 🔧 Troubleshooting

| Symptom | Try |
|---|---|
| Connected but zero lines | which layer? No bytes = transport — check the port pair; bytes but no lines = framing — check `\n` in the device's output |
| Lines appear but gauge frozen | parser returning `null` — check the JSON `type` field matches `"telemetry"` |
| `requestPort` throws immediately | Web Serial missing — Chrome/Edge on `localhost` required |

## ➡️ Next

Workshop 05 — close the loop: send commands back down the wire.

<sub>[← Workshop list](README.md)</sub>
