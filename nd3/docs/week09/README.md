# ND03 — Week 09: A Living Factory Cell — Drawing and Animating Automation on a Device

> **Before the practical:** do the [Setup](labs/README.md#1-setup-20-min) (Python 3.11 environment and board firmware, about 20 minutes). Week 09 is self-contained: it needs nothing from earlier weeks.

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND03-6d28d9?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-index-2e8b57?style=flat-square)

**Session:** Saturday 28 November 2026 · Online · 09:00–12:00  
**Topic:** *Draw factory equipment from code and bring it to life: animation loops, a conveyor, a robot arm with kinematics, and a digital-twin cell with a state machine*  
**Board:** ws28p (IMU + touchscreen) or es3c28p (touchscreen). The two labs that use motion also run with recorded motion (`--replay`).

An HMI, a SCADA mimic and a digital twin all do the same thing: they **draw the machine** and **move the drawing when the machine moves**. This week you build one from scratch on the board's 320 × 240 touchscreen, drawn from Python over USB: first a still picture of a cell, then smooth motion, a conveyor driven by the board's tilt, a 2-link robot arm that reaches where you tap, and finally a whole cell — conveyor, arm, stack light and emergency stop — run by a state machine.

---

## Table of Contents

- [Labs Guide](labs/README.md)
- Lessons: [01 — Animation on a small screen](lessons/01-animation-on-a-small-screen.md) · [02 — Robot arm kinematics](lessons/02-robot-arm-kinematics.md)
- [Self-Check](checkpoint.md) (with answers)
- [Mini Challenge](mini-challenge.md)
- Previous week: [Week 08](../week08/labs/README.md) · [Track Index](../README.md)

---

## Learning Outcomes

- **Draw with screen coordinates:** pixels, x right / y down, RGB565 colour, and building equipment from rectangles, circles and thick lines.
- **Write an animation loop:** measure `dt`, move things at a speed in px/s that does not depend on the frame rate, and redraw only what changed (no flicker).
- **Connect a sensor to motion:** drive a conveyor from the board's tilt, with rollers that turn at the right rate.
- **Use robot kinematics:** forward kinematics (joint angles → gripper position) and inverse kinematics (tap a point → joint angles) of a 2-link arm.
- **Run a cell with a state machine:** RUN → PICK → CARRY → RETURN, a stack light that shows the state, and an emergency stop that overrides everything.

---

## Schedule (09:00–12:00)

| Time | Block | Topic | Lab |
| :--- | :--- | :--- | :--- |
| **09:00–09:20** | Setup | Python environment and board firmware | [Setup](labs/README.md#1-setup-20-min) |
| **09:20–09:50** | Block 1 | Shapes and coordinates: a still factory cell | [Lab 9.1](labs/README.md#lab-91--a-static-cell-30-min) |
| **09:50–10:15** | Block 2 | The animation loop | [Lab 9.2](labs/README.md#lab-92--the-animation-loop-25-min) |
| **10:15–10:25** | Break | | |
| **10:25–10:55** | Block 3 | A conveyor driven by tilt | [Lab 9.3](labs/README.md#lab-93--a-working-conveyor-30-min) |
| **10:55–11:25** | Block 4 | A robot arm: forward and inverse kinematics | [Lab 9.4](labs/README.md#lab-94--a-robot-arm-30-min) |
| **11:25–12:00** | Block 5 | The digital-twin cell and its state machine | [Lab 9.5](labs/README.md#lab-95--the-digital-twin-cell-35-min) |

---

## How the labs work

Each lab is one short, **complete and working** Python script in `labs/python/`. Run it and the factory cell comes alive on the board's screen. When it starts, it prints what it does, what to do now and what to look for. In the code, comments `# Step 1`, `# Step 2`, `# Step 3` mark the key parts, which the [labs guide](labs/README.md) explains.

**Exercises (optional, separate):** the same labs with parts of the code left for you to write are in [`labs/python/exercises/`](labs/python/exercises/README.md). They do not change the demos.

```bash
cd nd3/docs/week09/labs/python
python lab9_1_static_cell.py          # draws on the board's screen (any board)
python lab9_3_conveyor.py --replay    # no ws28p: recorded motion drives the belt
```
