# Workshop 07 — Capstone: build a mini digital twin

> **Goal:** assemble everything from the week into the digital twin
> pattern — a simulated machine publishing state, a twin node that
> mirrors it, and a command path back. Same shape next week's real
> board will use.

**Requirements:** workshops 02–06 done

---

## The pattern (recap)

A digital twin is **a live graph consumer** — not a simulator bolted
on the side. It subscribes to the real asset's state topics, keeps
a synchronized mirror, and can send commands back through the same
graph.

```
┌─────────────────┐   /machine/01/state  ┌─────────────────────┐
│    machine      │ ──────────────────►  │        twin         │
│    (node)       │      state @ 5 Hz    │       (node)        │
│                 │                      │                     │
│  internal state │                      │   mirror = last     │
│  speed/running  │                      │   known state       │
│                 │                      │                     │
│    applies      │    /machine/01/cmd   │    decides          │
│    commands     │ ◄──────────────────  │    (START/STOP)     │
└─────────────────┘       commands       └─────────────────────┘
```

Read the loop direction carefully: **state flows down, commands
flow up** — the twin mirrors but never writes the machine's state
directly; it influences the machine only by publishing on `cmd`,
exactly like an HMI/SCADA supervisory layer. Two channels, two
directions, one asset.

## Step 1 — The "machine"

`code/07-machine.py` — a simulated asset: internal state, publishes
it at 5 Hz, applies commands from its command topic:

```python
import time, threading
import robotos
from robotos.messages.robotos.sensor.v1.imu_pb2 import Imu

STATE, CMD = "/machine/01/state", "/machine/01/cmd"
state = {"speed": 0.0, "running": False}
lock = threading.Lock()

with robotos.Node("machine") as node:
    pub = node.create_publisher(STATE, Imu)

    def on_cmd(msg, meta):
        with lock:
            if "START" in msg.frame_id:
                state["running"] = True
            elif "STOP" in msg.frame_id:
                state["running"] = False
    node.create_subscriber(CMD, Imu).on_message(on_cmd)

    while True:
        with lock:
            if state["running"]:
                state["speed"] = min(1.0, state["speed"] + 0.1)
            else:
                state["speed"] = max(0.0, state["speed"] - 0.2)
            v = state["speed"]
        pub.publish(Imu(timestamp_ns=time.time_ns(),
                        frame_id="machine_01",
                        acceleration={"x": v}))   # speed → acc.x
        time.sleep(0.2)
```

## Step 2 — The twin

`code/07-twin.py` — subscribes to state, keeps the mirror, sends
commands:

```python
import time
import robotos
from robotos.messages.robotos.sensor.v1.imu_pb2 import Imu

STATE, CMD = "/machine/01/state", "/machine/01/cmd"
mirror = {"speed": None, "stamp": None}

def watch(seconds):             # print the mirror once a second
    for _ in range(seconds):
        if mirror["speed"] is not None:
            print(f"  twin sees speed={mirror['speed']:.2f}")
        time.sleep(1)

with robotos.Node("twin") as node:
    def on_state(msg, meta):
        mirror["speed"] = msg.acceleration.x
        mirror["stamp"] = msg.timestamp_ns
    node.create_subscriber(STATE, Imu).on_message(on_state)
    cmd = node.create_publisher(CMD, Imu)

    watch(5)                      # idle — speed sits at 0.0

    print("twin sends START")
    cmd.publish(Imu(frame_id="START"))
    watch(8)                      # speed ramps 0.1 -> 1.0

    print("twin sends STOP")
    cmd.publish(Imu(frame_id="STOP"))
    watch(6)                      # speed decays back to 0.0
```

## Step 3 — Run the full loop

> New terminal? See [Every new terminal](README.md#every-new-terminal-copy-paste)
> (venv + `robotos` on PATH, work from `code/`).

```bash
# macOS / Linux
cd code
python3 07-machine.py # terminal 1
python3 07-twin.py    # terminal 2
robotos ui            # terminal 3 — watch the two-node graph
```

```powershell
# Windows PowerShell — python, not python3
cd code
python 07-machine.py  # terminal 1
python 07-twin.py     # terminal 2
robotos ui            # terminal 3
```

The twin prints the machine's speed flat at `0.00`, **rising to
`1.00` after `START`**, and **decaying back after `STOP`** — it's
reading the machine's state stream, not sharing memory with it.
The only coupling is the topics. Expected output:

```
  twin sees speed=0.00          (idle — machine not running)
  twin sees speed=0.00
  twin sees speed=0.00
  twin sees speed=0.00
twin sends START
  twin sees speed=0.00
  twin sees speed=0.40          (machine ramps +0.1 per 200 ms tick)
  twin sees speed=0.90
  twin sees speed=1.00          (saturated)
  ...
twin sends STOP
  twin sees speed=1.00
  twin sees speed=0.00          (decays −0.2 per tick — faster than it ramps)
  ...
```

## Step 4 — Prove it's a real twin

Swap in observation tools:

```bash
robotos topic echo /machine/01/state    # third consumer — a second twin
robotos record /machine/01/state -o shift.rbag --duration-s 10
robotos play shift.rbag                 # replay "yesterday's shift"
```

Record the real run, replay it, and the twin mirrors *history* —
the virtual-commissioning idea: test the twin against recorded
reality before touching the real asset.

## The closed loop, in time order

```
machine          /state          twin            /cmd           machine
   |               |              |               |               |
   |- speed ------>|- deliver --->|               |               |
   |               |              |- mirror[x]=v  |               |
   |- speed ------>|- deliver --->|               |               |
   |               |              |               |               |
   |               |              |- START ------>|-- deliver --->|
   |               |              |               |               |- running=
   |- speed up --->|- deliver --->|               |               |  true
   |               |              |- sees rising  |               |
   |               |              |- STOP ------->|-- deliver --->|
   |- speed down ->|- deliver --->|- sees falling |               |
```

## ✅ Checkpoint

- [ ] `node list` shows `machine` and `twin` as separate nodes
- [ ] Twin mirrors `speed=0.00` while the machine idles
- [ ] After `START`: twin sees the ramp `→ 1.00` (saturated)
- [ ] After `STOP`: twin sees the decay back to `0.00`
- [ ] `topic echo /machine/01/state` shows the live 5 Hz stream —
      a third observer, no code needed
- [ ] You can explain: the twin touches **topics only** — no shared
      memory with the machine

## 🔧 Troubleshooting

| Symptom | Try |
|---|---|
| `robotos` not recognized | new terminal lost PATH — [Every new terminal](README.md#every-new-terminal-copy-paste) |
| Twin prints nothing after startup | machine not running — start `07-machine.py` first |
| Twin sees 0.00 forever | START never reached it — check `/machine/01/cmd` with `topic echo` |
| Machine state silent in echo | discovery lag — give it a few seconds, or pin endpoints |
| Twin exits before START effect visible | that's the point of `watch()` — it must *stay* subscribed while commands fly |

## 🎓 Where you are

You've built the supervisory pattern that real digital twins use:
state flows down, commands flow up, and the observer couples to the
asset through topics alone. Next week the `machine` stops being a
Python script — an ESP32-S3 board publishes the same topics, and
your twin won't notice the difference.

<sub>[← Workshop list](README.md)</sub>
