"""Lab 9.2 — The animation loop: move a box smoothly, at a speed that does not depend on fps.

Every frame: measure dt, update the position, draw only what changed, flush.

    python lab9_2_animation_loop.py                # 15 fps
    python lab9_2_animation_loop.py --fps 5        # same speed, fewer frames?
"""
import time

import robotos_edge as rk
from lab_common import Clock, intro, parse_args

X0, X1, Y = 10, 300, 120                     # track for the box
BOX_W, BOX_H = 18, 14
BOX = rk.rgb565(210, 150, 60)
SPEED = 60.0                                 # px per second


def main():
    args = parse_args(__doc__, seconds=20,
                      extra=lambda ap: ap.add_argument("--fps", type=float, default=15.0))
    intro(__doc__, args,
          do='Look at the board: a box moves along a track and bounces at both ends. Then run it again with --fps 5.',
          look='After TODO 1 the box crosses the track in the same time at any --fps (only less smoothly); after TODO 3 the flicker is gone.',
          before='the box moves 4 px per frame, so --fps 5 makes it slower (TODO 1); it jumps back to the start instead of bouncing (TODO 2); and it flickers (TODO 3).')
    d = rk.Display.open(args.port, name="CELL")
    d.clear()
    d.text(10, 50, f"Lab 9.2 animation loop @ {args.fps:.0f} fps", rk.Color.GRAY)
    d.hline(X0, Y + BOX_H + 1, X1 - X0, rk.Color.GRAY)
    d.flush()

    x, v = float(X0), SPEED
    shown = None                             # x of the box currently on screen
    clock, t_end, frames = Clock(args.fps), time.monotonic() + args.seconds, 0
    while time.monotonic() < t_end:
        dt = clock.tick()
        # TODO 1: move the box: new x = x + speed * dt (then the speed in px/s is the same at any fps)
        x = x + 4
        # TODO 2: bounce: when the box reaches X0 or X1 - BOX_W, clamp x and reverse the speed v
        x = X0 if x > X1 - BOX_W else x
        xi = int(round(x))
        # TODO 3: the starter clears the whole track and redraws the box every frame (it FLICKERS). Draw only the change: erase the old box, then draw the new one, in ONE flush
        d.fill_rect(X0, Y, X1 - X0, BOX_H, rk.Color.BLACK); d.flush(); d.fill_rect(xi, Y, BOX_W, BOX_H, BOX)
        shown = xi
        if frames % 15 == 0:
            d.text(10, 160, f"fps {clock.fps:5.1f}  dt {dt * 1000:5.1f} ms ", rk.Color.WHITE)
        d.flush()
        frames += 1
    print(f"{frames} frames, fps {clock.fps:.1f}, link {d.stats}")
    d.close()


if __name__ == "__main__":
    main()
