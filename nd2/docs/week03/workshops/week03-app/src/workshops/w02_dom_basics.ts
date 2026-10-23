// Workshop 02 — DOM + state basics.
// Build a small control panel that does everything locally —
// no device yet. This is the UI skeleton the real app reuses.
import { button, colorField, gauge, grid, logBox, panel, slider, status, swatch, title } from "../lib/ui";

export function run() {
  title("w02 — control panel", "local only, no device yet");

  const st = status();
  document.getElementById("app")!.append(st.el);

  const row = grid();

  // --- connect panel (stub for now — real connect comes in w04) ---
  const conn = panel("connection");
  conn.append(
    button("Connect (stub)", () => {
      st.set(true);
      log.line("sys", "connect is a stub — real serial comes in w04");
    }, "primary"),
    button("Disconnect", () => st.set(false)),
  );

  // --- LED panel ---
  const led = panel("led color");
  const sw = swatch();
  led.append(
    sw.el,
    colorField("color", (hex) => {
      sw.set(hex);
      log.line("tx", `led ${hex}`);
    }),
  );

  // --- level panel ---
  const lvl = panel("level");
  const g = gauge();
  lvl.append(g.el, slider("drive", 0, 100, 30, (v) => g.set(v / 100)));

  // --- log ---
  const log = logBox();
  const lp = panel("log");
  lp.append(log.el);

  row.append(conn, led, lvl);
  document.getElementById("app")!.append(row, lp);
}
