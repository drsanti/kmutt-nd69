# Week 09 Mini Challenge — One signal, two screens

![track](https://img.shields.io/badge/track-ND02-1d4ed8?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-challenge-2e8b57?style=flat-square)

[Week 09 index](README.md)

> **Optional.** Try it during the session or afterwards, at your own pace. Nothing is handed in or scored; it is a way to practise what the labs showed.

Build a small **device gateway** in Node.js. It reads the board once and shows the same live data in two places:

1. **On the device:** one page that an operator can read at a glance. Show at least a live signal (strip chart or meter), the model's current decision, and a status that changes colour (OK / warning / alarm).
2. **In a browser:** a web page served by your gateway (e.g. `node:http` or Express, plus WebSocket or Server-Sent Events). It shows the same values, updated live, with a richer chart than the device can draw.

## Goals

- **Only the gateway opens the serial port.** The browser gets its data from the gateway, never from the board directly.
- Board page: stay inside the body area (y 46–221), **no flicker** (only changed parts are redrawn), at least **8 screen updates per second** with live data. Print `d.stats` at the end.
- One action works from **both** screens: a tap on the device or a button in the browser changes the detection threshold (or resets the counters), and both screens show the new value.
- The model stays in `gesture_service.py`; your gateway is its client.

## Check your result

1. Draw the processes and the messages between them (serial frames, WebSocket messages, HTTP): it shows where each piece of data lives.
2. Measure it: screen updates per second, commands per update (`d.stats`), and `ImuStream.lost` over 60 s.
3. Open two browser tabs, then start a second gateway. What breaks, and how could your design handle it?
4. Want to share it? A short video of the board and the browser side by side while you move the board shows it best.

**Advanced:** record 10 s of samples from the browser with a "record" button, save them as a CSV in the `samples/` format, and feed them back with `--replay`.
