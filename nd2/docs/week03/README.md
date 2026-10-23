# ND02 — Week 03: Browser Apps that Reach Hardware

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND02-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-03-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-index-2e8b57?style=flat-square)

Seven workshops build one browser app end to end: DOM control panel → Web Serial telemetry → commands → Web Bluetooth → a unified device dashboard. Everything runs on a laptop with simulated hardware — a Python fake device on a virtual serial pair, and a phone standing in as the BLE peripheral.

## Table of contents

- [Workshops](workshops/README.md)
- [The app project](workshops/week03-app/README.md)
- [Week 02](../week02/README.md)
- [Week 01](../week01/README.md)
- [Documents](../README.md)
- [Track index](../../README.md)

## Learning outcomes

- Explain why Web Serial and Web Bluetooth are Chromium-only, secure-context APIs.
- Build an event-driven dashboard UI in plain TypeScript — no framework.
- Set up a virtual serial port pair and connect a browser to it.
- Decode a line-framed JSON protocol with Web Streams (back-pressure aware).
- Send commands device-ward and verify them through the telemetry channel.
- Connect to a BLE peripheral and traverse the GATT service → characteristic → value tree.
- Manage the serial-port connect/disconnect lifecycle a real device app needs.

## What you need

- **Chrome or Edge** — the hardware APIs are Chromium-only; `localhost` is a secure context.
- **Vite+ (`vp`)** or any Node/npm — dev server and toolchain.
- **Python ≥ 3.10 + pyserial** — runs the fake device.
- **socat** (macOS/Linux) or **com0com** (Windows) — the virtual serial cable.
- **A smartphone with nRF Connect** — BLE peripheral for workshop 06.

No board this week — the ESP32-S3 arrives next week and speaks the same JSON-lines protocol the fake device uses.

Start with the [workshop list](workshops/README.md). The [project README](workshops/week03-app/README.md) is the daily reference for the app layout.
