// Web Serial helpers — the real API is verbose; these wrap it so
// workshops stay focused on the concept being taught.
//
// The browser sees a "device" (real board next week; the Python
// fake_device.py this week) over a serial line carrying JSON text.

export interface SerialDevice {
  write(text: string): Promise<void>;
  onLine(cb: (line: string) => void): void;
  close(): Promise<void>;
}

/** Ask the user to pick a port and open it. Throws on cancel. */
export async function connect(baudRate = 115200): Promise<SerialDevice> {
  if (!("serial" in navigator)) {
    throw new Error("Web Serial unsupported — use Chrome or Edge");
  }
  const port = await navigator.serial.requestPort();
  await port.open({ baudRate });

  const decoder = new TextDecoderStream();
  const writer = new TextEncoderStream();

  // pipe serial → decoded text; keep a line buffer
  void port.readable!.pipeTo(decoder.writable as WritableStream);
  const reader = decoder.readable.getReader();
  void writer.readable.pipeTo(port.writable!);
  const w = writer.writable.getWriter();

  let buffer = "";
  const listeners: ((line: string) => void)[] = [];
  (async () => {
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += value;
        let i: number;
        while ((i = buffer.indexOf("\n")) >= 0) {
          const line = buffer.slice(0, i).trim();
          buffer = buffer.slice(i + 1);
          if (line) listeners.forEach((cb) => cb(line));
        }
      }
    } catch { /* port closed */ }
  })();

  return {
    async write(text: string) {
      await w.write(text.endsWith("\n") ? text : text + "\n");
    },
    onLine(cb) { listeners.push(cb); },
    async close() {
      try { await w.close(); } catch { /* already closed */ }
      try { reader.cancel(); } catch { /* already closed */ }
      await port.close();
    },
  };
}
