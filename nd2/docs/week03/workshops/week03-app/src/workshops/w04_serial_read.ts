// Workshop 04 — Web Serial read path.
// requestPort → streams → decoded lines → telemetry gauge.
// Requires: device/fake_device.py running on a virtual serial pair.
import { button, gauge, grid, logBox, panel, status, title } from "../lib/ui";
import { connect } from "../lib/serial";
import { parseTelemetry } from "../lib/protocol";

export function run() {
  title("w04 — serial read", "telemetry from the device");

  const st = status();
  const g = gauge();
  const log = logBox();

  const conn = panel("connection");
  conn.append(button("Connect", async () => {
    try {
      const dev = await connect();
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

  const tele = panel("telemetry");
  tele.append(g.el);

  const lp = panel("log");
  lp.append(log.el);

  const row = grid();
  row.append(conn, tele);
  document.getElementById("app")!.append(st.el, row, lp);
}
