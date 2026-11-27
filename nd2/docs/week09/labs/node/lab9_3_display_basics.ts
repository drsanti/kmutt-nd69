/**
 * Lab 9.3 - Drawing on the device: a live |a| meter on the board's own screen.
 *
 * Opens a page (tab) on the board's 320 x 240 screen and draws a horizontal meter for |a|,
 * updating only the part of the bar that changed (no flicker, few bytes over USB).
 *
 *   npx tsx lab9_3_display_basics.ts --replay     # any board as the screen, recorded motion
 *   npx tsx lab9_3_display_basics.ts              # ws28p: live IMU + its screen
 */
import * as rk from "robotos-board";
import { imuSource, intro, onExit, parseArgs, run } from "./lab_common.ts";

const [BAR_X, BAR_Y, BAR_W, BAR_H] = [10, 110, 300, 30];      // meter area (inside the page body)
const A_MAX = 30;                                             // |a| at a full bar (m/s^2, about 3 g)
const USAGE = "npx tsx lab9_3_display_basics.ts [--replay [file.csv ...]] [--seconds N] [--port PATH]";

run(async () => {
  const args = parseArgs(USAGE);
  intro(args, {
    live: "Look at the board: a METER tab appears. Move and shake the board - the bar shows how hard.",
    replay: "Look at the board: a METER tab appears and the recorded motion drives the bar.",
    look: "Before TODO 3 the bar flickers; after it, it moves smoothly. At the end, compare 'commands' in the printed link stats before and after your fix.",
    before: "no title or frame on the screen (TODO 1) and an empty bar (TODO 2). Once the bar moves, it flickers until TODO 3.",
  });
  const d = await rk.Display.open({ port: args.port, name: "METER" });
  onExit(() => d.close());
  const src = imuSource(args, d.session);

  // TODO 1: draw the static parts once: clear the page, a title, and a white frame (d.rect) just around the meter
  d.clear();
  await d.flush();

  let shown = 0, shownColor: number | null = null;           // what the bar on screen looks like now
  let n = 0;
  const tEnd = Date.now() + args.seconds * 1000;
  for await (const s of src) {
    if (++n % 5) continue;                                    // 50 Hz IMU -> redraw at 10 Hz
    // TODO 2: convert |a| (0..A_MAX) to a bar width in pixels (0..BAR_W), clipped to that range
    const width = 0;
    const color = s.aMag < 15 ? rk.Color.GREEN : s.aMag < 22 ? rk.Color.YELLOW : rk.Color.RED;
    // TODO 3: the starter repaints the whole bar every frame and FLICKERS. Draw only what changed: grow -> paint the new part, shrink -> erase the extra part, new colour -> repaint the bar
    d.fillRect(BAR_X, BAR_Y, BAR_W, BAR_H, rk.Color.BLACK); await d.flush(); d.fillRect(BAR_X, BAR_Y, width, BAR_H, color);
    d.text(10, 160, `|a| = ${s.aMag.toFixed(2).padStart(5)} m/s^2  `, rk.Color.WHITE);
    await d.flush();
    if (Date.now() > tEnd) break;
  }
  console.log("link:", d.stats);
});
