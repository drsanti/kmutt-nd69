// Workshop 05 — Web Serial write path.
// Commands go the other way: browser → device.
// Complete monitor + control loop.
import { button, colorField, gauge, grid, logBox, panel, slider, status, swatch, title } from "../lib/ui";
import { connect, type SerialDevice } from "../lib/serial";
import { hexToRgb, led, parseTelemetry, rate } from "../lib/protocol";

export function run() {
  title("w05 — serial control", "monitor + command");

  const st = status();
  const g = gauge();
  const sw = swatch();
  const log = logBox();
  let dev: SerialDevice | null = null;

  const conn = panel("connection");
  conn.append(button("Connect", async () => {
    try {
      dev = await connect();
      st.set(true);
      dev.onLine((line) => {
        log.line("rx", line);
        const t = parseTelemetry(line);
        if (t) g.set(t.level);
      });
    } catch (e) {
      st.set("err");
      log.line("sys", String(e));
    }
  }, "primary"));

  const led_ = panel("led color");
  led_.append(sw.el, colorField("color", (hex) => {
    sw.set(hex);
    const [r, gg, b] = hexToRgb(hex);
    const cmd = led(r, gg, b);
    log.line("tx", cmd);
    void dev?.write(cmd);
  }));

  const ctl = panel("telemetry rate");
  ctl.append(
    g.el,
    slider("rate Hz", 1, 20, 5, (v) => {
      const cmd = rate(v);
      log.line("tx", cmd);
      void dev?.write(cmd);
    }),
  );

  const lp = panel("log");
  lp.append(log.el);

  const row = grid();
  row.append(conn, led_, ctl);
  document.getElementById("app")!.append(st.el, row, lp);
}
