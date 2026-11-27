"""Lab 9.3 — Drawing on the device: a live |a| meter on the board's own screen.

Opens a page (tab) on the board's 320 x 240 screen and draws a horizontal meter for |a|,
updating only the part of the bar that changed (no flicker, few bytes over USB).

    python lab9_3_display_basics.py --replay           # any board as the screen, recorded motion
    python lab9_3_display_basics.py                    # ws28p: live IMU + its screen
"""
import time

import robotos_edge as rk
from lab_common import imu_source, parse_args

BAR_X, BAR_Y, BAR_W, BAR_H = 10, 110, 300, 30       # meter area (inside the page body)
A_MAX = 30.0                                        # |a| at a full bar (m/s^2, about 3 g)


def main():
    args = parse_args(__doc__)
    d = rk.Display.open(args.port, name="METER")
    src = imu_source(args, d.session)

    # TODO 1: draw the static parts once: clear the page, a title, and a white frame around the meter
    d.clear()
    d.flush()

    shown, shown_color = 0, None                    # what the bar on screen looks like now
    n, t_end = 0, time.monotonic() + args.seconds
    for s in src:
        n += 1
        if n % 5:                                   # 50 Hz IMU -> redraw at 10 Hz
            continue
        # TODO 2: convert |a| (0..A_MAX) to a bar width in pixels (0..BAR_W), clipped
        width = 0
        color = rk.Color.GREEN if s.a_mag < 15 else rk.Color.YELLOW if s.a_mag < 22 else rk.Color.RED
        # TODO 3: the starter repaints the whole bar every frame and FLICKERS. Draw only what changed instead: grow -> paint the new part, shrink -> erase the extra part, new colour -> repaint the bar
        d.fill_rect(BAR_X, BAR_Y, BAR_W, BAR_H, rk.Color.BLACK); d.flush(); d.fill_rect(BAR_X, BAR_Y, width, BAR_H, color)
        d.text(10, 160, f"|a| = {s.a_mag:5.2f} m/s^2  ", rk.Color.WHITE)
        d.flush()
        if time.monotonic() > t_end:
            break
    print("link:", d.stats)
    d.close()


if __name__ == "__main__":
    main()
