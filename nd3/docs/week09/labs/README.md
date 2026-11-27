# Week 09 Labs: A Living Factory Cell

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND03-6d28d9?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-labs-2e8b57?style=flat-square)

[Week 09 index](../README.md) · Lessons: [01 — Animation on a small screen](../lessons/01-animation-on-a-small-screen.md) · [02 — Robot arm kinematics](../lessons/02-robot-arm-kinematics.md)

Five labs, 25–35 minutes each. Each script in `labs/python/` runs as-is and has **three `# TODO` tasks**; complete them in order. Every lab draws on the board's screen, so **a board is needed** (ws28p or es3c28p).

| You have | Run labs with |
|---|---|
| **ws28p** (IMU + screen) | no flag — Labs 9.3 and 9.5 use the board's live motion |
| **es3c28p** (mic + screen) | `--replay` for Labs 9.3 and 9.5 — recorded motion drives them |

---

## 1. Setup (20 min)

### 1a. Python environment

Week 09 is **self-contained**: you need nothing from earlier weeks. Do this setup **before class** if you can: the first install downloads about 600 MB (TensorFlow).

**Python 3.11 is required** (the `robotos_edge` wheel is built for 3.11). Check, and install it if missing:

| | Check | Install |
|---|---|---|
| macOS | `python3.11 --version` | `brew install python@3.11` |
| Windows | `py -3.11 --version` | `winget install Python.Python.3.11` |

**Create the environment** (once):

```bash
cd nd3/docs/week09/labs/python
```

- **macOS / Linux:**
  ```bash
  python3.11 -m venv .venv
  source .venv/bin/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  py -3.11 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **Windows (Git Bash):**
  ```bash
  py -3.11 -m venv .venv
  source .venv/Scripts/activate
  ```

Your prompt now starts with `(.venv)`. Then install everything with **one line** (copy the whole line). It first downloads the libraries (numpy, TensorFlow, pyserial; a few minutes the first time), then installs the course SDK `robotos_edge` from `labs/dist`. The second part only works after the first:

```bash
pip install -r requirements.txt; pip install -U --no-index -f ../dist robotos_edge
python -c "import robotos_edge as rk; from robotos_edge import scene; print(rk.__version__)"   # 0.2.2 or newer
```

Next time, only activate it again (`source .venv/bin/activate`, or `.\.venv\Scripts\Activate.ps1` on Windows).

> **Windows:** if the second `pip install` says *No matching distribution found for robotos_edge*, the Windows wheel is not in `labs/dist` yet: run `git pull` in the course folder and try again.

### 1b. Board firmware: update to 0.3.2

Week 09 needs board firmware **0.3.2** (0.3.1 also works): it draws the robot arm's thick links on the board itself, so the arm moves without blinking. Check what your board has:

```bash
robotos detect          # look for:  Firmware: robotos-fw/0.3.2 (protocol 3)
```

If it shows an older version (or says *older firmware; update*), flash the new one — **always pass your board**:

```bash
robotos flash-firmware --board ws28p        # or: --board es3c28p
```

It downloads the newest firmware, flashes it (about 1 minute), and checks the board. Run `robotos detect` again and confirm `robotos-fw/0.3.2`.

> All Week 09 labs use one screen page called **CELL**, so you can run them in any order and stop them with Ctrl+C at any time.

---

## Lab 9.1 — A static cell (30 min)

**Script:** `lab9_1_static_cell.py` · **Lesson:** [01 — Animation on a small screen](../lessons/01-animation-on-a-small-screen.md)

```bash
python lab9_1_static_cell.py
```

A **CELL** tab appears on the board's screen. Your drawing area is x 0–319, **y 46–221** (the tabs are above it). y grows **down**.

| TODO | Task |
|---|---|
| 1 | Draw the conveyor: a belt top, a return belt and 3 rollers |
| 2 | Put 3 boxes **on** the belt (which y puts a box's bottom on the belt top?) |
| 3 | Add a stack light (red, yellow, green) and the robot arm with `d.line(x0, y0, x1, y1, color, width)` |

**Observe:** the script prints how many drawing operations the picture needed. The board draws at most **32 operations per screen update** — keep that number in mind for animation.

**Answer in your notes:** (1) A box is 14 px high and the belt top is at y = 172. What is the box's y, and why? (2) Link 1 points at 120°. Why is its end *above* the shoulder on screen even though sin 120° is positive?

---

## Lab 9.2 — The animation loop (25 min)

**Script:** `lab9_2_animation_loop.py`

```bash
python lab9_2_animation_loop.py
python lab9_2_animation_loop.py --fps 5      # fewer frames: is the box slower?
```

| TODO | Task |
|---|---|
| 1 | Move the box by `speed × dt`, not a fixed number of pixels |
| 2 | Bounce at both ends of the track |
| 3 | The starter **flickers** (it clears the track every frame). Erase only the old box and draw the new one |

**Observe:** after TODO 1, the box crosses the track in the same time at 15 fps and at 5 fps — only smoother at 15. After TODO 3, the flicker is gone and the link sends far fewer commands (printed at the end).

**Answer in your notes:** (1) Why does `x += 4` per frame make the speed depend on the computer? (2) Why does clearing and redrawing flicker, while erase-old + draw-new does not?

---

## Lab 9.3 — A working conveyor (30 min)

**Script:** `lab9_3_conveyor.py`

```bash
python lab9_3_conveyor.py            # ws28p: tilt it left / right
python lab9_3_conveyor.py --replay   # es3c28p: recorded motion
```

| TODO | Task |
|---|---|
| 1 | Belt speed from tilt: `ax / g` (about −1…1) × `V_MAX` |
| 2 | Spawn a box every 2 s, move all boxes, remove the ones that leave the belt |
| 3 | Turn the rollers: angle += speed × dt / R, and draw a dot on each roller at that angle |

**Observe:** tilt the ws28p: the belt runs forward, stops when level, and runs backward the other way. The roller dots should turn exactly as fast as the belt moves (rolling without slipping).

**Answer in your notes:** (1) Where does a tilted board's `ax` come from, if the board is not moving? (2) A real conveyor has a speed limit and a ramp. Where would you add a ramp (a maximum change of speed per second)?

---

## Lab 9.4 — A robot arm (30 min)

**Script:** `lab9_4_robot_arm.py` · **Lesson:** [02 — Robot arm kinematics](../lessons/02-robot-arm-kinematics.md)

```bash
python lab9_4_robot_arm.py           # tap a point on the screen; the arm reaches for it
```

| TODO | Task |
|---|---|
| 1 | Forward kinematics: joint angles → elbow and gripper positions |
| 2 | The starter leaves a **trail** of arms. Move a `Sprite` instead: `arm.move(arm_shapes(pose))` |
| 3 | Inverse kinematics: a tapped point → joint angles (law of cosines), or `None` if it is out of reach |

**Observe:** without taps the arm visits four preset targets. Tap far away from the base: the screen says *out of reach!*. The two joints turn at a limited speed, so the arm moves smoothly, like a real one.

**Answer in your notes:** (1) What is the largest distance from the shoulder the gripper can reach, and the smallest? (2) Most targets have **two** arm poses (elbow up and elbow down). Which sign of q2 gives elbow up here?

---

## Lab 9.5 — The digital-twin cell (35 min)

**Script:** `lab9_5_digital_twin.py`

```bash
python lab9_5_digital_twin.py                         # ws28p: shake it hard = EMERGENCY STOP, tap = reset
python lab9_5_digital_twin.py --replay --auto-reset   # es3c28p: recorded motion, resets by itself
```

Boxes ride the conveyor; the arm picks each one at the end of the belt and drops it in the bin; the stack light shows the state.

| TODO | Task |
|---|---|
| 1 | Emergency stop: a shake in any state → `ESTOP`; a tap (or `--auto-reset` after 3 s of calm) resumes the state it stopped |
| 2 | The arm's state machine: RUN → PICK → CARRY → RETURN → RUN |
| 3 | The stack light (green RUN, yellow arm busy, red ESTOP) and stop the belt in ESTOP |

**Observe:** shake the ws28p while the arm carries a box: everything freezes, the light turns red, and after a tap the arm carries on from where it stopped. Count the placed boxes.

**Answer in your notes:** (1) Why does the e-stop check come **before** the state machine in the loop? (2) The shake test needs a large acceleration **and** a fast rotation. Which normal motion would trigger a false e-stop if it used acceleration alone?

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No matching distribution found for numpy>=1.26` (or tensorflow) when installing `robotos_edge` | The libraries were not installed first. Run the whole line from Setup: `pip install -r requirements.txt; pip install -U --no-index -f ../dist robotos_edge` |
| `ModuleNotFoundError: robotos_edge` | Activate the `.venv` in `labs/python` first (Setup 1a) |
| `ImportError: … 'scene'` / `AttributeError: … 'Sprite'` | Old wheel: run the `pip install -U …` line in Setup 1a |
| The robot arm **blinks** while it moves | Board firmware older than 0.3.1: Setup 1b |
| `could not create page … (rc=-12)` | The screen's page slots are full (old pages from other weeks): press RESET on the board |
| `no IMU samples …` | Not a ws28p: use `--replay` |
| The screen shows `?` instead of a symbol | The board's font has plain ASCII only. `d.text()` converts common symbols (`° → deg`, `² → 2`, `— → -`); avoid others (including Thai) in screen text |
| Nothing appears on the screen | Tap the **CELL** tab at the top of the screen |
| The board restarts again and again | Unplug it, close every other program that uses the port (Serial Monitor, another lab), plug it back in |
