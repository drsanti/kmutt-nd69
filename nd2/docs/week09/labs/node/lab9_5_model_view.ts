/**
 * Lab 9.5 - Seeing the model: live gesture probabilities and a tunable threshold on the device.
 *
 * The gesture model runs in the Python gesture service (start it first, in another terminal).
 * This script sends it the IMU samples over a WebSocket, draws the four class probabilities as
 * bars with a yellow threshold line, highlights a detected gesture, and lets you tap the bar area
 * to move the threshold.
 *
 *   python gesture_service.py                     # terminal 1: in ../service, with its .venv active
 *   npx tsx lab9_5_model_view.ts --replay         # terminal 2: any board as the screen
 *   npx tsx lab9_5_model_view.ts                  # terminal 2: ws28p, live IMU
 */
import * as rk from "robotos-board";
import { imuSource, intro, onExit, parseArgs, run } from "./lab_common.ts";

const BARS = { x: 8, y: 50, w: 200, h: 168 };      // bar chart area
const PLOT_H = BARS.h - 36;                         // bars() puts two 16 px label rows under the plot here
const USAGE = "npx tsx lab9_5_model_view.ts [--replay [file.csv ...]] [--seconds N] [--port PATH]";

run(async () => {
  const args = parseArgs(USAGE);
  intro(args, {
    live: "First start the service in another terminal (cd ../service, activate .venv, python gesture_service.py). Then look at the board: a MODEL tab appears. Perform shake, circle and lift; tap high or low on the bars to move the yellow threshold line.",
    replay: "First start the service in another terminal (cd ../service, activate .venv, python gesture_service.py). Then look at the board: a MODEL tab appears and the recorded gestures play; tap high or low on the bars to move the yellow threshold line.",
    look: "Four probability bars; a bar turns orange when its gesture passes the threshold; the detection counters on the right. The service terminal prints every detection.",
  });
  const model = await rk.GestureClient.connect();             // ws://127.0.0.1:8765/ws
  onExit(() => model.close());
  const d = await rk.Display.open({ port: args.port, name: "MODEL" });
  onExit(() => d.close());
  const src = imuSource(args, d.session);
  const gestures = model.gestures;
  const hits: Record<string, number> = Object.fromEntries(gestures.map((g) => [g, 0]));

  const paint = () => {
    d.clear();
    d.text(216, 50, "detections", rk.Color.GRAY);
    gestures.forEach((g, i) => d.text(216, 72 + 20 * i, `${g.padEnd(6)} ${String(hits[g]).padStart(3)}`, rk.Color.WHITE));
    d.text(216, 176, `thr ${model.threshold.toFixed(2)}`, rk.Color.YELLOW);
    d.text(216, 196, "tap bars", rk.Color.GRAY);
  };
  d.onShown = paint;
  paint();
  await d.flush();

  let nDet = 0, n = 0;
  const tEnd = Date.now() + args.seconds * 1000;
  for await (const s of src) {
    // TODO 1: send every IMU sample to the gesture service (model.push)
    void s;
    if (++n % 5) continue;                                   // screen at 10 Hz
    const probs = gestures.map((g) => model.probs[g] ?? 0);
    const top = probs.indexOf(Math.max(...probs));
    // TODO 2: draw the bars with labels and the threshold line; highlight the top class only if it is not "idle" and >= the threshold
    d.bars(probs, gestures, BARS);
    if (model.detections.length > nDet) {                    // new detection(s): update the counters
      for (const det of model.detections.slice(nDet)) {
        hits[det.label]++;
        const i = gestures.indexOf(det.label);
        d.text(216, 72 + 20 * i, `${det.label.padEnd(6)} ${String(hits[det.label]).padStart(3)}`, rk.Color.ORANGE);
      }
      nDet = model.detections.length;
    }
    for (const t of d.touches()) {
      // TODO 3: a tap inside the bars' plot area sets the threshold: top of the plot = 1.0, bottom = 0.0 (round to 2 decimals, then model.setThreshold)
      void t;
    }
    await d.flush();
    if (Date.now() > tEnd) break;
  }
  console.log("detections:", hits, "| link:", d.stats);
});
