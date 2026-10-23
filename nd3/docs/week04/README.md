# ND03 — Week 04: The Real Board (draft)

> Boards are distributed this week — the first hands-on session
> where nodes, topics, and params meet real silicon.

> [!NOTE]
> **Draft outline for instructors** — expand into per-workshop
> files before the week runs. Content stays concept-level per the
> project style guide: board capabilities are product surface;
> describe what the system *does*, never how the wire works.

## Who this is for

Automation people — PLC, DCS, SCADA backgrounds. Every exercise
maps a familiar industrial concept onto a robotos/ROS concept:

| You already know | This week's robotos name |
|---|---|
| PLC cyclic scan reading inputs | a node's publisher loop |
| Fieldbus tags | topics with schemas |
| Watchdog / station-alive | presence tokens |
| Retain memory / NVM setpoints | persisted parameters |
| Historian / data logging | record + replay |
| HMI | inspector + your own app |

## Workshop outline (proposed)

| # | Workshop | Board feature | Automation lesson |
|---|---|---|---|
| 01 | First contact — find the node | board joins the graph | "my station is alive" = presence |
| 02 | Read the process variables | battery, IMU, mic level streams | fieldbus → topics |
| 03 | Command an actuator | LED, sound effects | setpoint writes + acks |
| 04 | Parameters that outlive a reboot | display backlight, volume | retained setpoints in NVM |
| 05 | Discrete inputs as events | button presses (short/long) | interrupt I/O, not polling |
| 06 | Log the run | record the board's topics | historian pattern on real data |
| 07 | Mini digital twin II | replay + live board side-by-side | virtual commissioning |

## Teaching moments hiding in the hardware

- **Two board variants in the room** — one has an IMU, the other
  has a mic + LED. The discovery exercise (which topics exist on
  *your* board) is the "capability-driven integration" lesson —
  integrators don't hardcode the BOM.
- **Buttons classify themselves** — the device detects
  press/release/short/long before the event ever reaches the
  network; edge classification vs host-side processing is a real
  architecture decision worth naming.
- **A param set can outlive a power cycle** — set a value,
  physically unplug, power back, read it — the retained-memory
  story proves itself without a diagram.
- **Presence is the watchdog** — kill the board's power, watch
  the liveliness drop in the inspector; students who run watchdog
  bits in PLCs recognize it instantly.
- **Mute is not silence** — a muted mic reports near-zero levels;
  teaching "state flag vs telemetry value" is a real SCADA gotcha.

## Prerequisites

| Item | Why |
|---|---|
| Board (either variant) + USB cable | the real node |
| Everything from week 03 | same CLI + Python SDK |
| Serial monitor / terminal | watch the device talk |

<sub>[← Documents](../README.md)</sub>
