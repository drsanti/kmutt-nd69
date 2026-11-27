# Week 09 Checkpoint Quiz

![track](https://img.shields.io/badge/track-ND03-6d28d9?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-checkpoint-2e8b57?style=flat-square)

[Week 09 index](README.md) · [Labs Guide](labs/README.md)

Answer in your notes; short answers are enough.

1. On the board's screen, which corner is (0, 0), and in which direction does y grow?
2. A box 14 px high must sit on a belt whose top is at y = 150. What y do you pass to `fill_rect`?
3. Your loop moves an object `x += 5` every frame. At 15 fps, what is its speed in px/s? At 5 fps?
4. Rewrite the update so the speed is 75 px/s at any frame rate.
5. Why does "clear the screen, then draw everything" flicker? What do you do instead?
6. The board draws at most 32 operations per screen update. Why can a picture of 60 operations not appear all at once?
7. A conveyor roller has radius 8 px and the belt moves at 40 px/s. How fast does the roller turn (rad/s)?
8. A 2-link arm has L1 = 70, L2 = 60. Is a target 140 px from the shoulder reachable? One 5 px away?
9. Give the forward-kinematics formula for the gripper's **screen** y.
10. Why does a target usually have two IK solutions, and which one did the lab choose?
11. In the digital-twin cell, list the states of the arm's state machine and what makes each one end.
12. Why must the emergency stop be checked before the state machine, and why must reset resume the *previous* state rather than always going back to RUN?
