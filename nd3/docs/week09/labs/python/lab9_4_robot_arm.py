"""Lab 9.4 — A 2-link robot arm: forward kinematics, smooth motion, inverse kinematics.

Tap the screen: the arm reaches for the point you tapped. Without taps it visits four preset
targets in turn.

    python lab9_4_robot_arm.py              # any board (ws28p or es3c28p)
"""
import math
import time

import robotos_edge as rk
from robotos_edge.hardware.display import TOUCH_DOWN
from lab_common import Clock, intro, parse_args

BASE = (160, 200)                            # shoulder, near the bottom middle
L1, L2 = 70, 60                              # link lengths (px)
W1, W2 = 8, 6                                # link widths (px)
STEEL = rk.rgb565(150, 160, 175)
TURN = 2.0                                   # joint speed (rad/s)
PRESETS = [(90, 110), (230, 110), (200, 170), (110, 160)]


def fk(q1, q2):
    """Forward kinematics: joint angles (rad) -> elbow (x1, y1) and gripper (x2, y2) in screen px."""
    # Step 1: elbow = base + L1 * (cos q1, -sin q1); gripper = elbow + L2 * (cos(q1+q2), -sin(q1+q2)). Screen y grows DOWN, hence the minus
    x1 = BASE[0] + L1 * math.cos(q1)
    y1 = BASE[1] - L1 * math.sin(q1)
    x2 = x1 + L2 * math.cos(q1 + q2)
    y2 = y1 - L2 * math.sin(q1 + q2)
    return x1, y1, x2, y2


def ik(x, y):
    """Inverse kinematics: gripper target (screen px) -> (q1, q2) elbow-up, or None if unreachable."""
    # Step 3: law of cosines. dx = x - BASE_x, dy = BASE_y - y; cos q2 = (dx²+dy²-L1²-L2²)/(2 L1 L2) (None if |cos q2| > 1); q2 = -acos(...) for elbow up; q1 = atan2(dy, dx) - atan2(L2 sin q2, L1 + L2 cos q2)
    dx, dy = x - BASE[0], BASE[1] - y
    c2 = (dx * dx + dy * dy - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    if abs(c2) > 1:
        return None
    q2 = -math.acos(c2)
    q1 = math.atan2(dy, dx) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
    return q1, q2


def arm_shapes(pose):
    """The arm at pose (x1, y1, x2, y2) as a list of board shapes: two links, elbow, gripper."""
    x1, y1, x2, y2 = pose
    return (rk.line_shapes(BASE[0], BASE[1], x1, y1, STEEL, W1) + rk.line_shapes(x1, y1, x2, y2, STEEL, W2)
            + [rk.circle_shape(x1, y1, W1 // 2 + 1, rk.Color.WHITE), rk.circle_shape(x2, y2, W2 // 2 + 1, rk.Color.ORANGE),
               rk.circle_shape(BASE[0], BASE[1], W1 // 2 + 2, rk.Color.WHITE),
               rk.rect_shape(BASE[0] - 16, BASE[1], 32, 10, STEEL)])


def main():
    args = parse_args(__doc__, seconds=40)
    intro(__doc__, args,
          do='Tap a point on the screen: the arm reaches for it. Without taps it visits four preset targets in turn.',
          look="Smooth joint motion with no trail, and 'out of reach!' when you tap too far from the shoulder.")
    d = rk.Display.open(args.port, name="CELL")
    d.clear()
    d.text(10, 50, "Lab 9.4 robot arm: tap a target", rk.Color.GRAY)
    d.fill_rect(BASE[0] - 16, BASE[1], 32, 10, STEEL)
    d.flush()

    arm = rk.Sprite(d)                                   # the arm on screen
    q = [math.radians(90), math.radians(-30)]
    target_q, target_xy, aimed, preset, last_change = None, None, None, 0, -10.0
    shown = None
    clock, t_end = Clock(15), time.monotonic() + args.seconds
    while time.monotonic() < t_end:
        dt = clock.tick()
        now = time.monotonic()
        taps = [(t.x, t.y) for t in d.touches() if t.event == TOUCH_DOWN and t.y > 60]
        if taps:
            target_xy, last_change = taps[-1], now
        elif now - last_change > 4.0:
            target_xy, preset, last_change = PRESETS[preset % len(PRESETS)], preset + 1, now
        if target_xy and target_xy != aimed:
            if aimed:
                d.circle(int(aimed[0]), int(aimed[1]), 3, rk.Color.BLACK)       # remove the old target mark
            target_q, aimed = ik(*target_xy), target_xy
            d.text(10, 70, "out of reach!" if target_q is None else " " * 13, rk.Color.RED)
        if target_q:
            for i in range(2):                                    # turn each joint toward its target
                err = math.atan2(math.sin(target_q[i] - q[i]), math.cos(target_q[i] - q[i]))
                q[i] += max(-TURN * dt, min(TURN * dt, err))
        pose = tuple(int(round(v)) for v in fk(*q))
        if pose != shown:
            # Step 2: a simpler version only draws each new pose, so the arm leaves a trail. Move a Sprite instead: arm.move(arm_shapes(pose)) erases only the pixels the old pose no longer covers and draws the new pose, in ONE screen update, so there is no trail and no blink
            arm.move(arm_shapes(pose))
            shown = pose
        if target_xy:
            d.circle(int(target_xy[0]), int(target_xy[1]), 3, rk.Color.YELLOW)
        d.flush()
    print(f"fps {clock.fps:.1f}, link {d.stats}")
    d.close()


if __name__ == "__main__":
    main()
