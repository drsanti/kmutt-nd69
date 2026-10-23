# ND02 — Week 04: The Real Board (draft)

> The simulation ends — your app meets actual hardware.
> Boards are distributed this week. Everything you built in
> week 03 still applies; only the device is real.

> [!NOTE]
> **Draft outline for instructors** — flesh out into per-workshop
> files before the week runs. Keep content concept-level per the
> project style guide: describe board capabilities as product
> surface, never the wire internals.

## What's new this week

| Change | Consequence |
|---|---|
| Real board instead of `fake_device.py` | real timing, real framing, real failure modes |
| Two board variants in the room | apps must detect capabilities, not assume them |
| Physical buttons, touch, mic, speaker, backlight | richer telemetry + more things to control |
| Persisted settings on the device | commands can outlive a reboot — or not |

## Workshop outline (proposed)

| # | Workshop | Board feature exercised |
|---|---|---|
| 01 | First connect — identify your board | board identity + capability report; which variant do you have? |
| 02 | Telemetry is real now | battery level, IMU (if present), mic level |
| 03 | Commands that do something | LED color, sound effects, display |
| 04 | Persisted params | backlight level, volume — set once, survives reboot |
| 05 | Input events | button presses stream as events (press, release, short, long) |
| 06 | The level meter | mirror the on-device VU meter in the app |
| 07 | Capstone — board-aware dashboard | detect capabilities, show only what exists |

## Good teaching moments hiding in the hardware

- **Two boards, one app** — variants differ in peripherals
  (IMU vs mic, LED vs speaker amp). Capability-driven UI is the
  lesson: query what's there, don't hardcode a model name.
- **Buttons are events, not polls** — the board classifies
  press/release/short/long itself; the app just subscribes.
- **Settings can persist** — changing backlight or volume keeps
  the value across a power cycle; make the exercise *prove* it
  (set → power off → reboot → read back).
- **The mute button is a trap** — the device-side mute and the
  app-side "not streaming" look alike in the UI; teaching the
  difference (state vs telemetry) is a nice debugging story.
- **The meter is logarithmic** — a loud tap lights a red segment
  at the far right; the students' linear app-side meters from
  week 03 need rescaling. Perceptual scales are a real UI topic.

## Prerequisites

| Item | Why |
|---|---|
| Board (either variant) + USB cable | the real device |
| Chrome or Edge | Web Serial / Web Bluetooth |
| Everything from week 03 | the app keeps working |
| nRF Connect (phone) | the board also speaks BLE |

<sub>[← Documents](../README.md)</sub>
