"""Lab 9.1 — Shapes and coordinates: draw a factory cell on the board screen.

Screen pixels: x to the right, y DOWN, (0, 0) top-left. Your area is y 46..221.

    python lab9_1_static_cell.py            # any board (ws28p or es3c28p)
"""
import math
import time

import robotos_edge as rk
from lab_common import intro, parse_args

BELT_X0, BELT_X1, BELT_Y = 10, 232, 172      # conveyor: left end, right end, top of the belt
ROLLER_R = 7
BOX_W, BOX_H = 18, 14
STEEL = rk.rgb565(150, 160, 175)
BELT = rk.rgb565(90, 90, 100)
BOX = rk.rgb565(210, 150, 60)
BASE = (272, 128)                            # robot shoulder
L1, L2 = 58, 50


def main():
    args = parse_args(__doc__, seconds=10)
    intro(__doc__, args,
          do='Look at the board: a CELL tab appears with your drawing (it stays for 10 s).',
          look='The conveyor, three boxes sitting ON the belt, a stack light and the robot arm. The script prints how many drawing operations the picture needed (the board draws up to 32 per screen update).')
    d = rk.Display.open(args.port, name="CELL")
    d.clear()
    d.text(44, 50, "Lab 9.1 static cell", rk.Color.GRAY)

    # Step 1: the conveyor: a belt top (6 px high) and a return belt (3 px) from BELT_X0 to BELT_X1, and 3 rollers (left end, middle, right end) between them
    d.fill_rect(BELT_X0, BELT_Y, BELT_X1 - BELT_X0, 6, BELT)
    d.fill_rect(BELT_X0, BELT_Y + 6 + 2 * ROLLER_R, BELT_X1 - BELT_X0, 3, BELT)
    for cx in (BELT_X0 + ROLLER_R, (BELT_X0 + BELT_X1) // 2, BELT_X1 - ROLLER_R):
        d.circle(cx, BELT_Y + 6 + ROLLER_R, ROLLER_R, STEEL)

    # Step 2: three boxes sitting ON the belt at x = 40, 100, 160 (which y puts their bottom on the belt top?)
    for x in (40, 100, 160):
        d.fill_rect(x, BELT_Y - BOX_H, BOX_W, BOX_H, BOX)

    # Step 3: a stack light (red, yellow, green circles r=8 stacked at x=20 from y=70) and the robot arm: link 1 at 120 deg, link 2 at -60 deg relative, using d.line()
    for i, c in enumerate((rk.Color.RED, rk.Color.YELLOW, rk.Color.GREEN)):
        d.circle(20, 70 + i * 19, 8, c)
    q1, q2 = math.radians(120), math.radians(-60)
    x1, y1 = BASE[0] + L1 * math.cos(q1), BASE[1] - L1 * math.sin(q1)         # screen y is down
    x2, y2 = x1 + L2 * math.cos(q1 + q2), y1 - L2 * math.sin(q1 + q2)
    d.fill_rect(BASE[0] - 14, BASE[1], 28, 10, STEEL)
    d.line(BASE[0], BASE[1], x1, y1, STEEL, 8)
    d.line(x1, y1, x2, y2, STEEL, 6)
    d.circle(int(x1), int(y1), 5, rk.Color.WHITE)
    d.circle(int(x2), int(y2), 4, rk.Color.ORANGE)

    n = d.pending()
    d.flush()
    print(f"drew the cell with {n} drawing operations; link {d.stats}")
    time.sleep(args.seconds)
    d.close()


if __name__ == "__main__":
    main()
