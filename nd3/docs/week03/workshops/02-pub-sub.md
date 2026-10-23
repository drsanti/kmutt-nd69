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

The SDK ships as a wheel in `code/` — one command, fully offline.

**macOS / Linux:**

```bash
# recommended: an isolated environment (venv)
python3 -m venv .venv && source .venv/bin/activate

# install the bundled wheel — native library included, no env vars
pip install code/robotos-0.3.0-py3-none-any.whl protobuf
```

**Windows** (PowerShell):

```powershell
# venv — activation script differs on Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # cmd.exe: .venv\Scripts\activate.bat

pip install code\robotos-0.3.0-py3-none-any.whl protobuf
```

Verify (all platforms):

```bash
python3 -c "import robotos; print(robotos.Node.version())"   # Windows: python
# → 0.3.0
```

> [!NOTE]
> The wheel bundles `librobotos_ffi` — no `ROBOTOS_FFI_LIB` path
> needed. Per-platform wheels follow standard Python packaging
> practice (like numpy or grpcio). Install the wheel matching
> **your** OS: `*-macos-*.whl`, `*-windows-*.whl`, `*-linux-*.whl`.

> [!TIP]
> **Naming conventions below** — commands show `python3`/`robotos`;
> on Windows use `python` and `robotos.exe` (or just `python` /
> `robotos` after PATH is set — cmd finds the `.exe` itself).

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
cd code
python3 02-sim_sensor.py       # terminal 1 — leave running

robotos node list              # terminal 2 → sim_sensor
robotos topic list             # → /machine/01/sensor/imu
robotos topic echo /machine/01/sensor/imu   # messages decoded live
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
python3 02-monitor.py          # terminal 3 — values stream in
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
| `ModuleNotFoundError: robotos` | install the bundled wheel — `pip install code/robotos-0.3.0-py3-none-any.whl protobuf` |
| monitor prints nothing | is the publisher still running? Subscriber matching takes a few seconds on a fresh session — wait |
| `topic echo` silent but `node list` works | multicast scouting flakiness — pin `ROBOTOS_LISTEN`/`ROBOTOS_CONNECT` to `tcp/127.0.0.1` |

## ➡️ Next

Workshop 03 — request/response with services.

<sub>[← Workshop list](README.md)</sub>
