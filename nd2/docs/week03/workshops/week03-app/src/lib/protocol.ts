// The wire protocol — shared between the web app and fake_device.py.
// One JSON object per line. Next week the real board speaks the
// same shape, so nothing here changes.

// device → app
export interface Telemetry {
  type: "telemetry";
  seq: number;
  level: number;        // 0..1 — e.g. audio level / sensor value
  ts_ms: number;
}

// app → device
export interface LedCommand {
  type: "led";
  r: number;            // 0..255
  g: number;
  b: number;
}
export interface RateCommand {
  type: "rate";
  hz: number;
}
export type Command = LedCommand | RateCommand;

export function parseTelemetry(line: string): Telemetry | null {
  try {
    const o = JSON.parse(line);
    return o.type === "telemetry" ? (o as Telemetry) : null;
  } catch {
    return null;      // non-JSON noise on the wire — skip
  }
}

export function led(r: number, g: number, b: number): string {
  return JSON.stringify({ type: "led", r, g, b });
}

export function rate(hz: number): string {
  return JSON.stringify({ type: "rate", hz });
}

export function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
