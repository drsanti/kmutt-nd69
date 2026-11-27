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
    look: "The bar moves smoothly without flicker: each update redraws only the part of the bar that changed. The link stats printed at the end show how few commands that needs.",
  });
  const d = await rk.Display.open({ port: args.port, name: "METER" });
  onExit(() => d.close());
  const src = imuSource(args, d.session);

  // Step 1: draw the static parts once: clear the page, a title, and a white frame (d.rect) just around the meter
  d.clear();
  d.text(10, 56, "Lab 9.3  |a| meter", rk.Color.WHITE);
  d.rect(BAR_X - 2, BAR_Y - 2, BAR_W + 4, BAR_H + 4, rk.Color.WHITE);
  d.text(BAR_X, BAR_Y + BAR_H + 6, "0", rk.Color.GRAY);
  d.text(BAR_X + BAR_W - 24, BAR_Y + BAR_H + 6, A_MAX.toFixed(0), rk.Color.GRAY);
  await d.flush();

  let shown = 0, shownColor: number | null = null;           // what the bar on screen looks like now
  let n = 0;
  const tEnd = Date.now() + args.seconds * 1000;
  for await (const s of src) {
    if (++n % 5) continue;                                    // 50 Hz IMU -> redraw at 10 Hz
    // Step 2: convert |a| (0..A_MAX) to a bar width in pixels (0..BAR_W), clipped to that range
    const width = Math.round(Math.min(Math.max(s.aMag / A_MAX, 0), 1) * BAR_W);
    const color = s.aMag < 15 ? rk.Color.GREEN : s.aMag < 22 ? rk.Color.YELLOW : rk.Color.RED;
    // Step 3: a simpler version repaints the whole bar every frame and FLICKERS. Draw only what changed: grow -> paint the new part, shrink -> erase the extra part, new colour -> repaint the bar
    if (color !== shownColor) {
      d.fillRect(BAR_X, BAR_Y, width, BAR_H, color);
      if (width < shown) d.fillRect(BAR_X + width, BAR_Y, shown - width, BAR_H, rk.Color.BLACK);
    } else if (width > shown) d.fillRect(BAR_X + shown, BAR_Y, width - shown, BAR_H, color);
    else if (width < shown) d.fillRect(BAR_X + width, BAR_Y, shown - width, BAR_H, rk.Color.BLACK);
    shown = width;
    shownColor = color;
    d.text(10, 160, `|a| = ${s.aMag.toFixed(2).padStart(5)} m/s^2  `, rk.Color.WHITE);
    await d.flush();
    if (Date.now() > tEnd) break;
  }
  console.log("link:", d.stats);
});
