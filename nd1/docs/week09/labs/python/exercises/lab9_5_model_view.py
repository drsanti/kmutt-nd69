"""Lab 9.5 — Seeing the model: live gesture probabilities and a tunable threshold on the device.

Feeds the IMU into your gesture model (imu_artifacts/, see Setup), draws the four class probabilities as
bars with a yellow threshold line, highlights a detected gesture, and lets you tap the bar
area to move the threshold.

    robotos-kws train-imu --synthetic --out imu_artifacts    # if you have no model yet
    python lab9_5_model_view.py --replay                     # any board as the screen
    python lab9_5_model_view.py                              # ws28p: live IMU + its screen
"""
import time
from pathlib import Path

import robotos_edge as rk
from robotos_edge.hardware.display import TOUCH_DOWN
from robotos_edge.imu import features as ic
from lab_common import imu_source, intro, parse_args

BAR_X, BAR_Y, BAR_W, BAR_H = 8, 50, 200, 168        # bar chart
PLOT_H = BAR_H - 36       # bars() needs two staggered 16 px label rows here ("circle" fills its 50 px slot)
MODEL = Path("imu_artifacts/model_int8.tflite")


def main():
    args = parse_args(__doc__)
    intro(__doc__, args,
          live='Look at the board: a MODEL tab appears. Perform shake, circle and lift. Tap high or low on the bars to move the yellow threshold line. (Needs imu_artifacts/model_int8.tflite - see Setup.)',
          replay='Look at the board: a MODEL tab appears and the recorded gestures play. Tap high or low on the bars to move the yellow threshold line. (Needs imu_artifacts/model_int8.tflite - see Setup.)',
          look='Four probability bars; a bar turns orange when its gesture passes the threshold; the detection counters on the right.',
          before='all four bars stay at 0 (TODO 1), there is no yellow threshold line or orange highlight (TODO 2), and tapping the bars does nothing (TODO 3).')
    if not MODEL.exists():
        raise SystemExit(f"{MODEL} not found — train one first: robotos-kws train-imu --synthetic --out imu_artifacts")
    det = rk.GestureDetector(str(MODEL), threshold=0.7, verbose=False)
    d = rk.Display.open(args.port, name="MODEL")
    src = imu_source(args, d.session)
    hits = {g: 0 for g in ic.GESTURES}

    def paint(_d=None):
        d.clear()
        d.text(216, 50, "detections", rk.Color.GRAY)
        for i, g in enumerate(ic.GESTURES):
            d.text(216, 72 + 20 * i, f"{g:<6} {hits[g]:3d}", rk.Color.WHITE)
        d.text(216, 176, f"thr {det.threshold:.2f}", rk.Color.YELLOW)
        d.text(216, 196, "tap bars", rk.Color.GRAY)

    d.on_shown = paint
    paint()
    d.flush()

    n_det, n, t_end = 0, 0, time.monotonic() + args.seconds
    for s in src:
        n += 1
        # TODO 1: give every sample to the gesture detector (time, accel tuple, gyro tuple)
        pass
        if n % 5:
            continue
        probs = [det.probs[g] for g in ic.GESTURES]
        top = max(range(len(probs)), key=lambda i: probs[i])
        # TODO 2: draw the bars with labels and the threshold line; highlight the top class only if it is not "idle" and >= the threshold
        d.bars(probs, ic.GESTURES, BAR_X, BAR_Y, BAR_W, BAR_H)
        if len(det.detections) > n_det:                     # new detection(s): update the counters
            for _, label, _ in det.detections[n_det:]:
                hits[label] += 1
                i = ic.GESTURES.index(label)
                d.text(216, 72 + 20 * i, f"{label:<6} {hits[label]:3d}", rk.Color.ORANGE)
            n_det = len(det.detections)
        for t in d.touches():
            # TODO 3: a tap inside the bars' plot area sets the threshold: top of the plot = 1.0, bottom = 0.0
            pass
        d.flush()
        if time.monotonic() > t_end:
            break
    print("detections:", hits, "| link:", d.stats)
    d.close()


if __name__ == "__main__":
    main()
