/**
 * Lab 9.4 - Live charts on the device: a 3-axis strip chart and a bubble level.
 *
 * Top: ax, ay, az scroll across the screen like a chart recorder (StripChart, sweep style).
 * Bottom right: a "bubble" that moves with the board's tilt, like a spirit level.
 *
 *   npx tsx lab9_4_live_charts.ts --replay     # any board as the screen, recorded motion
 *   npx tsx lab9_4_live_charts.ts              # ws28p: live IMU + its screen
 */
import * as rk from "robotos-board";
import { imuSource, onExit, parseArgs, run } from "./lab_common.ts";

const [LEVEL_CX, LEVEL_CY, LEVEL_R] = [260, 182, 34];      // bubble level: centre and radius of the dial
const BUBBLE_R = 7;
const USAGE = "npx tsx lab9_4_live_charts.ts [--replay [file.csv ...]] [--seconds N] [--port PATH]";

run(async () => {
  const args = parseArgs(USAGE);
  const d = await rk.Display.open({ port: args.port, name: "CHARTS" });
  onExit(() => d.close());
  const src = imuSource(args, d.session);

  // TODO 1: create a StripChart with 3 traces (ax red, ay green, az blue), each with range [-20, 20] m/s^2, at x 4, y 50, w 312, h 90
  const chart = new rk.StripChart(d, { ranges: [[-20, 20]], x: 4, y: 50, w: 312, h: 90 });

  const paint = () => {
    d.clear();
    chart.reset();
    d.text(4, 146, "ax", rk.Color.RED).text(36, 146, "ay", rk.Color.GREEN).text(68, 146, "az", rk.Color.BLUE);
    d.circle(LEVEL_CX, LEVEL_CY, LEVEL_R, rk.Color.DARK);
    d.hline(LEVEL_CX - LEVEL_R, LEVEL_CY, 2 * LEVEL_R, rk.Color.GRAY).vline(LEVEL_CX, LEVEL_CY - LEVEL_R, 2 * LEVEL_R, rk.Color.GRAY);
    d.text(4, 196, "tilt the board ->", rk.Color.GRAY);
  };
  d.onShown = paint;                                       // the user tapped back to this tab: repaint
  paint();
  await d.flush();

  let old: [number, number] | null = null;                // bubble position currently on screen
  let n = 0;
  const tEnd = Date.now() + args.seconds * 1000;
  for await (const s of src) {
    let drawn = chart.push(s.ax, s.ay, s.az);
    if (++n % 5 === 0) {                                   // bubble at 10 Hz
      // TODO 2: bubble position from tilt: ax / G and ay / G are about -1..1 (clip them); move up to LEVEL_R - BUBBLE_R pixels from the centre
      const [bx, by] = [LEVEL_CX, LEVEL_CY];
      if (!old || old[0] !== bx || old[1] !== by) {
        // TODO 3: the starter leaves a TRAIL of bubbles. Erase only the old bubble (paint it in the dial colour, rk.Color.DARK), then draw the new one in YELLOW
        d.circle(bx, by, BUBBLE_R, rk.Color.YELLOW);
        d.hline(LEVEL_CX - LEVEL_R, LEVEL_CY, 2 * LEVEL_R, rk.Color.GRAY).vline(LEVEL_CX, LEVEL_CY - LEVEL_R, 2 * LEVEL_R, rk.Color.GRAY);
        old = [bx, by];
      }
      drawn ||= 1;
    }
    if (drawn) await d.flush();
    if (Date.now() > tEnd) break;
  }
  console.log("link:", d.stats, "| chart dropped samples:", chart.dropped);
});
