// Shared DOM helpers — every workshop builds its UI from these,
// so workshop files contain zero markup/style code.

export function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className = "",
  text = "",
): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (text) e.textContent = text;
  return e;
}

export function title(t: string, sub = ""): void {
  const h = el("h1", "", t);
  if (sub) h.append(el("span", "dim", `  ${sub}`));
  document.getElementById("app")!.append(h);
}

export function panel(heading: string): HTMLElement {
  const p = el("div", "panel");
  p.append(el("h2", "", heading));
  return p;
}

export function grid(): HTMLElement {
  return el("div", "grid");
}

export function button(
  label: string,
  onClick: () => void,
  kind: "" | "primary" | "danger" = "",
): HTMLButtonElement {
  const b = el("button", `btn ${kind}`.trim(), label);
  b.onclick = onClick;
  return b;
}

export function status(): { el: HTMLElement; set(on: boolean | "err", text?: string): void } {
  const s = el("span", "status", "disconnected");
  return {
    el: s,
    set(on, text) {
      s.className = `status ${on === "err" ? "err" : on ? "on" : ""}`;
      s.textContent = text ?? (on === "err" ? "error" : on ? "connected" : "disconnected");
    },
  };
}

export function gauge(): { el: HTMLElement; set(frac: number): void } {
  const g = el("div", "gauge");
  const bar = el("div");
  g.append(bar);
  return {
    el: g,
    set(frac) { bar.style.width = `${Math.max(0, Math.min(1, frac)) * 100}%`; },
  };
}

export function logBox(): { el: HTMLElement; line(dir: "tx" | "rx" | "sys", text: string): void } {
  const box = el("div", "log");
  return {
    el: box,
    line(dir, text) {
      const prefix = dir === "tx" ? "→ " : dir === "rx" ? "← " : "! ";
      box.append(el("div", dir, prefix + text));
      box.scrollTop = box.scrollHeight;
    },
  };
}

export function slider(
  label: string,
  min: number, max: number, value: number,
  onInput: (v: number) => void,
): HTMLElement {
  const f = el("div", "field");
  const lab = el("label", "", label);
  const input = el("input") as HTMLInputElement;
  input.type = "range";
  input.min = String(min); input.max = String(max); input.value = String(value);
  const val = el("span", "value", String(value));
  input.oninput = () => {
    val.textContent = input.value;
    onInput(Number(input.value));
  };
  f.append(lab, input, val);
  return f;
}

export function colorField(
  label: string,
  onChange: (hex: string) => void,
): HTMLElement {
  const f = el("div", "field");
  const lab = el("label", "", label);
  const input = el("input") as HTMLInputElement;
  input.type = "color";
  input.value = "#22d3ee";
  input.oninput = () => onChange(input.value);
  f.append(lab, input);
  return f;
}

export function swatch(): { el: HTMLElement; set(hex: string): void } {
  const s = el("div", "swatch");
  return { el: s, set(hex) { s.style.background = hex; } };
}
