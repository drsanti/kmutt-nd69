// Workshop 01 — environment check.
// Verifies this browser can actually use the hardware APIs the
// week depends on. Run this first — it answers "is my setup right?"
import { grid, logBox, panel, status, title } from "../lib/ui";

export function run() {
  title("w01 — environment check", "can this browser reach hardware?");

  const st = status();
  const log = logBox();

  // --- capability panel: each API either exists or it doesn't ---
  const caps = panel("browser capabilities");

  const checks: [string, boolean][] = [
    ["Web Serial", "serial" in navigator],
    ["Web Bluetooth", "bluetooth" in navigator],
    ["Secure context", window.isSecureContext],
    ["Streams API", "ReadableStream" in window],
  ];

  for (const [name, ok] of checks) {
    const s = status();
    s.set(ok ? true : "err", `${name}: ${ok ? "yes" : "no"}`);
    caps.append(s.el);
  }

  // --- info panel ---
  const info = panel("about this browser");
  info.append(
    kv("user agent", navigator.userAgent),
    kv("location", location.href),
    kv("protocol", location.protocol),
  );

  function kv(k: string, v: string): HTMLElement {
    const d = document.createElement("div");
    d.className = "field";
    const l = document.createElement("label");
    l.textContent = k;
    const s = document.createElement("span");
    s.className = "value";
    s.textContent = v;
    s.style.textAlign = "left";
    s.style.minWidth = "0";
    d.append(l, s);
    return d;
  }

  // --- verdict ---
  const allOk = checks.every(([, ok]) => ok);
  st.set(allOk, allOk ? "ready" : "something is missing");

  const lp = panel("notes");
  log.line("sys", allOk
    ? "all checks passed — hardware APIs are available"
    : "missing capability? Web Serial + Web Bluetooth need Chrome/Edge on a secure context (localhost counts)");
  lp.append(log.el);

  const row = grid();
  row.append(caps, info);
  document.getElementById("app")!.append(st.el, row, lp);
}
