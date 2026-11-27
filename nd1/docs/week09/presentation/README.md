# ND01 Week 09 — Seeing the Signal

85 English interactive HTML slides for the five Week 09 labs. The presentation uses plain HTML, CSS and JavaScript, with no runtime packages, CDN, analytics, fonts, fetch calls, Python runtime or hardware connection.

## Open

Download [`dist/week09-presentation.html`](dist/week09-presentation.html) and double-click it. This **single file** includes the slides, components, styles and all four CSV datasets. It runs with the network disconnected in a modern browser. GitHub's file viewer displays source; download the raw HTML to present it.

Alternatively, open [`index.html`](index.html) from a full checkout. It loads local scripts and CSS with ordinary script tags and also works through `file://`; no local server is required. Keep its companion folders beside it.

Use arrows, Page Up/Down or Space to move; Home/End to jump; **F** for fullscreen, **O** for all slides, **N** for instructor notes and **?** for help. Form controls retain their keyboard behavior. The chapter menu jumps to a lab; URL fragments such as `#slide-36` can bookmark a slide. All features also have visible controls. Fullscreen and clipboard support depend on browser permissions; a selectable text fallback appears if copying is denied.

The layout stacks on narrow screens. Dense demonstrations can scroll vertically; navigation remains available at the end. Theme switches light/dark. Print produces an 85-page static **text reference**, including instructor notes and quiz answers. It does not freeze interactive plots or produce a tested PDF artifact.

### Desktop Progressive Web App (PWA)

To run the presentation in a distraction-free, dedicated desktop app window:
1. Serve the presentation folder with any local static HTTP server (e.g., `python -m http.server 8000` or GitHub Pages).
2. Open `http://localhost:8000` in Chrome, Edge, or Brave.
3. Click the **"Install App"** button in the top navigation bar (or the install icon in the browser address bar).
4. The presentation installs as a native desktop app with offline caching via Service Worker (`sw.js`), desktop app icons, and right-click desktop shortcuts jumping directly to Labs 9.1–9.5.

## Teaching route

| Chapter | Slides | Focus |
|---|---:|---|
| Introduction | 1–5 | System architecture, source and execution boundaries |
| Setup & CLI | 6–15 | Environment, pip, CLI, firmware, replay and model preparation |
| Lab 9.1 | 16–27 | SI units, gravity, array shapes, sampling and sample loss |
| Lab 9.2 | 28–41 | Waveforms, numerical transform, DC, bins, aliasing and model input |
| Lab 9.3 | 42–54 | Screen ownership, SDK calls, RGB565, budgets and dirty rectangles |
| Lab 9.4 | 55–66 | Sweep chart, sample/display clocks, level and measurement |
| Lab 9.5 | 67–81 | CNN input, training data, quantisation, scores and metrics |
| Integration | 82–85 | Optional dashboard challenge and evidence-based explanation |

Reference slides are labelled and can be skipped during live teaching. See [`INSTRUCTOR.md`](INSTRUCTOR.md) for the three-hour route, prompts and answers. Notes are embedded in every slide. The original lab scripts remain complete and unchanged; optional exercises stay in their original separate folder.

## Simulations and provenance

| Component | What actually runs |
|---|---|
| Signal, sampling, aliasing | Generated arrays; original curve, sample dots and a signed alias curve matching sample times |
| Spectrum | A direct numerical DFT, mathematically the same transform as the lab's FFT, using raw magnitudes; no fabricated peak bars |
| CSV and tensor explorer | Exact numerical values from `labs/python/samples/{idle,shake,circle,lift}.csv`; computed magnitude, spectrum and fixed-scale input heatmap |
| IMU | One-axis static tilt plus added z acceleration; no sensor fusion or gyro estimation |
| Display | Parameter-driven SDK geometry preview with copyable Python; body-only preview clipping and approximate font/rasterisation |
| RGB565 | SDK-compatible bit masks and an expanded RGB preview; panel gamma is not emulated |
| Dirty rectangles | Stateful previous/new widths and colours; changed pixel area and bar-operation count, **not USB bytes** |
| Strip chart | Synthetic 50 Hz input, fixed-width column buffer, sweep/wrap and adjustable pixels/sample; browser timing is illustrative |
| Bubble level | Actual lab's independent axis clipping, plus an explicitly labelled optional radial-limit extension |
| Gesture bars | Adjustable invented scores normalised to sum 1; overall argmax, idle rejection and inclusive threshold comparison |
| Confusion metrics | Recomputed TP/FP/FN/TN and ratios on 16 fixed invented labelled trials; undefined precision displays n/a |
| Command builder | Generates terminal text only; Lab 9.2 is constrained to file analysis and irrelevant duration/port options are disabled |

The bundled CSVs are **synthetic**, although older script comments sometimes call them “recorded.” Plotting the actual files does not turn them into measured sensor data. Neither the probability simulation nor the confusion matrix runs or evaluates `model_int8.tflite`. Gesture highlights do not simulate the detector's warm-up, smoothing or refractory event counter; those behaviors are explained separately from the SDK implementation.

The **host** performs FFT, preprocessing, model inference and UI logic in the current labs. The **MCU** acquires sensor data, applies drawing commands and reports touch events. Replay replaces acquisition; Labs 9.3–9.5 still need a physical screen board. A standalone browser cannot run the terminal commands, install packages, train the lab model or flash a board. Those actions require the lab environment; firmware downloads and first-time dependency installs need internet.

[`assets/source-manifest.json`](assets/source-manifest.json) records the pinned course commit, SHA-256 of each source and the inspected SDK commit/paths. Slide links use the pinned course commit. Sources include the Week 09 index, labs README, both lessons, checkpoint, mini challenge, common helpers, five demos, requirements and four CSVs. SDK explanations were checked in `drsanti/robotos` at the manifest's commit, specifically display batching/geometry, fixed-scale normalisation and gesture decision/timing defaults. SDK source is **not** copied into this curriculum package.

The inspected course revision contains CPython 3.11 Windows x64 and Apple Silicon macOS 0.2.2 wheels. Their presence does not establish that they install or run correctly; SDK/hardware validation is outside this presentation test. No Linux wheel is bundled.

## Edit and rebuild

- `slides/00.json` … `07.json`: chapter content, code, widget selection, quiz and instructor notes.
- `components/core.js`: reusable numerical/DOM helpers and widget registry.
- `components/signals.js`: signal, sampling, DFT, aliasing, CSV/tensor and IMU components.
- `components/display.js`: LCD geometry, RGB565, dirty rectangles, chart and bubble.
- `components/decisions.js`: gesture/metrics, command builder and architecture explorer.
- `components/presentation.js`: navigation, mount/cleanup lifecycle, copying, quizzes and print reference.
- `styles/presentation.css`: responsive layouts, themes and print styles.
- `template.html`: presentation shell.

From this directory, run `python build.py` using Python 3.11 or newer. No Python packages are required. Commit the generated `assets/content.js`, `index.html` and `dist/week09-presentation.html` with source changes. The build is deterministic and refuses to proceed if a source hash changed: review affected content and deliberately update the manifest. Do not edit generated files directly. JavaScript sources use a shared `W09` registry so they can be reused without a bundler; a widget receives its root and kind and may return a cleanup callback.

## Verification

```text
python build.py
node --test tests/numerics.test.cjs
npm ci
npx playwright install chromium
npm run test:browser
```

Python and Node are author/test tools only. The browser suite needs Node 20+ and Playwright; it opens both file entry points **offline**, exercises all 85 slides and all widget range boundaries/select options, checks navigation/copy/quiz/fullscreen/print preparation, and checks every slide at 1440×1000 and 390×844 for horizontal overflow and JavaScript errors. It writes representative screenshots and `results.json` to a temporary folder; set `W09_QA_DIR` to override it. An existing Chrome can be used with `W09_BROWSER_CHANNEL=chrome`. Do not commit test dependencies or screenshots.

Numerical tests cover analytic sine/DC spectra, alias folds and phase consistency, RGB565, fixed scaling, threshold equality/idle handling, confusion ratios, dirty-region exceptions, slide counts/notes and every embedded CSV value. See [`VALIDATION.md`](VALIDATION.md) for the observed run and its limits.
