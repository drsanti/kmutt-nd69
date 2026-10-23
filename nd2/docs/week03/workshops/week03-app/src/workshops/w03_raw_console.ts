// Workshop 03 — raw serial console.
// Proves the plumbing before any parsing: open the port, dump
// every line the device sends. If you see JSON here, w04 is just
// a decode away. Also the simplest possible Web Serial program.
import { button, grid, logBox, panel, status, title } from "../lib/ui";
import { connect } from "../lib/serial";

export function run() {
  title("w03 — raw console", "plumbing check, no parsing");

  const st = status();
  const log = logBox();
  let count = 0;

  const conn = panel("connection");
  conn.append(button("Connect", async () => {
    try {
      const dev = await connect();
      st.set(true);
      log.line("sys", "port open — listening");
      dev.onLine((line) => {
        count++;
        log.line("rx", `#${count}  ${line}`);   // raw line, unparsed
      });
    } catch (e) {
      st.set("err");
      log.line("sys", String(e));
    }
  }, "primary"));

  const lp = panel("raw lines");
  lp.append(log.el);

  const row = grid();
  row.append(conn);
  document.getElementById("app")!.append(st.el, row, lp);
}
