/** Shared helpers for the Week 09 labs: command-line flags, live board or recorded IMU files, clean exit. */
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import * as rk from "robotos-board";

export const HERE = dirname(fileURLToPath(import.meta.url));
export const SAMPLES = join(HERE, "samples");
const ORDER = ["idle", "shake", "circle", "lift"];

export interface Args { port?: string; replay: string[] | null; seconds: number }

/** --port PATH, --replay [file.csv ...], --seconds N (and --help). */
export function parseArgs(usage: string, defaults: { seconds?: number } = {}): Args {
  const argv = process.argv.slice(2);
  const args: Args = { replay: null, seconds: defaults.seconds ?? 60 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") { console.log(usage); process.exit(0); }
    else if (a === "--port") args.port = argv[++i];
    else if (a === "--seconds") args.seconds = Number(argv[++i]);
    else if (a === "--replay") {
      args.replay = [];
      while (i + 1 < argv.length && !argv[i + 1].startsWith("--")) args.replay.push(argv[++i]);
    } else { console.error(`unknown option ${a}\n\n${usage}`); process.exit(2); }
  }
  return args;
}

/** The CSV files to replay: the ones given after --replay, or all of samples/ (idle first). */
export function replayFiles(args: Args): string[] {
  if (args.replay?.length) return args.replay;
  const rank = (f: string) => { const i = ORDER.indexOf(basename(f, ".csv")); return i < 0 ? 9 : i; };
  const found = existsSync(SAMPLES) ? readdirSync(SAMPLES).filter((f) => f.endsWith(".csv")).map((f) => join(SAMPLES, f)) : [];
  if (!found.length) throw new Error(`no CSV files in ${SAMPLES}`);
  return found.sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
}

/** Live samples from the board (a ws28p) or, with --replay, recorded files (looped). */
export function imuSource(args: Args, session?: rk.BoardSession): rk.ImuSource {
  if (args.replay !== null) {
    const files = replayFiles(args);
    console.log("IMU source: replay of", files.map((f) => basename(f)).join(", "));
    return new rk.ImuReplay(files, { loop: true });
  }
  if (!session) throw new Error("live IMU needs a board session");
  console.log("IMU source: live board");
  return new rk.ImuStream(session);
}

const cleanups: (() => Promise<void> | void)[] = [];
/** Run `fn` on Ctrl+C or when the lab ends (e.g. close the screen page). */
export function onExit(fn: () => Promise<void> | void): void { cleanups.push(fn); }

async function cleanup(): Promise<void> {
  while (cleanups.length) {
    try { await cleanups.pop()!(); } catch { /* keep going */ }
  }
}

/** Run a lab's main(): Ctrl+C stops it cleanly, and errors print as one short message. */
export function run(main: () => Promise<void>): void {
  process.on("SIGINT", () => { console.log("\nstopped"); cleanup().finally(() => process.exit(130)); });
  main().then(cleanup, async (e: unknown) => {
    console.error(`\nerror: ${e instanceof Error ? e.message : String(e)}`);
    await cleanup();
    process.exit(1);
  });
}

// ---------------------------------------------------------------- start-up guide
const WIDTH = 78;

function wrap(text: string, first: string, rest: string): string[] {
  const out: string[] = [];
  let line = first;
  for (const word of text.split(/\s+/).filter(Boolean)) {
    if (line.length + word.length + 1 > WIDTH - 1 && line.trim() !== first.trim()) { out.push(line.trimEnd()); line = rest; }
    line += (line === first || line === rest ? "" : " ") + word;
  }
  out.push(line.trimEnd());
  return out;
}

export interface Guide { live?: string; replay?: string; do?: string; look?: string; before?: string }

/** Print what this lab is (from the comment at the top of the lab file), what it does, what to
 *  do now (live board or --replay), what to look for, and the TODO tasks in the file. */
export function intro(args: Args | null, g: Guide): void {
  const file = process.argv[1] ?? "";
  let src = "";
  try { src = readFileSync(file, "utf8"); } catch { /* no file: skip the details */ }
  const head = /\/\*\*([\s\S]*?)\*\//.exec(src)?.[1] ?? "";
  const paras = head.split("\n").map((l) => l.replace(/^\s*\* ?/, "")).join("\n").trim().split(/\n\s*\n/);
  const title = (paras[0] ?? basename(file)).split("\n")[0];
  const what = (paras[1] ?? "").replace(/\s+/g, " ").trim();
  const replay = args?.replay !== null && args?.replay !== undefined;
  const lines: string[] = [];
  if (what) lines.push(...wrap(what, " What it does: ", " ".repeat(15)));
  if (g.live || g.replay) {
    lines.push(...wrap(replay ? "recorded motion (--replay)" : "live board  - no ws28p? run it again with --replay", " Mode:         ", " ".repeat(15)));
    lines.push(...wrap((replay ? g.replay : g.live) ?? "", " Do now:       ", " ".repeat(15)));
  } else if (g.do) lines.push(...wrap(g.do, " Do now:       ", " ".repeat(15)));
  if (g.look) lines.push(...wrap(g.look, " Look for:     ", " ".repeat(15)));
  if (g.before) lines.push(...wrap(g.before, " Before TODOs: ", " ".repeat(15)));
  const todos = [...src.matchAll(/^\s*\/\/\s*(?:>>> )?(?:TODO|Step) (\d+): (.*?)(?: \| starter: .*)?$/gm)];
  const demo = !src.includes("TODO");
  if (todos.length) {
    lines.push(demo ? " Key steps in the code:" : " Your tasks (TODOs in this file):");
    for (const m of todos) lines.push(...wrap(m[2].split(/(?<=[a-z0-9)]): |; |\. /)[0].replace(/\.$/, ""), `   ${demo ? "Step" : "TODO"} ${m[1]}: `, " ".repeat(11)));
  }
  lines.push(` Stop: Ctrl+C    Options: npx tsx ${basename(file)} --help`);
  console.log(`${"=".repeat(WIDTH)}\n ${title}\n${"=".repeat(WIDTH)}\n${lines.join("\n")}\n${"-".repeat(WIDTH)}`);
}
