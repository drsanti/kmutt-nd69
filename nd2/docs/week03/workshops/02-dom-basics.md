# Workshop 02 — DOM + state: the control panel

> **Goal:** build a working dashboard UI entirely in the browser —
> no device needed. This is the exact shell the real app reuses:
> a connect button, an LED control, a level gauge, and a log.

**Requirements:** workshop 01 done

---

## What you're looking at

`src/workshops/w02_dom_basics.ts` — the default module. Everything
on screen is built in ~40 lines of TypeScript using the shared
`lib/ui.ts` helpers:

```ts
const conn = panel("connection");
conn.append(button("Connect", () => { /* ... */ }, "primary"));

const led = panel("led color");
led.append(swatch().el, colorField("color", hex => { /* ... */ }));
```

Three ideas:

1. **`lib/ui.ts` gives you components** — `panel`, `button`,
   `gauge`, `slider`, `colorField`, `logBox`, `status`, `swatch`.
   Workshop files never write markup or CSS.
2. **`styles.css` is the shared theme** — the dark dashboard look
   is fixed; components apply classes like `.panel`, `.btn`,
   `.status.on`.
3. **Everything is a `run()` function** — called once by
   `main.ts` when the page loads.

## How a click becomes a visible change

The entire UI is one pattern repeated: a DOM event fires, your
callback runs, state changes, the DOM updates. No framework sits
between you and this loop — that's deliberate:

```
user            button          your callback      component       DOM
 |                |                  |                |             |
 |-- click ------>|-- handler() ---->|                |             |
 |                |                  |-- sw.set(hex)->|             |
 |                |                  |                |-- update -->|
 |                |                  |-- log.line() --------------->|
 |                |                  |                |             |
 |<------------------ browser repaints -----------------------------|
```

Two things to notice:

- **Callbacks are the whole control flow.** `button(label, fn)`
  stores `fn`; the browser calls it on click. There is no polling,
  no main loop — the app is *event-driven*, exactly like the
  embedded interrupt model in nd1 and the node callbacks in nd3.
- **State lives in the components.** `sw.set(hex)` mutates the
  swatch; `gauge.set(v)` moves the needle. The DOM is the output —
  your code never queries the DOM to ask "what color is it now?"

## Why no React this week

React (or any framework) would insert a reconciliation layer
between your code and the events — you'd learn *the framework's*
model of state, not the browser's. Since next week's real app must
handle streaming serial bytes and BLE notifications — imperative,
event-driven APIs — learning the raw `addEventListener` +
callback model now transfers directly. The `lib/ui.ts` helpers
exist only to remove markup repetition, not to hide the event
model.

## Step 1 — Read the layout

The workshop builds a grid of panels:

```
┌─────────────┬─────────────┬─────────────┐
│ connection  │  led color  │    level    │
│ (buttons)   │ (swatch +   │ (gauge +    │
│             │  picker)    │  slider)    │
├─────────────┴─────────────┴─────────────┤
│ log console — every action prints here  │
└─────────────────────────────────────────┘
```

This is the *same anatomy* the real app will have — status pill,
controls, telemetry display, and a wire log showing every message.

## Step 2 — Wire up the log

The `logBox()` helper is your best friend this week — it renders
the traffic between app and device with direction arrows:

```ts
log.line("rx", "incoming from device");   // ← cyan arrow
log.line("tx", "outgoing to device");     // → amber arrow
log.line("sys", "error / note");          // ! red
```

Try it: in `w02_dom_basics.ts`, make the Connect button log a line.
Save → hot reload → click the button.

## Step 3 — Wire a control to a (stub) command

The color picker already writes to the log:

```ts
colorField("color", (hex) => {
  sw.set(hex);                    // update the swatch
  log.line("tx", `led ${hex}`);   // "as if" we sent it
});
```

Save — the swatch now tracks the picker, and the log prints what
*would* go out on the wire. Notice the event loop again: pick →
callback → state → repaint. Workshops 03–07 replace that stub
`tx` line with real bytes on a real port.

## ✅ Checkpoint

- [ ] Panel grid renders: connection / led color / level / log
- [ ] Connect (stub) flips the status pill and logs a line
- [ ] Color picker updates the swatch and writes a `tx` log entry
- [ ] The drive slider moves the gauge — no device involved

## 🔧 Troubleshooting

| Symptom | Try |
|---|---|
| Click does nothing | open DevTools console — a JS error in a callback shows there |
| Page looks stale | save the file — HMR only fires on write; then hard-refresh |
| `panel is not defined` | missing import — check the `import { … } from "../lib/ui"` line |

## ➡️ Next

Workshop 03 — make a virtual serial cable and the fake device.

<sub>[← Workshop list](README.md)</sub>
