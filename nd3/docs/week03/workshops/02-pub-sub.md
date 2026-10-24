# Workshop 02 — Publish & Subscribe: your first topic

> **Goal:** write two small Python programs — one publishing sensor
> data, one receiving it — and watch the messages flow through
> the graph and the inspector.

**Requirements:** workshop 01 done, Python ≥ 3.10,
`librobotos_ffi` reachable (`ROBOTOS_FFI_LIB` or bundled)

---

## What we're building

```
┌────────────┐  publish     ┌───────────────────────┐  subscribe   ┌──────────┐
│ sim_sensor │ ───────────► │ /machine/01/sensor/   │ ───────────► │ monitor  │
│   (node)   │              │       imu (topic)     │              │  (node)  │
└────────────┘              └──────────┬────────────┘              └──────────┘
                                       │
                                       │ also watches (no code needed)
                                       ▼
                              ┌─────────────────┐
                              │ robotos ui /    │
                              │ topic echo      │
                              └─────────────────┘
```

A **simulated machine** publishes IMU readings at 10 Hz — exactly
the shape real sensor nodes take. No board needed: the data is
generated, but the transport is real.

## The idea that matters: decoupling

The publisher never learns that `monitor` exists. It addresses the
*topic*, not the consumer:

- **subscriber joins late** → starts getting new messages, no
  restart of the publisher
- **subscriber dies** → publisher doesn't notice or care
- **a second subscriber joins** (like `topic echo`) → the same
  stream fans out to both, no extra work from the publisher

This is the opposite of a function call: in a function call, caller
and callee must exist simultaneously and know each other. Pub/sub
removes both constraints — that's what lets a robot graph grow to
dozens of nodes without an N² web of direct connections.

## Step 1 — Install the Python SDK

> Session setup reminder: [Every new terminal](README.md#every-new-terminal-copy-paste).

The SDK ships as a wheel **inside `code/`** (next to the `.py`
scripts). Run these from `code/` — not from the `robotos-v0.3.0-*`
package folder.

**macOS / Linux:**

```bash
cd code
python3 -m venv .venv && source .venv/bin/activate
pip install ./robotos-0.3.0-py3-none-any.whl protobuf
```

**Windows** — **PowerShell only** (not Git Bash):

```powershell
cd code        # folder that contains the .whl and 02-*.py — NOT robotos-v0.3.0-windows-x64
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install .\robotos-0.3.0-py3-none-win_amd64.whl protobuf
```

If activation is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Verify:

```bash
# macOS / Linux
python3 -c "import robotos; print(robotos.Node.version())"
# → 0.3.0
```

```powershell
# Windows PowerShell — use python, NOT python3
python -c "import robotos; print(robotos.Node.version())"
# → 0.3.0
```

> [!IMPORTANT]
> **Interpreter name by OS (all workshops this week):**
> | OS | command |
> |---|---|
> | macOS / Linux | `python3` |
> | Windows (PowerShell) | `python` |
>
> On Windows, `python3` often bypasses `.venv` →
> `ModuleNotFoundError: robotos` even with `(.venv)` in the prompt.

> [!NOTE]
> The wheel bundles `librobotos_ffi` — no `ROBOTOS_FFI_LIB` path
> needed. Install the wheel matching **your** OS:
> macOS/Linux → `robotos-0.3.0-py3-none-any.whl`,
> Windows → `robotos-0.3.0-py3-none-win_amd64.whl`.

> [!WARNING]
> `pip install code\…whl` fails if your shell is already inside
> `code\robotos-v0.3.0-windows-x64` — that path looks for a nested
> `code\` that does not exist. Use `cd ..` (up to `code\`) then
> `pip install .\robotos-0.3.0-py3-none-win_amd64.whl protobuf`.

## Step 2 — Write the publisher

`code/02-sim_sensor.py` — runnable as-is, or type it yourself:

```python
import random, time
import robotos
from robotos.messages.robotos.sensor.v1.imu_pb2 import Imu

TOPIC = "/machine/01/sensor/imu"

with robotos.Node("sim_sensor") as node:
    pub = node.create_publisher(TOPIC, Imu)
    print(f"publishing on {TOPIC} — Ctrl-C to stop")
    while True:
        pub.publish(Imu(
            timestamp_ns=time.time_ns(),
            frame_id="imu_01",
            acceleration={"x": 0.0, "y": 0.0, "z": 9.81},
            angular_velocity={"x": random.uniform(-1, 1)},
        ))
        time.sleep(0.1)          # 10 Hz
```

Three ideas in 15 lines: `Node` = your process on the graph,
`create_publisher(topic, Type)` = a typed channel,
`publish(msg)` = fire-and-forget.

## Step 3 — Watch it without code

```bash
# macOS / Linux
cd code
python3 02-sim_sensor.py       # terminal 1 — leave running
```

```powershell
# Windows PowerShell
cd code
python 02-sim_sensor.py        # terminal 1 — leave running
```

Then in **another** terminal — use the
[Every new terminal](README.md#every-new-terminal-copy-paste)
setup (venv + PATH), then:

```bash
robotos node list              # → sim_sensor
robotos topic list             # → /machine/01/sensor/imu
robotos topic echo /machine/01/sensor/imu
```

Open `robotos ui` — the node and topic edge appear.

## Step 4 — Write the subscriber

`code/02-monitor.py`:

```python
import robotos
from robotos.messages.robotos.sensor.v1.imu_pb2 import Imu

TOPIC = "/machine/01/sensor/imu"

with robotos.Node("monitor") as node:
    sub = node.create_subscriber(TOPIC, Imu)
    sub.on_message(lambda msg, meta: print(
        f"acc.z={msg.acceleration.z:.2f}  gyro.x={msg.angular_velocity.x:+.3f}"))
    input("subscribed — press Enter to stop")
```

```bash
# macOS / Linux
python3 02-monitor.py          # terminal 3 — values stream in
```

```powershell
# Windows PowerShell
python 02-monitor.py
```

`on_message(cb)` = event-driven push — the PLC→event-driven shift
from week02, in two lines. (`sub.recv(timeout_ms)` is the polling
alternative if you want pull-style.)

## Step 5 — See the graph complete

In the inspector, `sim_sensor` and `monitor` now both appear with
the topic between them — publisher on one side, subscriber on the
other. Kill the publisher: watch the subscriber's edge update.

## The message path, in time order

```
sim_sensor       transport         monitor          inspector
    |                |                |                 |
    |- Imu{...} ---->|                |                 |
    |                |- fanout ------>|                 |
    |                |                |- on_message --->|
    |                |                |  (callback runs)|- topic edge
    |- Imu{...} ---->|- fanout ------>|                 |  updates
    |                |                |                 |
    |  (publisher exits)              |                 |
    |                |- presence ---->|                 |- edge drops
    |                |   withdrawn    |  (no more msgs) |
```

## ✅ Checkpoint

- [ ] `pip install` of the bundled wheel + `protobuf` succeeds
- [ ] `robotos.Node.version()` prints `0.3.0`
- [ ] `node list` shows `sim_sensor` while the publisher runs
- [ ] `topic echo` decodes live `Imu` messages
- [ ] `02-monitor.py` prints `acc.z=9.81` and changing `gyro.x` values

## 🔧 Troubleshooting

| Symptom | Try |
|---|---|
| `ModuleNotFoundError: robotos` | from `code/`, install the wheel — `pip install ./robotos-0.3.0-py3-none-any.whl protobuf` (Windows: `.\robotos-0.3.0-py3-none-win_amd64.whl`) |
| `file does not exist` on `pip install code\…` | you are inside the package folder — `cd ..` into `code\`, then `pip install .\robotos-0.3.0-py3-none-win_amd64.whl` |
| `robotos: The term 'robotos' is not recognized` | new terminal lost PATH — from `code\`: `$env:PATH = "$PWD\robotos-v0.3.0-windows-x64\bin;$env:PATH"`, or use permanent PATH (workshop 01 Option C) |
| monitor prints nothing | is the publisher still running? Subscriber matching takes a few seconds on a fresh session — wait |
| `topic echo` silent but `node list` works | multicast scouting flakiness — pin `ROBOTOS_LISTEN`/`ROBOTOS_CONNECT` to `tcp/127.0.0.1` |

## ➡️ Next

Workshop 03 — request/response with services.

<sub>[← Workshop list](README.md)</sub>
