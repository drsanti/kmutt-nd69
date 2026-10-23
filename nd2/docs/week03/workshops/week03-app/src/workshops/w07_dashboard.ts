// Workshop 07 — capstone: unified dashboard.
// The full monitor + control app behind a single connect button.
// Same shape the real board app takes next week.
import { button, colorField, gauge, grid, logBox, panel, slider, status, swatch, title } from "../lib/ui";
import { connect, type SerialDevice } from "../lib/serial";
import { hexToRgb, led, parseTelemetry, rate } from "../lib/protocol";

export function run() {
  title("w07 — device dashboard", "capstone");

  const st = status();
  const g = gauge();
  const sw = swatch();
  const log = logBox();
  let dev: SerialDevice | null = null;

  const conn = panel("connection");
  const connectBtn = button("Connect", async () => {
    try {
      dev = await connect();
      st.set(true);
      connectBtn.disabled = true;
      dev.onLine((line) => {
        log.line("rx", line);
        const t = parseTelemetry(line);
        if (t) g.set(t.level);
      });
    } catch (e) {
      st.set("err");
      log.line("sys", String(e));
    }
  }, "primary");
  const disconnectBtn = button("Disconnect", async () => {
    await dev?.close();
    dev = null;
    st.set(false);
    connectBtn.disabled = false;
  });
  conn.append(connectBtn, disconnectBtn);

  const led_ = panel("led color");
  led_.append(sw.el, colorField("color", (hex) => {
    sw.set(hex);
    const [r, gg, b] = hexToRgb(hex);
    void dev?.write(led(r, gg, b));
  }));

  const tele = panel("telemetry");
  tele.append(
    g.el,
    slider("rate Hz", 1, 20, 5, (v) => void dev?.write(rate(v))),
  );

  const lp = panel("log");
  lp.append(log.el);

  const row = grid();
  row.append(conn, led_, tele);
  document.getElementById("app")!.append(st.el, row, lp);
}
