"""Lab 9.3 — A working conveyor: boxes spawn, ride the belt, and the board's tilt sets the speed.

Tilt the ws28p left/right to run the belt backward/forward; rollers turn with the belt.

    python lab9_3_conveyor.py --replay      # any board screen, recorded motion
    python lab9_3_conveyor.py               # ws28p: live tilt
"""
import math
import time

import robotos_edge as rk
from robotos_edge.scene import Box, BELT, STEEL
from lab_common import Clock, imu_source, intro, parse_args

X0, X1, Y = 10, 300, 150                     # belt from X0 to X1, top at Y
R = 8                                        # roller radius
ROLLERS = [X0 + R, (X0 + X1) // 2, X1 - R]
G = 9.80665
V_MAX = 90.0                                 # px/s at full tilt
SPAWN_S = 2.0


def main():
    args = parse_args(__doc__, seconds=40)
    intro(__doc__, args,
          live='Tilt the board left and right: the belt runs that way; hold it level to stop it.',
          replay='Nothing to do: the recorded motion tilts the belt for you - just watch.',
          look='A new box every 2 s rides the belt and leaves at the end; the dots on the rollers turn exactly as fast as the belt moves.')
    d = rk.Display.open(args.port, name="CELL")
    imu = imu_source(args, d.session)
    d.clear()
    d.text(10, 50, "Lab 9.3 conveyor: tilt to drive", rk.Color.GRAY)
    d.fill_rect(X0, Y, X1 - X0, 6, BELT)
    d.fill_rect(X0, Y + 6 + 2 * R, X1 - X0, 3, BELT)
    for cx in ROLLERS:
        d.circle(cx, Y + 6 + R, R, STEEL)
    d.flush()

    boxes, speed, angle, last_spawn, dots = [], 0.0, 0.0, -SPAWN_S, None
    clock, t_end = Clock(15), time.monotonic() + args.seconds
    while time.monotonic() < t_end:
        dt = clock.tick()
        samples = imu.read()
        if samples:
            ax = samples[-1].ax
            # Step 1: belt speed from tilt: ax / G is about -1..1; speed = that * V_MAX (clipped to +-V_MAX)
            speed = max(-1.0, min(1.0, ax / G)) * V_MAX
        now = time.monotonic()
        # Step 2: spawn a new Box(X0, Y - Box.H) every SPAWN_S seconds (at most 6); move every box by speed * dt; remove boxes that leave the belt (box.erase(d))
        if now - last_spawn > SPAWN_S and len(boxes) < 6:
            start = X0 if speed >= 0 else X1 - Box.W
            boxes.append(Box(start, Y - Box.H))
            last_spawn = now
        for b in list(boxes):
            b.x += speed * dt
            if b.x < X0 - 1 or b.x > X1 - Box.W + 1:
                b.erase(d)
                boxes.remove(b)
        for b in boxes:
            b.draw(d)
        # Step 3: turn the rollers: angle += speed * dt / R (rolling without slipping); draw a dot on each roller at that angle, erasing the old dots
        angle += speed * dt / R
        cy = Y + 6 + R
        new = [(int(cx + (R - 3) * math.cos(angle)), int(cy + (R - 3) * math.sin(angle))) for cx in ROLLERS]
        if new != dots:
            for p in dots or []:
                d.circle(p[0], p[1], 2, STEEL)
            for p in new:
                d.circle(p[0], p[1], 2, rk.Color.BLACK)
            dots = new
        d.text(10, 200, f"speed {speed:+6.1f} px/s  boxes {len(boxes)} ", rk.Color.WHITE)
        d.flush()
    print(f"fps {clock.fps:.1f}, link {d.stats}")
    d.close()


if __name__ == "__main__":
    main()
