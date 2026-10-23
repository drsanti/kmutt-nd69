# Workshop 05 — Web Serial write: commands to the device

> **Goal:** close the loop — the browser sends commands, the device
> acts on them. Monitor *and* control in one app.

**Requirements:** workshop 04 done

---

## The write path

Reading was `port.readable → reader`. Writing is symmetric:

```ts
const writer = new TextEncoderStream();
void writer.readable.pipeTo(port.writable);   // text → bytes → port
const w = writer.writable.getWriter();
await w.write(command + "\n");                // one line per command
```

`lib/serial.ts` wraps this as `dev.write(text)` — the workshop just
calls it.

## The closed loop

Reading gave you half the system. This workshop closes it:

```
            ┌──────────────────────────────┐
            │           browser            │
            │  controls -> tx   rx -> UI   │
            └───────┬───────────┴──────────┘
                    │ commands  ▲ telemetry
                    ▼           │
            ┌───────┬───────────┴──────────┐
            │         fake_device.py       │
            │  parse cmd -> state -> emit  │
            └──────────────────────────────┘
```

The device is now an actor, not just a source: a command changes
its *state*, and the changed state comes back through the existing
telemetry channel. This is the canonical control loop — and the
reason commands are verifiable without a separate ack protocol.

## What w05 adds

Two control channels, both live:

```ts
// LED command — color picker → device
colorField("color", (hex) => {
  const [r, g, b] = hexToRgb(hex);
  void dev?.write(led(r, g, b));        // {"type":"led","r":..,"g":..,"b":..}
});

// rate command — slider → device
slider("rate Hz", 1, 20, 5, (v) => {
  void dev?.write(rate(v));             // {"type":"rate","hz":N}
});
```

## Step 1 — Run the loop

`w05_serial_cmd` in `main.ts`, device running, connect:

1. Pick a color → `fake_device.py` prints `led → rgb(…)`
2. Drag the rate slider → `fake_device.py` prints `rate → N Hz`
   **and the telemetry visibly speeds up** — the command changed
   device behavior, confirmed through the same wire it came in on

That last part is the real lesson: **commands are observable** —
you see the effect in the telemetry stream, not just a "sent" log.

## Step 2 — The command table

| UI action | JSON sent | Device response |
|---|---|---|
| color change | `{"type":"led","r","g","b"}` | prints `led → rgb(…)` |
| rate slider | `{"type":"rate","hz"}` | prints `rate → N`, telemetry speeds up |

A command is just a message going the other direction — same
protocol, same line-per-JSON framing. The device validates and
clamps values (bad rates get clamped to 0.1–100 Hz).

## One command, end to end

```
user           UI control       dev.write()       port          device
 |                 |                 |             |              |
 |-- pick -------->|                 |             |              |
 |   color         |-- hexToRgb() -->|             |              |
 |                 |                 |- {"led"}+\n>|              |
 |                 |                 |             |-- bytes ---->|
 |                 |                 |             |              |-- led state
 |                 |                 |             |              |  changes
 |                 |<----- telemetry (new state visible) ---------|
 |<-- gauge/log shows the effect ----|             |              |
```

Two design details in that flow:

- **Write ≠ confirmation.** `dev.write()` resolves when bytes leave
  the browser — it says nothing about the device receiving or
  applying them. The *telemetry* is the confirmation channel;
  that's why watching `rate` change the stream is the real proof.
- **The device clamps, not the UI.** Validation lives on the
  device side (0.1–100 Hz) because the wire is untrusted — any
  client can send anything. UIs constrain for convenience; devices
  constrain for correctness.

## Step 3 — Exercises

- Send an invalid command from the browser console — how does the
  device report it? (It prints `rx (unknown)` — the protocol is
  forgiving on unknown types)
- Make the LED swatch reflect the *device's* state: have
  `fake_device.py` ack the command with a telemetry field —
  the difference between "button clicked" and "device confirmed"

## ✅ Checkpoint

- [ ] Color changes print on the device terminal
- [ ] Rate changes speed up the telemetry stream
- [ ] Log shows `tx` commands and `rx` telemetry interleaved
- [ ] The gauge keeps updating while commands flow

## 🔧 Troubleshooting

| Symptom | Try |
|---|---|
| Commands don't reach the device | `dev` is null until Connect succeeds — check the status pill |
| Device ignores a command | bad JSON or wrong `type` — check the device's own log |
| Everything works but slowly | rate clamped at 0.1–100 Hz by the device — that's intentional |

## ➡️ Next

Workshop 06 — cut the cable: the same app pattern over Web Bluetooth.

<sub>[← Workshop list](README.md)</sub>
