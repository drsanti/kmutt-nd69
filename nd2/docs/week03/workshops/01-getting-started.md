# Workshop 01 — Getting started: the Vite+ environment

> **Goal:** install the toolchain, get `week03-app` running in the
> browser, and verify your browser can actually reach hardware APIs.

**Requirements:** one computer, Chrome or Edge installed

---

## The stack you're building on

Every workshop this week runs inside one layered stack. Each
layer only talks to its neighbor — your workshop code never
touches the OS directly:

```
┌───────────────────────────────────────────────┐
│ workshop module   w01-w07  (picked by import) │
├───────────────────────────────────────────────┤
│ shared helpers    src/lib: ui, serial, proto  │
├───────────────────────────────────────────────┤
│ browser APIs      Web Serial and Bluetooth    │
├───────────────────────────────────────────────┤
│ Chromium browser  secure context: localhost   │
├───────────────────────────────────────────────┤
│ OS drivers        serial port and BLE radio   │
└───────────────────┬───────────────────────────┘
                    │
            ┌───────┴─────────┐
            │ device          │
            │ real board or   │
            │ fake_device.py  │
            └─────────────────┘
```

This layering is the whole design lesson of the week: the browser
API is a **capability boundary**, not just a function call. The OS
drivers and the hardware sit below it — everything you write stays
inside the sandbox and asks permission through the API.

## Why Chromium only

`navigator.serial` and `navigator.bluetooth` are Chromium
implementations of web-platform hardware APIs. Safari and Firefox
have deliberately not shipped them — the APIs grant web pages raw
access to devices, and the other vendors consider the security
model unsettled. This is worth understanding rather than
memorizing: **the browser is the gatekeeper of your hardware**.
When it refuses, nothing below it is reachable from the page.

`localhost` is special-cased as a *secure context* — the browser
treats it as trustworthy because traffic can't leave your machine.
That's why plain `http://localhost:5173` unlocks hardware APIs
while `http://192.168.x.x` would not.

---

## Step 1 — Install Vite+

One command per platform — `vp` manages the Node runtime and
package manager for you:

```bash
# macOS / Linux
curl -fsSL https://vite.plus | bash

# Windows (PowerShell — not Git Bash)
irm https://vite.plus/ps1 | iex
```

Open a **new** terminal, then verify:

```bash
vp --version
```

> [!NOTE]
> Vite+ is the unified toolchain — one CLI covering dev server,
> build, test, lint, and format. If you already have Node.js +
> npm installed, plain `npm`/`npx vite` works too; the workshops
> show `vp` commands since that's the modern default.

## Step 2 — Get the app running

The project is already scaffolded — `week03-app/` in this folder:

```bash
cd week03-app
vp install          # or: npm install
vp dev              # or: npm run dev
```

Open `http://localhost:5173` — you should see a dark control
panel (that's workshop 02's UI, the default import).

> [!IMPORTANT]
> Use **Chrome or Edge**. Web Serial and Web Bluetooth are
> Chromium-only — Safari and Firefox will load the page but the
> connect buttons will fail. `localhost` counts as a secure
> context, so no HTTPS is needed for development.

## Step 3 — Run the environment check

Switch to workshop 01's module — open `src/main.ts`:

```ts
import { run } from "./workshops/w01_env_check";   // ← uncomment this
// import { run } from "./workshops/w02_dom_basics";
run();
```

Save — Vite+ hot-reloads instantly. What just happened, in time
order:

```
you              terminal          Vite+ dev server      browser
 |                   |                    |                  |
 |- vp dev --------->|-- spawn ---------->|                  |
 |                   |                    |- serve app ----->|
 |                   |                    |                  |- run
 |- edit main.ts --->|                    |                  |  module
 |                   |-- fs change ------>|- HMR update ---->|
 |                   |                    |                  |- rerun
 |                   |                    |                  |  module
```

**HMR (hot module replacement)** swaps the changed module without
a full page reload — that's why switching workshops feels instant.
The browser re-executes the new module's `run()` the moment the
file lands on disk.

The page now reports, live:

- **Web Serial** — present?
- **Web Bluetooth** — present?
- **Secure context** — yes on `localhost`
- **Streams API** — yes on modern browsers

All green → your environment is ready for the week.

## Step 4 — Understand the project layout

```
week03-app/
+-- src/main.ts        <- the workshop selector (one import)
+-- src/styles.css     <- shared theme — no per-workshop CSS
+-- src/workshops/     <- one file per workshop: w01..w07
+-- src/lib/           <- shared helpers: serial, protocol, ui
+-- device/            <- fake_device.py (the board stand-in)
```

## ✅ Checkpoint

- [ ] `vp --version` (or `npm --version`) works in a fresh terminal
- [ ] `vp dev` serves the app on `http://localhost:5173`
- [ ] The env-check module reports all four capabilities green
- [ ] Editing `main.ts` hot-swaps the page without a manual reload

## 🔧 Troubleshooting

| Symptom | Try |
|---|---|
| `vp: command not found` | open a **new** terminal — the installer adds PATH for new sessions |
| Page loads but capabilities are red | wrong browser — Web Serial/Bluetooth need Chrome or Edge |
| `localhost:5173` refuses | dev server not running, or another app holds the port — check the terminal |

## ➡️ Next

Workshop 02 — build the dashboard UI itself, no device required.

<sub>[← Workshop list](README.md)</sub>
