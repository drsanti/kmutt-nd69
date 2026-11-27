# ND02 — Week 09: Seeing the Signal, from Node.js — Visualization for Edge AI

> **Before the practical:** do the [Setup](labs/README.md#1-setup-20-min) (Node.js 22+ and a Python 3.11 environment, about 20 minutes). Week 09 is self-contained: it needs nothing from earlier weeks.

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND02-1d4ed8?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-index-2e8b57?style=flat-square)

**Session:** Saturday 28 November 2026 · Online · 09:00–12:00  
**Topic:** *Visualizing sensor signals, features and model decisions with TypeScript — on the PC and on the device's own screen*  
**Board:** ws28p (IMU + touchscreen). No board, or an es3c28p? Every lab also runs with recorded motion (`--replay`).  
**Language:** TypeScript on Node.js 22+, run with `npx tsx`. The model service in Lab 9.5 is Python (FastAPI, as in Week 08).

Every stage of an Edge AI pipeline should be something you can **see**: the raw signal, its frequency content, what the model receives, what it decides, and how the device shows it to a person. This week you build those views from Node.js. First as plots in a web page, then live on the board's 320 × 240 touchscreen, drawn over USB with the `robotos-board` library. Finally you connect a Python model service and show its decisions on the device.

---

## Table of Contents

- [Labs Guide](labs/README.md)
- Lessons: [01 — Time and frequency](lessons/01-time-and-frequency.md) · [02 — Drawing on a device](lessons/02-drawing-on-a-device.md)
- [Checkpoint Quiz](checkpoint.md)
- [Mini Challenge](mini-challenge.md)
- Previous week: [Week 08](../week08/labs/README.md) · [Track Index](../README.md)

---

## Learning Outcomes

- **Read a sensor signal in the time domain:** units, gravity, noise, sample rate and lost samples of a 50 Hz IMU stream.
- **Read it in the frequency domain:** compute a spectrum with the FFT, explain frequency resolution and the 25 Hz Nyquist limit, and see the gesture model's 100 × 6 input window.
- **Drive a device from Node.js:** a binary serial protocol behind an async API, pages, pixel coordinates, RGB565 colour and the drawing budget of a small screen.
- **Update a display without flicker:** redraw only what changed (dirty rectangles) and measure the result.
- **Split a system into services:** stream samples over a WebSocket to a Python model service and show its decisions, with a threshold you tune by touch.

---

## Schedule (09:00–12:00)

| Time | Block | Topic | Lab |
| :--- | :--- | :--- | :--- |
| **09:00–09:20** | Setup | `npm install`, connect the board | [Setup](labs/README.md#1-setup-20-min) |
| **09:20–09:50** | Block 1 | Time domain: what the IMU really sends | [Lab 9.1](labs/README.md#lab-91--time-domain-30-min) |
| **09:50–10:20** | Block 2 | Frequency domain and the model's input | [Lab 9.2](labs/README.md#lab-92--frequency-domain-30-min) |
| **10:20–10:30** | Break | | |
| **10:30–11:00** | Block 3 | Drawing on the device: a live meter | [Lab 9.3](labs/README.md#lab-93--drawing-on-the-device-30-min) |
| **11:00–11:30** | Block 4 | Live charts and a bubble level | [Lab 9.4](labs/README.md#lab-94--live-charts-on-the-device-30-min) |
| **11:30–12:00** | Block 5 | A model service and its decisions | [Lab 9.5](labs/README.md#lab-95--seeing-the-model-30-min) |

---

## How the labs work

Each lab is one short TypeScript file in `labs/node/` with **three `// TODO` tasks**. Every file already runs before you change anything. Until you complete the TODOs, the plot or screen just shows zeros, a flicker or a trail. Work through them in order; each TODO says exactly what to compute or draw.

```bash
cd nd2/docs/week09/labs/node
npm install                                   # once
npx tsx lab9_1_time_domain.ts --replay        # no board: recorded motion
npx tsx lab9_1_time_domain.ts                 # ws28p connected: live
```
