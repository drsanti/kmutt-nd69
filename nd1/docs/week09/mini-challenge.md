# Week 09 Mini Challenge — A device dashboard on a budget

![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-challenge-2e8b57?style=flat-square)

[Week 09 index](README.md)

> **Optional.** Try it during the session or afterwards, at your own pace. Nothing is handed in or scored; it is a way to practise what the labs showed.

Design **one page** for the ws28p screen that an operator could read at a glance while the board is mounted on a machine or a robot. Combine at least **three** views from the labs or your own:

- a live signal (strip chart of one or more axes, or a scrolling |a|)
- a derived value (vibration level, dominant frequency from Lab 9.2, tilt angle in degrees)
- the model's decision (current gesture, confidence, detection count)
- a status element that changes colour (OK / warning / alarm)

## Goals

- Stay inside the body area (y 46–221) and keep the firmware's title, tabs and footer.
- **No flicker:** only changed parts are redrawn.
- **Budget:** at least **8 screen updates per second** with live data. Print `d.stats` at the end to see the number of commands per update.
- One tap action (e.g. reset counters, change the threshold or the chart range).

## Check your result

1. Sketch the layout with pixel coordinates before you code it: it saves a lot of trial and error.
2. Measure it: updates per second, commands per update (`d.stats`), and `ImuStream.lost` over 60 s.
3. Ask yourself which design choice saved the most drawing time, and why.
4. Want to share it? A photo or short video of the screen is a nice way to show the group.

**Advanced:** draw the same page from ESP-IDF firmware on the board itself (no PC), and compare frame time and USB use.
