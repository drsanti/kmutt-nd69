# Week 09 Self-Check

![track](https://img.shields.io/badge/track-ND03-6d28d9?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-self--check-2e8b57?style=flat-square)

[Week 09 index](README.md) · [Labs Guide](labs/README.md)

For you, not for a grade: try each question in your head or on paper, then open **Answer** to check.

**1.** On the board's screen, which corner is (0, 0), and in which direction does y grow?
<details><summary>Answer</summary>The top-left corner. x grows to the right and y grows **down**.</details>

**2.** A box 14 px high must sit on a belt whose top is at y = 150. What y do you pass to `fill_rect`?
<details><summary>Answer</summary>150 − 14 = **136**: `fill_rect` takes the top-left corner, so the box's bottom edge lands on the belt top.</details>

**3.** Your loop moves an object `x += 5` every frame. At 15 fps, what is its speed in px/s? At 5 fps?
<details><summary>Answer</summary>75 px/s at 15 fps, but only 25 px/s at 5 fps: the speed depends on the frame rate.</details>

**4.** Rewrite the update so the speed is 75 px/s at any frame rate.
<details><summary>Answer</summary>`x += 75 * dt`, where `dt` is the time since the last frame in seconds.</details>

**5.** Why does "clear the screen, then draw everything" flicker? What do you do instead?
<details><summary>Answer</summary>The screen can refresh between the clear and the redraw, so for a moment it shows the empty background. Instead, erase only the old object and draw the new one, sent in the same flush, so both land in one screen update.</details>

**6.** The board draws at most 32 operations per screen update. Why can a picture of 60 operations not appear all at once?
<details><summary>Answer</summary>It needs at least two screen updates (32 + 28), so the first part appears before the rest: you can see it build up. Keep each frame's change small.</details>

**7.** A conveyor roller has radius 8 px and the belt moves at 40 px/s. How fast does the roller turn (rad/s)?
<details><summary>Answer</summary>ω = v / r = 40 / 8 = **5 rad/s** (rolling without slipping).</details>

**8.** A 2-link arm has L1 = 70, L2 = 60. Is a target 140 px from the shoulder reachable? One 5 px away?
<details><summary>Answer</summary>Neither. The reach is from |L1 − L2| = 10 px to L1 + L2 = 130 px: 140 px is too far and 5 px is too close.</details>

**9.** Give the forward-kinematics formula for the gripper's **screen** y.
<details><summary>Answer</summary>y2 = y0 − L1·sin(q1) − L2·sin(q1 + q2): minus signs, because screen y grows down.</details>

**10.** Why does a target usually have two IK solutions, and which one did the lab choose?
<details><summary>Answer</summary>The elbow can bend either way (elbow up or elbow down): q2 = ±acos(…). The lab uses q2 = −acos(…), elbow up, so the arm stays above the conveyor.</details>

**11.** In the digital-twin cell, list the states of the arm's state machine and what makes each one end.
<details><summary>Answer</summary>RUN ends when a box reaches the end of the belt → PICK ends when the gripper reaches the box (it takes the box) → CARRY ends at the bin (it drops the box, placed + 1) → RETURN ends at the home position → RUN. A shake in any state goes to ESTOP.</details>

**12.** Why must the emergency stop be checked before the state machine, and why must reset resume the *previous* state rather than always going back to RUN?
<details><summary>Answer</summary>Checked first, a shake stops everything in the same frame, before anything else moves. Resuming the previous state lets the cell finish the job it was doing (for example the arm carrying a box) instead of skipping steps or dropping the box.</details>
