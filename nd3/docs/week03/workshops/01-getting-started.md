# Workshop 01 — Getting started: install and see the graph

> **Goal:** install robotos on your machine and open the inspector
> to see a live graph — before writing a single line of code.

**Requirements:** one computer, no network needed, no compiler

---

## What you're installing — one binary, three faces

Everything this week runs on a single concept: a **graph** that
nodes join and leave. The CLI, the inspector, and your Python
scripts are all citizens of the same graph:

```
┌──────────────────────────────────────────────────────────┐
│                    robotos graph                         │
│         (nodes, topics — discovered automatically)       │
│                                                          │
│   ┌──────────┐    ┌────────────┐    ┌────────────────┐   │
│   │ example  │    │ your Python│    │ robotos CLI    │   │
│   │ nodes    │    │ nodes      │    │ (node/topic/..)│   │
│   └──────────┘    └────────────┘    └───────┬────────┘   │
│                                             │ serves     │
│                                     ┌───────┬────────┐   │
│                                     │ inspector UI   │   │
│                                     │ 127.0.0.1:4789 │   │
│                                     └────────────────┘   │
└──────────────────────────────────────────────────────────┘
                    all on one machine — no server
```

Key difference from what you may expect: **there is no broker to
start**. Nodes discover each other through the transport
(multicast on your LAN, or loopback) — you don't launch "the
server" and then connect clients. The inspector watches the same
graph your code does; `topic echo` taps the same messages a
subscriber would.

## Step 1 — Locate the package

The robotos package is included in this repository — no download
needed. Open the `code/` folder and find the directory matching
your platform:

```
code/
+-- robotos-v<ver>-macos-arm64/     <- macOS Apple Silicon
+-- robotos-v<ver>-windows-x64/     <- Windows 64-bit
+-- robotos-v<ver>-linux-x64/       <- Linux 64-bit
        +-- bin/robotos[.exe]     <- the CLI — one binary does everything
        +-- lib/librobotos_ffi.*  <- shared library used by every SDK
        |                           (.dylib / .so / .dll per platform)
        +-- include/              <- headers (not needed this week)
```

Open the folder matching **your** platform — the file names differ
slightly per OS (`librobotos_ffi.dylib` on macOS, `.so` on Linux,
`.dll` on Windows) but everything works the same way.

## Step 2 — Make `robotos` runnable

You need a way to run the CLI — pick one of three options:

### macOS / Linux

**Option A — run it in place** (zero setup, good for a first try):

```bash
cd code/robotos-v0.3.0-macos-arm64     # or -linux-x64
./bin/robotos version
```

The `./` tells the shell "run the program *in this folder*" —
without it, `robotos version` fails because the shell only
searches folders listed in `PATH`.

**Option B — temporary PATH** (works until you close the terminal):

```bash
cd code/robotos-v0.3.0-macos-arm64     # run FROM INSIDE the folder — $PWD = "here"
export PATH="$PWD/bin:$PATH"
robotos version                        # works without ./
```

`$PWD` expands once to the package's absolute path — it stays valid
even after you `cd` elsewhere, but only until this terminal closes.

**Option C — permanent PATH** (survives new terminals — recommended):

```bash
cd code/robotos-v0.3.0-macos-arm64     # run FROM INSIDE the folder
echo 'export PATH="$PWD/bin:$PATH"' >> ~/.zshrc    # Linux: ~/.bashrc
source ~/.zshrc
```

### Windows

**Option A — run it in place** (PowerShell or cmd, zero setup):

```powershell
cd code\robotos-v0.3.0-windows-x64
.\bin\robotos.exe version
```

**Option B — temporary PATH** (current PowerShell session only):

```powershell
cd code\robotos-v0.3.0-windows-x64
$env:PATH = "$PWD\bin;$env:PATH"
robotos version
```

**Option C — permanent PATH** (recommended):

Settings → search **"Environment Variables"** → edit `Path` →
add the full path to the package's `bin\` folder
(e.g. `C:\...\code\robotos-v0.3.0-windows-x64\bin`) → open a
new terminal and `robotos version` works everywhere.

## Step 3 — Verify it works (3 commands)

```bash
robotos version     # → robotos 0.3.0
robotos doctor      # → checks transport, discovery, config — all should pass
robotos ui          # → opens the browser at http://127.0.0.1:4789
```

> [!NOTE]
> `robotos ui` doesn't open an external website — the inspector is
> embedded in the same binary and served on `127.0.0.1` only
> (loopback, nothing leaves your machine).

The inspector screen will be empty — **that's correct**.
No nodes are running yet: you're looking at "a graph with
no actors on stage".

## Step 4 — See your first node in the graph

The package ships ready-made example programs in `examples/` —
no code needed for this step. Open a second terminal:

```bash
# terminal 2 — the graph is still empty
robotos node list               # → nothing yet

# run the bundled example publisher (from the package folder)
./examples/rust-publisher
```

Back in the first terminal:

```bash
robotos node list       # → "rs_publisher"
robotos topic list      # → /robot/01/sensor/imu
robotos topic echo /robot/01/sensor/imu   # → real messages flowing in
```

Switch to the browser — **the node appears in the inspector
instantly**, with a topic edge connecting it to the graph.

How "instantly" works — presence is a heartbeat, not a query:

```
publisher        transport          inspector         your terminal
     |               |                   |                  |
     |- starts ----->|                   |                  |
     |               |- presence ------->|                  |
     |               |  announce (live)  |- node appears    |
     |- pub msg ---->|                   |                  |
     |               |- msg fanout ------------------------>|
     |               |                   |                  |- topic echo
     |               |<- subscribe req ---------------------|  shows msgs
     |               |- msgs ------------------------------>|
     |- exits ------>|- presence gone -->|- node disappears |
```
