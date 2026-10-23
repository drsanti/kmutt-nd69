// Workshop 06 — Web Bluetooth.
// Connect to a BLE peripheral (phone running nRF Connect this week;
// the real board next week). Discover → connect → read a value.
import { button, grid, logBox, panel, status, title } from "../lib/ui";

export function run() {
  title("w06 — web bluetooth", "BLE, no cable");

  const st = status();
  const log = logBox();

  const conn = panel("connection");
  conn.append(button("Scan & connect", async () => {
    if (!("bluetooth" in navigator)) {
      st.set("err");
      log.line("sys", "Web Bluetooth unsupported — use Chrome or Edge");
      return;
    }
    try {
      const device = await navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: ["battery_service", "device_information"],
      });
      log.line("rx", `found: ${device.name ?? "(unnamed)"}`);
      const server = await device.gatt!.connect();
      st.set(true, `connected: ${device.name ?? "?"}`);

      // read battery level if the peripheral exposes it
      try {
        const svc = await server.getPrimaryService("battery_service");
        const ch = await svc.getCharacteristic("battery_level");
        const v = await ch.readValue();
        log.line("rx", `battery_level = ${v.getUint8(0)}%`);
      } catch {
        log.line("sys", "no battery_service — normal for a mock peripheral");
      }
    } catch (e) {
      st.set("err");
      log.line("sys", String(e));
    }
  }, "primary"));

  const lp = panel("log");
  lp.append(log.el);

  const row = grid();
  row.append(conn);
  document.getElementById("app")!.append(st.el, row, lp);
}
