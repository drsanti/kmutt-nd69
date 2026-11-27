# Lesson 02 — Robot Arm Kinematics

![track](https://img.shields.io/badge/track-ND03-6d28d9?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-lesson-2e8b57?style=flat-square)

[Week 09 index](../README.md) · [Labs Guide](../labs/README.md) · Previous: [01 — Animation on a small screen](01-animation-on-a-small-screen.md)

A planar arm with two rotating joints (shoulder, elbow) — the same geometry as a SCARA robot seen from above.

```
                      ● gripper (x2, y2)
                     /
                L2  /  q2 (relative to link 1)
                   /
     elbow (x1,y1)●
                 /
            L1  /  q1 (from the +x axis)
               /
  shoulder  ■────────▶ +x
```

## 1. Forward kinematics: angles → position

Given the joint angles, where is the gripper? Add the two links as vectors (maths convention, y **up**):

- elbow: `x1 = x0 + L1 cos q1`, `y1 = y0 + L1 sin q1`
- gripper: `x2 = x1 + L2 cos(q1 + q2)`, `y2 = y1 + L2 sin(q1 + q2)`

On the screen, y grows **down**, so use `y0 − L1 sin q1` and `y1 − L2 sin(q1 + q2)`. Note that the second link's angle is `q1 + q2`: q2 is measured *relative to link 1*, like a real elbow encoder.

Forward kinematics always has exactly one answer.

## 2. Inverse kinematics: position → angles

Given a target point, which angles put the gripper there? Let `dx = x − x0`, `dy = y0 − y` (flip y back to "up") and `r² = dx² + dy²`.

The shoulder, elbow and target form a triangle with sides L1, L2 and r. The **law of cosines** gives the elbow angle:

```
cos q2 = (r² − L1² − L2²) / (2 · L1 · L2)
```

- If `|cos q2| > 1`, the target is **out of reach** (too far: r > L1 + L2, or too close: r < |L1 − L2|).
- Otherwise there are **two** solutions, `q2 = +acos(…)` and `q2 = −acos(…)`: elbow down and elbow up. The lab uses `−acos` (elbow up) so the arm stays above the conveyor.

Then the shoulder angle is the direction to the target minus the angle the second link adds:

```
q1 = atan2(dy, dx) − atan2(L2 sin q2, L1 + L2 cos q2)
```

## 3. Moving like a real robot

A real joint cannot jump to a new angle; its motor has a maximum speed. Each frame, turn each joint toward its target by at most `TURN · dt`:

```python
err = atan2(sin(target − q), cos(target − q))   # shortest way round, in −π…π
q += clamp(err, −TURN·dt, +TURN·dt)
```

Both joints move at the same time, so the gripper follows a curve, not a straight line — that is **joint-space** motion. Making the gripper move in a straight line (Cartesian motion) needs IK every frame; try it in the mini challenge.

## 4. In the digital twin

`robotos_edge.scene.Arm` packages the same maths (`fk`, `ik`, `move_toward`) with drawing. Lab 9.5 uses it so you can focus on the cell's **state machine**: the twin's arm is driven by states (PICK, CARRY, RETURN), exactly like the PLC program of a real pick-and-place cell.

## Check yourself

1. L1 = 70 px, L2 = 60 px. What are the largest and smallest reach?
2. With q1 = 90° and q2 = 0°, where is the gripper relative to the shoulder (on screen)?
3. Why does the lab compute the angle error with `atan2(sin, cos)` instead of `target − q`?
