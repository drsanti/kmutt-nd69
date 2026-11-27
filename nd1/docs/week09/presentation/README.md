# ND01 Week 09 — Seeing the Signal: Presentation

85 interactive slides covering signal visualization, time/frequency analysis (FFT/DFT), LCD drawing, RGB565 graphics, sweep charts, and Edge AI CNN gesture quantisation for Week 09.

---

## How to Run

### 1. Standalone Offline HTML (Any OS / Browser)
- Download and double-click [`dist/week09-presentation.html`](dist/week09-presentation.html) or [`index.html`](index.html).
- **100% Offline**: All 85 slides, simulation models, styles, and four accelerometer CSV datasets are self-contained in a single file. No internet connection, server, Python runtime, or npm install required.
- Works offline in Chrome, Edge, Safari, Firefox, or Brave.

### 2. Standalone Windows Desktop App
- Download and run [`dist/ND01-Week09-Seeing-the-Signal-win_x64.exe`](dist/ND01-Week09-Seeing-the-Signal-win_x64.exe).
- Runs in a native borderless window with macOS-style window controls, titlebar dragging, maximize/restore, and rounded corners.

### 3. Desktop Progressive Web App (PWA)
- Serve this folder with any local static HTTP server (e.g. `python -m http.server 8000`).
- Open `http://localhost:8000` in Chrome, Edge, or Brave.
- Click the **"Install App"** button in the titlebar to install as a standalone desktop application.

---

## Navigation & Controls

| Action | Control |
|---|---|
| Next slide | **→** / **↓** / **Page Down** / **Space** / **⟩** in titlebar |
| Previous slide | **←** / **↑** / **Page Up** / **⟨** in titlebar |
| First / Last slide | **Home** / **End** |
| All 85 slides overview | **O** key / **All slides** button |
| Jump to chapter | Chapter dropdown menu in titlebar |
| Fullscreen | **F** key / **Fullscreen** button / Green traffic light |
| Dark / Light theme | **Theme** button |
| Print reference | **Print** button (generates 85-page static text reference) |
| Shortcuts help | **?** key / **?** button |

---

## Teaching Route

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

---

## Interactive Simulations

- **Signals & Aliasing**: Live frequency sweeps, sample folding across Nyquist limits, and interactive DFT spectrum displays.
- **Sensor Data Explorer**: Real datasets from `labs/python/samples/` (`idle`, `shake`, `circle`, `lift`) with dynamic magnitude and frequency plots.
- **LCD Display Geometry**: Live RGB565 bit-packing previews, dirty rectangle budget calculators, and interactive bubble level.
- **Edge AI Decision Engine**: CNN class probability threshold sliders, live gesture prediction rules, and dynamic confusion matrix calculators.
