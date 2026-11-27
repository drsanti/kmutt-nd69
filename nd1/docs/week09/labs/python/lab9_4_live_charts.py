"""Lab 9.4 — Live charts on the device: a 3-axis strip chart and a bubble level.

Top: ax, ay, az scroll across the screen like a chart recorder (StripChart, sweep style).
Bottom right: a "bubble" that moves with the board's tilt, like a spirit level.

    python lab9_4_live_charts.py --replay              # any board as the screen, recorded motion
    python lab9_4_live_charts.py                       # ws28p: live IMU + its screen
"""
import time

import robotos_edge as rk
from lab_common import imu_source, intro, parse_args

G = 9.80665
LEVEL_CX, LEVEL_CY, LEVEL_R = 260, 182, 34          # bubble level: centre and radius of the dial
BUBBLE_R = 7


def main():
    args = parse_args(__doc__)
    intro(__doc__, args,
          live='Look at the board: a CHARTS tab appears. Tilt the board in all directions, then shake it.',
          replay='Look at the board: a CHARTS tab appears; the recorded motion drives the chart and the bubble.',
          look='Three lines (ax red, ay green, az blue) sweep left to right like a chart recorder; the yellow bubble moves like a spirit level and leaves no trail (TODO 3).',
          before='only the red ax line (TODO 1) and a bubble that stays in the centre (TODO 2). Once the bubble moves, it leaves a trail until TODO 3.')
    d = rk.Display.open(args.port, name="CHARTS")
    src = imu_source(args, d.session)

    # TODO 1: create a StripChart for 3 traces (ax red, ay green, az blue), range -20..20 m/s^2, at x=4 y=50 w=312 h=90
    chart = rk.StripChart(d, ranges=[(-20, 20)], x=4, y=50, w=312, h=90)

    def paint(_d=None):
        d.clear()
        chart.reset()
        d.text(4, 146, "ax", rk.Color.RED).text(36, 146, "ay", rk.Color.GREEN).text(68, 146, "az", rk.Color.BLUE)
        d.circle(LEVEL_CX, LEVEL_CY, LEVEL_R, rk.Color.DARK)
        d.hline(LEVEL_CX - LEVEL_R, LEVEL_CY, 2 * LEVEL_R, rk.Color.GRAY)
        d.vline(LEVEL_CX, LEVEL_CY - LEVEL_R, 2 * LEVEL_R, rk.Color.GRAY)
        d.text(4, 196, "tilt the board ->", rk.Color.GRAY)

    d.on_shown = paint
    paint()
    d.flush()

    old = None                                      # bubble position currently on screen
    n, t_end = 0, time.monotonic() + args.seconds
    for s in src:
        n += 1
        drawn = chart.push(s.ax, s.ay, s.az)
        if n % 5 == 0:                              # bubble at 10 Hz
            # TODO 2: bubble position from tilt: ax/G and ay/G are in -1..1; move up to LEVEL_R - BUBBLE_R pixels from the centre
            bx, by = LEVEL_CX, LEVEL_CY
            if (bx, by) != old:
                # TODO 3: erase only the old bubble (paint it in the dial colour), then draw the new one in YELLOW
                d.circle(bx, by, BUBBLE_R, rk.Color.YELLOW)
                d.hline(LEVEL_CX - LEVEL_R, LEVEL_CY, 2 * LEVEL_R, rk.Color.GRAY)
                d.vline(LEVEL_CX, LEVEL_CY - LEVEL_R, 2 * LEVEL_R, rk.Color.GRAY)
                old = (bx, by)
            drawn = drawn or 1
        if drawn:
            d.flush()
        if time.monotonic() > t_end:
            break
    print("link:", d.stats, "| chart dropped samples:", chart.dropped)
    d.close()


if __name__ == "__main__":
    main()
