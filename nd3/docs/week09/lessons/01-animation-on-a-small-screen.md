# Lesson 01 — Animation on a Small Screen

![track](https://img.shields.io/badge/track-ND03-6d28d9?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-lesson-2e8b57?style=flat-square)

[Week 09 index](../README.md) · [Labs Guide](../labs/README.md) · Next: [02 — Robot arm kinematics](02-robot-arm-kinematics.md)

## 1. The screen is a grid of pixels

The board's screen is **320 × 240** pixels. Position (0, 0) is the **top-left** corner; **x grows to the right, y grows down**. The top strip (tabs) and the bottom strip belong to the board, so your page draws in **y 46–221**.

```
(0,0) ───────────── x ──────────▶ (319,0)
  │   [ HOST ] [ CELL ]           ← tabs (board)
  │ (0,46) ┌──────────────────┐
  y        │   your drawing   │
  │        └──────────────────┘ (319,221)
  ▼
```

Because y grows down, a point that is *higher* on the screen has a *smaller* y. In maths, angles are measured with y up; on the screen we therefore **subtract** the sine: `y = y0 − L·sin θ`.

Colours are **RGB565**: 5 bits red, 6 bits green, 5 bits blue in 16 bits. `rk.rgb565(210, 150, 60)` converts normal 0–255 values; `rk.Color.RED` etc. are ready-made.

## 2. You send drawing operations, not pixels

Python does not send pictures. It sends small **operations** — fill a rectangle, draw a circle, draw a thick line, write text — and the board's firmware draws them:

| Call | Operation |
|---|---|
| `d.fill_rect(x, y, w, h, color)` | solid rectangle |
| `d.circle(cx, cy, r, color)` | filled circle |
| `d.line(x0, y0, x1, y1, color, width)` | thick line with round ends (firmware 0.3.1) |
| `d.text(x, y, "msg", color)` | 8 × 16 px characters, background painted black |
| `d.flush()` | send everything queued since the last flush |

A full-screen image would be 320 × 240 × 2 = **153 600 bytes**; a box move is two operations of about 20 bytes. That is why devices like this (and many HMIs) draw with operations.

The board applies at most **32 operations per screen update** (about every 30 ms). The SDK paces bigger batches for you, but a picture that needs more than 32 operations is drawn over several updates — you can see it build up.

## 3. The animation loop

Every animation, in games, HMIs and digital twins, is the same loop:

```python
clock = Clock(15)                      # aim for 15 frames per second
while running:
    dt = clock.tick()                  # 1. how much time passed (s)
    x = x + speed * dt                 # 2. update the model (physics, logic)
    draw only what changed             # 3. update the picture
    d.flush()                          # 4. send it
```

**Use `dt`.** If you move `x += 4` each frame, the speed is 4 px × fps: 60 px/s at 15 fps but 20 px/s at 5 fps, and it changes whenever the computer is busy. With `x += speed * dt`, the speed is always `speed` px/s; a slower frame rate only makes the motion less smooth.

## 4. Why clearing flickers — and the fix

The simple way — clear everything, then draw everything — shows the **empty** screen for a moment every frame. That is flicker.

Instead, draw only the **change**:

1. erase the old object (paint the background colour over it),
2. draw the object in its new place,
3. send both in **one** flush, so they land in the same screen update.

This is called **dirty-rectangle** drawing: only the parts of the screen that changed are touched. For an object made of many shapes (the robot arm), `rk.Sprite` does it for you: `sprite.move(new_shapes)` erases only the pixels the old pose no longer covers and draws the new pose, in one update.

## Check yourself

1. A box is 18 × 14 px. To put it on a belt whose top edge is at y = 172, what y do you give `fill_rect`?
2. A loop runs at 15 fps with `speed = 60` px/s. How many pixels does the box move per frame?
3. Why must the erase and the draw go in the same `flush()`?
