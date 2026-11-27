/**
 * Lab 9.2 - Frequency domain: the spectrum of a motion, and what the gesture model sees.
 *
 * Takes one 2 s window (100 samples at 50 Hz) per gesture, computes the magnitude spectrum of
 * |a|, finds the dominant frequency, and shows the normalised 100 x 6 window the model gets.
 *
 *   npx tsx lab9_2_frequency.ts                         # the 4 sample gestures in samples/
 *   npx tsx lab9_2_frequency.ts --replay ../service/imu_dataset/shake/s01_me_ws28p_0000.csv   # your own take
 */
import { basename } from "node:path";

import * as rk from "robotos-board";
import { intro, parseArgs, replayFiles, run } from "./lab_common.ts";

const { rfft, abs, mean, argmax } = rk.dsp;
const FS = 50;                                         // sample rate (Hz)
const USAGE = "npx tsx lab9_2_frequency.ts [--replay file.csv ...]";

/** Return the frequency (Hz) and magnitude of every FFT bin of one window of |a| samples. */
function spectrum(aMag: number[]): { freqs: number[]; mag: number[] } {
  // TODO 1: remove the mean (gravity, 0 Hz) from the window, then take the magnitude of the FFT: rfft(centered).map(abs)
  const mag = new Array(Math.floor(aMag.length / 2) + 1).fill(0);
  // TODO 2: the frequency of bin k is k * FS / N (N = number of samples); the last bin must be FS / 2 (Nyquist)
  const freqs = mag.map((_, k) => k);
  return { freqs, mag };
}

run(async () => {
  const args = parseArgs(USAGE);
  intro(args, {
    "do": "Nothing to do: it analyses the 4 recordings in samples/ (or the files after --replay) and opens a page of plots in your browser.",
    look: "The dominant frequency of each gesture (printed, and a red dashed line in the plot): shake peaks near 11.5 Hz. The heat maps at the bottom are exactly what the gesture model receives (100 samples x 6 channels).",
    before: "every dominant frequency is 0.00 Hz and the spectra are flat (TODO 1), and the axis is wrong: resolution 1.00 Hz, Nyquist 50.0 Hz instead of 0.50 and 25.0 (TODO 2).",
  });
  if (args.replay === null) args.replay = [];
  const files = replayFiles(args);
  const fig = new rk.Figure("Lab 9.2 - spectrum of |a| (top) and the model's normalised 100 x 6 window (bottom)", { columns: files.length });
  const heat: { name: string; rows: number[][] }[] = [];
  for (const f of files) {
    const win = rk.loadCsv(f).slice(0, rk.WINDOW);
    const aMag = win.map((s) => s.aMag);
    const { freqs, mag } = spectrum(aMag);
    // TODO 3: the dominant frequency in Hz: the bin with the largest magnitude, ignoring bin 0 (leftover DC)
    const peakHz = 0;
    const name = basename(f, ".csv");
    console.log(`${name.padEnd(8)} dominant ${peakHz.toFixed(2).padStart(5)} Hz   resolution ${freqs[1].toFixed(2)} Hz   Nyquist ${freqs[freqs.length - 1].toFixed(1)} Hz`);
    fig.panel({ title: `${name}: peak ${peakHz.toFixed(1)} Hz`, xlabel: "Hz" }).line(freqs, mag).vline(peakHz);
    const norm = rk.normalise(win);                    // rows = samples, columns = channels
    heat.push({ name, rows: rk.CHANNELS.map((_, c) => norm.map((row) => row[c])) });
  }
  for (const h of heat) fig.panel({ title: `${h.name}: model input`, xlabel: "sample" }).heatmap(h.rows, { rowLabels: [...rk.CHANNELS], vmin: -2, vmax: 2 });
  await fig.save("lab9_2_frequency.html");
});
