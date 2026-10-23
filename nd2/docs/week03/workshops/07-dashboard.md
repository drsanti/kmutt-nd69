# Workshop 07 — Capstone: the device dashboard

> **Goal:** put it all together — the complete monitor + control
> app with a real connect/disconnect lifecycle. This is the shape
> next week's real board app takes.

**Requirements:** workshops 03–05 done

---

## What w07 completes

Everything from w05 plus the lifecycle the earlier workshops skipped:

```ts
const connectBtn = button("Connect", async () => {
  dev = await connect();
  st.set(true);
  connectBtn.disabled = true;          // one connection at a time
  dev.onLine(/* telemetry → gauge + log */);
});

const disconnectBtn = button("Disconnect", async () => {
  await dev?.close();                  // release the port cleanly
  dev = null;
  st.set(false);
  connectBtn.disabled = false;
});
```

The full state machine in miniature — the port is an exclusive
resource, so every state has rules about which buttons are legal:

```
                     Connect clicked
               ┌─────────────────────────┐
               ▼                         │
   ┌──────────────┐    picker ok   ┌───────────────┐
   │ disconnected │ ─────────────► │  connecting   │
   │ (Connect on) │                │ (buttons off) │
   └──────┬───────┘                └──────┬────────┘
          ▲                               │ open() ok
          │                               ▼
          │                        ┌───────────────┐
          │                        │  connected    │
          │                        │ (Disconnect   │
          │                        │  on, tx+rx    │
          │                        │  flowing)     │
          │                        └──────┬────────┘
          │ close() done    Disconnect    │
          └───────────────────────────────┘
```

Each transition maps to exactly one `await`: `connect()` awaits
the picker + `open()`, `close()` awaits the port release. The
button states exist because a port is *exclusive* — two opens on
the same port is an OS-level error, so the UI makes it impossible
rather than catching the failure.

## The complete app anatomy

```
┌───────────────────────────────────────────────┐
│  status pill — shows link state at a glance   │
├──────────────┬───────────────┬────────────────┤
│ connection   │ led color     │ telemetry      │
│ connect/dis  │ color picker  │ gauge + rate   │
├──────────────┴───────────────┴────────────────┤
│  log — tx commands + rx telemetry + sys       │
└───────────────────────────────────────────────┘
```

- **status** — user can see the link state at a glance
- **controls** — LED color, telemetry rate → `dev.write()`
- **telemetry** — live gauge from parsed messages
- **log** — the wire made visible: both directions, timestamped
- **lifecycle** — Connect disabled while connected; Disconnect
  releases the port so another app (or a re-run) can use it

## Step 1 — Run the full flow

`w07_dashboard` in `main.ts`, fake device on the pair:

Connect → drag rate to 10 Hz → pick a color → watch the log
interleave `tx` commands with `rx` telemetry → Disconnect →
Connect again (the port released cleanly).

The full lifecycle, end to end:

```
user            app             port            device          UI
 |               |               |               |               |
 |-- Connect --->|-- open() ---->|               |               |
 |               |<-- handle ----|               |-- status=on ->|
 |               |               |<-- telemetry -|               |
 |               |<--- lines ----|               |-- gauge, rx ->|
 |-- color ----->|-- led cmd --->|-------------->|-- tx logged ->|
 |               |               |               |-- led prints  |
 |-- Disconnect->|-- close() --->|               |               |
 |               |<-- released --|               |-- status=off->|
 |-- Connect --->|-- open() ---->| (works — port was released)   |
```

## Step 2 — What the real board changes (nothing)

Next week the same app connects to the ESP32 board — because
`fake_device.py` and the board speak the same JSON-lines protocol:

| This week | Next week |
|---|---|
| `fake_device.py` on a virtual pair (socat/com0com) | real board on `/dev/cu.usb*` (mac) / `COM*` (Win) / `/dev/ttyUSB*` (Linux) |
| simulated `level` waveform | real sensor data |
| `led → rgb()` printed in terminal | real WS2812 LED lights up |
| `{"type":"led"...}` JSON | same JSON |

The app — `lib/serial.ts`, `protocol.ts`, the UI — doesn't change.
**That's the payoff of teaching the protocol, not the hardware.**

## Step 3 — Exercises

- Add a "Reconnect on drop" — `port` emits `disconnect` events
- Buffer a second panel showing `seq` gaps — real links drop packets
- Swap the LED JSON for your own command type (e.g. `{"type":"buzz"}`)
  and extend `fake_device.py` to honor it — you're extending the protocol

## ✅ Checkpoint

- [ ] Connect/disconnect cycles work repeatedly
- [ ] Telemetry gauge tracks live data
- [ ] Both commands change device behavior
- [ ] Log shows the bidirectional wire clearly
- [ ] You can explain what changes when the real board arrives (nothing)

## 🎓 Where you are

You've built a real hardware app from a browser — connect, monitor,
control, lifecycle, protocol. Next week the same skills land on the
physical board: the serial port becomes USB to silicon, the
telemetry becomes real sensor data, and the LED commands light a
real LED.

<sub>[← Workshop list](README.md)</sub>
