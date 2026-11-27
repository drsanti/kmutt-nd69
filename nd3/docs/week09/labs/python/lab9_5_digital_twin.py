"""Lab 9.5 — The digital-twin cell: conveyor + robot arm + stack light, driven by a state machine.

Boxes ride the conveyor; the arm picks each one at the end of the belt and drops it in the bin.
The stack light shows the cell state. Shake the board (ws28p) to trigger an EMERGENCY STOP;
tap the screen to reset it.

    python lab9_5_digital_twin.py --replay --auto-reset   # any board screen, recorded motion
    python lab9_5_digital_twin.py                         # ws28p: live, shake = e-stop
"""
import math
import time

import robotos_edge as rk
from robotos_edge.hardware.display import TOUCH_DOWN
from robotos_edge.scene import Arm, Conveyor, StackLight
from lab_common import Clock, imu_source, intro, parse_args

PICK = (223, 154)            # gripper above the box at the end of the belt
PLACE = (300, 182)           # gripper above the bin
HOME = (250, 80)
BIN = (284, 196, 34, 22)     # x, y, w, h
SHAKE_MS2 = 15.0             # shake = |a| above this ...
SHAKE_RAD_S = 2.0            # ... while the board also rotates faster than this (a lift does not)
SPAWN_S = 3.0
TURN_RAD_S = 2.5             # arm joint speed


def main():
    args = parse_args(__doc__, seconds=120,
                      extra=lambda ap: ap.add_argument("--auto-reset", action="store_true",
                                                       help="reset an e-stop after 3 s of calm (unattended demos)"))
    intro(__doc__, args,
          live='Watch the cell work. Then shake the board hard: EMERGENCY STOP (red light, belt stops). Tap the screen to resume.',
          replay='Watch the cell work; the recording contains a shake that triggers the EMERGENCY STOP. Add --auto-reset so it resumes by itself (nobody taps during a replay).',
          look="Stack light: green = running, yellow = arm busy, red = stopped. The 'placed' counter grows; after a stop the arm carries on from where it stopped.")
    d = rk.Display.open(args.port, name="CELL")
    imu = imu_source(args, d.session, default=["idle"] * 4 + ["shake"])
    belt, arm, light = Conveyor(), Arm(), StackLight()
    state, resume, placed, last_spawn, calm_since = "RUN", "RUN", 0, -SPAWN_S, None
    bx, by, bw, bh = BIN
    bin_shapes = [rk.rect_shape(bx, by, bw, 1, rk.Color.GRAY), rk.rect_shape(bx, by + bh - 1, bw, 1, rk.Color.GRAY),
                  rk.rect_shape(bx, by, 1, bh, rk.Color.GRAY), rk.rect_shape(bx + bw - 1, by, 1, bh, rk.Color.GRAY)]
    home_q = arm.ik(*HOME)
    arm.q = list(home_q)

    def paint(_d=None):
        d.clear()
        belt.draw_static(d)
        d.rect(*BIN, rk.Color.GRAY)
        light.draw_static(d)
        arm.draw_static(d)
        d.text(44, 50, "digital twin cell", rk.Color.GRAY)

    d.on_shown = paint
    paint()
    d.flush()
    clock, t_end, shown = Clock(fps=15), time.monotonic() + args.seconds, None
    while time.monotonic() < t_end:
        dt = clock.tick()
        now = time.monotonic()
        samples = imu.read()
        a_max = max((s.a_mag for s in samples), default=9.81)
        g_max = max((math.sqrt(s.gx ** 2 + s.gy ** 2 + s.gz ** 2) for s in samples), default=0.0)
        tapped = any(t.event == TOUCH_DOWN for t in d.touches())

        # TODO 1: emergency stop: a shake (a_max > SHAKE_MS2 and g_max > SHAKE_RAD_S) in any state -> "ESTOP" (remember the state to resume). In ESTOP, a tap (or --auto-reset after 3 s of calm) goes back to that state
        pass

        if state != "ESTOP":
            if now - last_spawn > SPAWN_S and len(belt.boxes) < 4:
                belt.add_box()
                last_spawn = now
            belt.step(dt)
            step = TURN_RAD_S * dt
            # TODO 2: the arm's state machine: RUN -> (box at the end) PICK -> CARRY -> RETURN -> RUN. In PICK/CARRY/RETURN move toward PICK/PLACE/HOME with arm.move_toward(arm.ik(x, y), step); on arrival: PICK takes the box off the belt (arm.holding), CARRY drops it (placed += 1)
            pass

        # TODO 3: stack light: green = RUN, yellow = arm busy (PICK/CARRY/RETURN), red = ESTOP; and stop the belt (speed 0) while in ESTOP
        light.set("green")

        belt.draw(d)
        arm.draw(d, under=lambda: belt.shapes() + bin_shapes)   # repaint what the arm uncovers
        light.draw(d)
        status = (state, placed)
        if status != shown:
            label = "EMERGENCY STOP - tap" if state == "ESTOP" else f"{state:<6} placed {placed:3d}"
            d.text(44, 74, f"{label:<20}", rk.Color.RED if state == "ESTOP" else rk.Color.WHITE)
            shown = status
        d.flush()
    print(f"placed {placed} boxes | fps {clock.fps:.1f} | link {d.stats}")
    d.close()


if __name__ == "__main__":
    main()
