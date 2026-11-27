# Lesson 02 — Drawing on a device: pixels, budgets and flicker

![track](https://img.shields.io/badge/track-ND02-1d4ed8?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-lesson-2e8b57?style=flat-square)

[Week 09 index](../README.md) · [Labs](../labs/README.md) · Previous: [01 — Time and frequency](01-time-and-frequency.md)

## 1. The screen and its pages

Both workshop boards have a **320 × 240** touchscreen (x to the right, y **down**, (0, 0) top-left). The workshop firmware lets the PC add its own **page** (a tab) and draw on it over USB — no firmware changes:

```ts
import * as rk from "robotos-board";

const d = await rk.Display.open({ name: "METER" });  // connect, add the METER tab, show it
d.clear().text(10, 56, "hello", rk.Color.WHITE);
d.fillRect(10, 110, 120, 30, rk.Color.GREEN);
await d.flush();                                     // nothing is sent before flush()
```

| Area | y range | Owner |
|---|---|---|
| Title bar and tabs | 0–45 | firmware (clock, link status, tabs) |
| **Body** — your drawing area | **46–221** | you (`rk.BODY`) |
| Footer | 222–239 | firmware |

Text uses an 8 × 16 pixel font. The board holds **3 pages** of your own; re-opening a page with the same name reuses it.

## 2. Colours: RGB565

The panel stores each pixel in **16 bits**: 5 bits red, 6 green, 5 blue.

```ts
rk.rgb565(255, 220, 0);   // yellow -> 0xFEE0
```

A full screen is 320 × 240 × 2 = **153,600 bytes**. Displays also have **gamma**: on this panel the darkest colours look brighter than on a monitor, so choose colour maps by looking at the real screen.

## 3. The drawing budget

Drawing goes over USB as small **operations** (rectangle, line, circle, text, bitmap). The board applies up to **32 operations per screen update**, and each message carries about 1 KB. `flush()` splits and paces your operations for you, but every operation still costs time:

| Approach | Data per update | Updates per second (measured) |
|---|---|---|
| Waveform as a bitmap, 16 columns | ~3.5 KB, 7 messages | **0.5** (fell behind) |
| Same waveform as 16 vertical lines | ~0.3 KB, 1 message | **~10** |

`await d.flush()` resolves when the board has acknowledged every message, so a loop that awaits it can never run ahead of the screen.

**Rule:** draw shapes, not pixels, and send only what changed.

## 4. Flicker and dirty rectangles

If every frame first clears an area and then redraws it, the screen can refresh **between** the two — you see a blink. The fix used by every small display:

1. Remember what is on the screen (bar width, bubble position…).
2. Each frame, compare with the new value and draw **only the difference**: paint the part of a bar that grew, erase the part that shrank, erase the old bubble and draw the new one.
3. Never clear something you are about to redraw.

```ts
if (width > shown) d.fillRect(x + shown, y, width - shown, h, color);          // grew
else if (width < shown) d.fillRect(x + width, y, shown - width, h, BLACK);     // shrank
shown = width;
```

`Display.bars()` and `StripChart` do this internally. Labs 9.3 and 9.4 show it in a few lines (Step 3 in each).

## 5. Showing a decision

A model outputs probabilities; a **threshold** turns them into decisions. Draw the probabilities, the threshold line, and highlight a class only when it crosses the line — then a person can see *why* the device acted, and tune the threshold by touch.

## Check yourself

1. How many bytes does a 100 × 50 RGB565 image need? How many 512-byte bitmap strips?
2. A bar shrinks from 200 to 150 px. What is the smallest drawing operation that updates it?
3. Why does the firmware drop drawing for a page that is not in front, and how does a script repaint when the user comes back (`d.onShown`)?
