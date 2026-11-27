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
import { imuSource, intro, onExit, parseArgs, run } from "./lab_common.ts";

const [LEVEL_CX, LEVEL_CY, LEVEL_R] = [260, 182, 34];      // bubble level: centre and radius of the dial
const BUBBLE_R = 7;
const USAGE = "npx tsx lab9_4_live_charts.ts [--replay [file.csv ...]] [--seconds N] [--port PATH]";

run(async () => {
  const args = parseArgs(USAGE);
  intro(args, {
    live: "Look at the board: a CHARTS tab appears. Tilt the board in all directions, then shake it.",
    replay: "Look at the board: a CHARTS tab appears; the recorded motion drives the chart and the bubble.",
    look: "Three lines (ax red, ay green, az blue) sweep left to right like a chart recorder; the yellow bubble moves like a spirit level and leaves no trail.",
  });
  const d = await rk.Display.open({ port: args.port, name: "CHARTS" });
  onExit(() => d.close());
  const src = imuSource(args, d.session);

  // Step 1: create a StripChart with 3 traces (ax red, ay green, az blue), each with range [-20, 20] m/s^2, at x 4, y 50, w 312, h 90
  const chart = new rk.StripChart(d, { ranges: [[-20, 20], [-20, 20], [-20, 20]], colors: [rk.Color.RED, rk.Color.GREEN, rk.Color.BLUE], x: 4, y: 50, w: 312, h: 90 });

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
      // Step 2: bubble position from tilt: ax / G and ay / G are about -1..1 (clip them); move up to LEVEL_R - BUBBLE_R pixels from the centre
      const reach = LEVEL_R - BUBBLE_R;
      const clip = (v: number) => Math.max(-1, Math.min(1, v));
      const bx = LEVEL_CX + Math.round(clip(s.ax / rk.G) * reach);
      const by = LEVEL_CY + Math.round(clip(s.ay / rk.G) * reach);
      if (!old || old[0] !== bx || old[1] !== by) {
        // Step 3: a simpler version leaves a TRAIL of bubbles. Erase only the old bubble (paint it in the dial colour, rk.Color.DARK), then draw the new one in YELLOW
        if (old) d.circle(old[0], old[1], BUBBLE_R, rk.Color.DARK);
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
