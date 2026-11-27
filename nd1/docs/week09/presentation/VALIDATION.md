# Observed validation — 27 November 2026

Test environment: Windows, Python 3.11.9, Node 24.19.0, Playwright 1.65.1 using installed Chrome 158.0.8127.38 in headless mode. The presentation requires none of those authoring tools to open.

## Content and numerical checks

- Exactly 85 slides across chapters of 5, 10, 12, 14, 13, 12, 15 and 4 slides; every slide has instructor notes.
- Course sources pinned to `371bceed0ebe8034124a87889b9f11e716d58de9`; SHA-256 assertions passed for all manifest files.
- SDK display batching, geometry, RGB565, chart mapping, normalisation and detector defaults were read at `bd695ce3018f670b574a2c4ddc2bdab43e4b5b85` in `drsanti/robotos`.
- Eight Node test groups passed: analytic sine/DC DFT, alias folds/phase, RGB565, preprocessing/clipping, overall argmax/idle/inclusive threshold/ties, confusion metrics/undefined precision, dirty-region repaint exceptions, slide count/notes and all embedded CSV values.
- `python build.py` generated both entry points. Repeated builds produced identical outputs. `git diff --check` passed for the staged files.

## Browser checks

- Opened `dist/week09-presentation.html` and `index.html` directly via `file://`, with browser networking disabled.
- Visited all 85 slides at 1440×1000 and 390×844; no horizontal overflow or JavaScript errors.
- Exercised visible range minimum/maximum values and every select option across all slides, plus quizzes.
- Checked sample-period readout, 40 Hz at 50 Hz alias readout, idle-dominant gesture rejection, tap threshold updates, Lab 9.2 command restrictions and unsafe command-text rejection.
- Checked code copying (including allowed fallback), arrows/Home/End, focused-slider key handling, overview selection, chapter jump, notes, themes, entering/exiting fullscreen and 85-slide print-reference preparation.
- No HTTP/HTTPS requests were made during the run. Source links were not clicked because they intentionally require internet.
- Representative screenshots cover signal/FFT, CSV, architecture, command builder, LCD, dirty rectangles, level, model and integration slides, plus narrow-screen, dark and print views. Visual review prompted a more compact desktop control layout and shorter geometry labels. Dense slides and mobile layouts support vertical scrolling.

## Limits

- No physical board, USB timing, firmware flash, SDK installation or Python lab/model training was exercised. No claim is made about Windows wheel correctness, hardware frame rate or real gesture accuracy.
- Browser plots use a direct DFT for clarity, while the Python lab uses NumPy's FFT implementation. Their transform convention/raw magnitude is equivalent; algorithmic speed differs.
- Synthetic CSVs are exact course data, not sensor measurements. Probability and confusion demonstrations use labelled illustrative scores, not model output.
- The LCD preview approximates geometry/font/rasterisation and forces body clipping. It does not emulate firmware, transport budgets, panel gamma or dropped packets.
- Only Chrome was executed. The dependency-free APIs are intended for modern browsers; Safari/Firefox and mobile devices were not separately run. Mobile validation used a narrow desktop browser viewport, not a real phone.
- Fullscreen, clipboard and browser printing remain browser-dependent. The print feature is a text reference with quiz answers and notes, not a verified PDF or frozen interactive slide export.
