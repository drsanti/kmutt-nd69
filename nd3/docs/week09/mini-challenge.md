# Week 09 Mini Challenge — Extend the Digital Twin

![track](https://img.shields.io/badge/track-ND03-6d28d9?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-challenge-2e8b57?style=flat-square)

[Week 09 index](README.md) · [Labs Guide](labs/README.md)

> **Optional.** Try it during the session or afterwards, at your own pace. Nothing is handed in or scored; it is a way to practise what the labs showed.

Start from the demo `lab9_5_digital_twin.py` (copy it as `my_cell.py`, so the demo stays as it is). Pick any of the tasks below, one or several.

| # | Task | Hint |
|---|---|---|
| 1 | **Box sorting.** Give each box a colour (two kinds). The arm drops each kind in its own bin. | Add a second bin and a second PLACE point; choose the point from the box's colour in CARRY. |
| 2 | **Straight-line move.** Make the gripper move from PICK to PLACE along a straight line instead of a curve. | Each frame, move the *target point* a few px along the line, then call `arm.ik()` on it. |
| 3 | **A production counter HMI.** Show boxes per minute and the time spent in each state (RUN / busy / ESTOP). | Add up `dt` per state; draw with `d.text` only when the numbers change. |
| 4 | **Belt jam fault.** If a box waits at the end of the belt for more than 5 s (the arm is too slow), go to a `FAULT` state with a flashing yellow light. | A flashing light = toggle every 0.5 s using `time.monotonic()`. |
| 5 | **Touch HMI buttons.** Draw START and STOP buttons on the screen; tapping them starts and stops the cell. | Check whether the tap's (x, y) lies inside the button's rectangle. |

**Check your result:** trigger an emergency stop in the middle of each state (RUN, PICK, CARRY, RETURN, and any state you added). Does the cell stop safely, and carry on correctly after the reset? Want to share it? A short phone video of the board's screen shows each feature well.
