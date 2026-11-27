# Week 09 Exercises (optional)

![track](https://img.shields.io/badge/track-ND03-6d28d9?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-exercises-2e8b57?style=flat-square)

[Labs guide](../../README.md) · [Week 09 index](../../../README.md)

This folder is **separate from the demos**. The demos in the folder above are complete, working programs. Here are the same five labs as **exercises**: in each file, three parts of the code are left out and marked `TODO 1`, `TODO 2`, `TODO 3`. Each file still runs before you change anything; it just shows less (for example only one chart line, or a bubble that does not move) until you write the missing code.

Use the same environment as the demos: activate the `.venv` in `labs/python` (see the labs guide, Setup).

```bash
cd nd3/docs/week09/labs/python/exercises
python lab9_4_robot_arm.py
```

When a script starts, it prints its tasks and what the unfinished version shows. All options work as in the demos (`--replay`, `--seconds`, `--port`, `--help`).

**Stuck?** The demo with the same file name in the folder above (`../lab9_….py`) is the complete answer. Compare it with your file.

## The tasks

### Lab 9.1 — A static cell

`lab9_1_static_cell.py`

| TODO | Task |
|---|---|
| 1 | Draw the conveyor: a belt top, a return belt and 3 rollers |
| 2 | Put 3 boxes **on** the belt (which y puts a box's bottom on the belt top?) |
| 3 | Add a stack light (red, yellow, green) and the robot arm with `d.line(x0, y0, x1, y1, color, width)` |

### Lab 9.2 — The animation loop

`lab9_2_animation_loop.py`

| TODO | Task |
|---|---|
| 1 | Move the box by `speed × dt`, not a fixed number of pixels |
| 2 | Bounce at both ends of the track |
| 3 | The starter **flickers** (it clears the track every frame). Erase only the old box and draw the new one |

### Lab 9.3 — A working conveyor

`lab9_3_conveyor.py`

| TODO | Task |
|---|---|
| 1 | Belt speed from tilt: `ax / g` (about −1…1) × `V_MAX` |
| 2 | Spawn a box every 2 s, move all boxes, remove the ones that leave the belt |
| 3 | Turn the rollers: angle += speed × dt / R, and draw a dot on each roller at that angle |

### Lab 9.4 — A robot arm

`lab9_4_robot_arm.py`

| TODO | Task |
|---|---|
| 1 | Forward kinematics: joint angles → elbow and gripper positions |
| 2 | The starter leaves a **trail** of arms. Move a `Sprite` instead: `arm.move(arm_shapes(pose))` |
| 3 | Inverse kinematics: a tapped point → joint angles (law of cosines), or `None` if it is out of reach |

### Lab 9.5 — The digital-twin cell

`lab9_5_digital_twin.py`

| TODO | Task |
|---|---|
| 1 | Emergency stop: a shake in any state → `ESTOP`; a tap (or `--auto-reset` after 3 s of calm) resumes the state it stopped |
| 2 | The arm's state machine: RUN → PICK → CARRY → RETURN → RUN |
| 3 | The stack light (green RUN, yellow arm busy, red ESTOP) and stop the belt in ESTOP |
