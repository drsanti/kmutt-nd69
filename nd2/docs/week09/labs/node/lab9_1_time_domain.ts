/**
 * Lab 9.1 - Time domain: what does the IMU really send?
 *
 * Records a few seconds of 6-axis IMU data (live from a ws28p, or --replay), prints basic signal
 * statistics, and writes an HTML page with the accelerometer, |a| and gyroscope plots.
 *
 *   npx tsx lab9_1_time_domain.ts --replay          # no board
 *   npx tsx lab9_1_time_domain.ts --seconds 10      # live ws28p, auto-detected port
 */
import * as rk from "robotos-board";
import { imuSource, intro, parseArgs, replayFiles, run } from "./lab_common.ts";

const { mean, median, diff, std } = rk.dsp;
const USAGE = "npx tsx lab9_1_time_domain.ts [--replay [file.csv ...]] [--seconds N] [--port PATH]";

async function record(args: ReturnType<typeof parseArgs>): Promise<{ samples: rk.Sample[]; lost: number }> {
  const want = Math.round(args.seconds * rk.RATE_HZ);
  if (args.replay !== null) {                          // replay: no need to wait in real time
    const all = replayFiles(args).flatMap((f) => rk.loadCsv(f));
    const samples = Array.from({ length: want }, (_, i) => {   // repeat the files if --seconds asks for more
      const s = all[i % all.length];
      return new rk.Sample(i / rk.RATE_HZ, s.ax, s.ay, s.az, s.gx, s.gy, s.gz);
    });
    return { samples, lost: 0 };
  }
  const session = await rk.connect({ port: args.port, needCap: rk.CAP_IMU });
  try {
    const stream = imuSource(args, session);
    console.log(`Recording ${args.seconds} s - move the board around, then hold it still.`);
    const samples: rk.Sample[] = [];
    for await (const s of stream) {
      samples.push(s);
      if (samples.length >= want) break;
    }
    return { samples, lost: stream.lost };
  } finally {
    await session.close();
  }
}

run(async () => {
  const args = parseArgs(USAGE, { seconds: 8 });
  intro(args, {
    live: "Move the board around for a few seconds, then hold it still until recording ends (8 s; change with --seconds). A page of plots opens in your browser at the end.",
    replay: "Nothing to do: the recorded idle, shake, circle and lift motions are used. A page of plots opens in your browser at the end.",
    look: "|a| stays near 9.81 m/s^2 when the board is still, whatever its tilt; during a lift it dips below, then rises above. The script prints the sample rate, lost samples and the axis along gravity.",
    before: "|a| is all zeros (TODO 1), the rate prints 0.0 Hz (TODO 2) and the axis along gravity always says x (TODO 3).",
  });
  const { samples, lost } = await record(args);
  const t = samples.map((s) => s.t);
  const axes = [samples.map((s) => s.ax), samples.map((s) => s.ay), samples.map((s) => s.az)];

  // TODO 1: compute |a| = sqrt(ax² + ay² + az²) for every sample (an array of N numbers)
  const aMag = samples.map(() => 0);

  // TODO 2: estimate the sample rate in Hz from the timestamps t (hint: the median time between two samples)
  const rateHz = 0;

  // TODO 3: which axis (0 = x, 1 = y, 2 = z) points along gravity? Compare the mean of each accel axis in axes (absolute value)
  const upAxis = 0;

  const still = samples.slice(0, 50);                 // the first second
  const noise = ["ax", "ay", "az"].map((k) => std(still.map((s) => s[k as "ax"])).toFixed(3));
  console.log(`samples: ${samples.length}  duration: ${(t[t.length - 1] - t[0]).toFixed(2)} s  rate: ${rateHz.toFixed(1)} Hz  lost: ${lost}`);
  console.log(`|a| mean ${mean(aMag).toFixed(2)} m/s^2 (gravity = ${rk.G.toFixed(2)})   min ${Math.min(...aMag).toFixed(2)}   max ${Math.max(...aMag).toFixed(2)}`);
  console.log(`axis along gravity: ${"xyz"[upAxis]}   accel noise (std, first 1 s): x ${noise[0]}  y ${noise[1]}  z ${noise[2]}`);

  const fig = new rk.Figure(`Lab 9.1 - ${samples.length} samples at ${rateHz.toFixed(1)} Hz, ${lost} lost`);
  const acc = fig.panel({ title: "accelerometer", ylabel: "m/s^2" });
  ["x", "y", "z"].forEach((k, i) => acc.line(t, axes[i], { label: k }));
  fig.panel({ title: "|a|", ylabel: "m/s^2" }).line(t, aMag, { color: "currentColor", label: "|a|" }).hline(rk.G, { label: "1 g" });
  const gyr = fig.panel({ title: "gyroscope", ylabel: "rad/s", xlabel: "time (s)" });
  (["gx", "gy", "gz"] as const).forEach((k) => gyr.line(t, samples.map((s) => s[k]), { label: k }));
  await fig.save("lab9_1_time_domain.html");
});
