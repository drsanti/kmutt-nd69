# Workshop 04 — Actions: long-running goals with feedback

> **Goal:** run a job that takes time — get progress updates while
> it works, and cancel it mid-flight. This is the pattern for
> "homing an axis", "running a batch cycle", "charging a battery".

**Requirements:** workshop 03 done

---

## Topic vs service vs action (recap)

| Pattern | Shape | Use for |
|---|---|---|
| topic | continuous stream | sensor data |
| service | short request → reply | quick commands |
| **action** | goal → feedback…→ result | long work, cancellable |

An action gives you three channels in one concept — **goal**,
**feedback**, **result** — plus the client's right to cancel:

```
┌────────────┐                ┌───────────────────────────────┐
│   client   │   goal ──────► │         action server         │
│   (node)   │                │                               │
│            │ ◄──── feedback │  handler loop:                │
│            │     (many)     │    check cancel? ─► abort     │
│            │                │    do work ─► send feedback   │
│            │ ──── cancel ─► │                               │
│            │                │    done ─► return result      │
│            │ ◄───── result  │                               │
└────────────┘     (once)     └───────────────────────────────┘
```

Why this needs its own pattern: a *service* must hold the request
open for the whole duration — a 5-minute homing cycle would be a
5-minute blocked call with no visibility and no way out. An
action decouples "starting the work" from "watching the work":
`send_goal` returns immediately with a `goal_id`, then feedback
and result arrive on their own schedule. Cancellation exists
because long work *needs* an abort path — fire-and-forget can't
give you one.

## Step 1 — The action server

`code/04-cycle_server.py` — simulates a 5-step machine cycle:

```python
import time
import robotos
from robotos.messages.robotos.test.v1.echo_pb2 import (
    EchoRequest, EchoResponse)

ACT = "/machine/01/cycle"

with robotos.Node("cycle_server") as node:
    def handler(goal, ctx):
        for i in range(1, 6):
            if ctx.cancel_requested():            # client cancelled?
                return EchoResponse(text="aborted",
                                    sequence=goal.sequence)
            ctx.send_feedback(                    # progress update
                EchoRequest(text=f"step {i}/5"))
            time.sleep(1.0)                     # work takes time
        return EchoResponse(text="cycle complete",
                            sequence=goal.sequence)

    node.create_action(ACT, EchoRequest, EchoRequest,
                       EchoResponse, handler)
    print(f"serving {ACT} — Ctrl-C to stop")
    while True:
        time.sleep(1)
```

`create_action(name, GoalT, FeedbackT, ResultT, handler)` — the
handler checks `ctx.cancel_requested()` and calls
`ctx.send_feedback(...)` between work steps.

## Step 2 — The action client

`code/04-cycle_client.py`:

```python
import time
import robotos
from robotos.messages.robotos.test.v1.echo_pb2 import (
    EchoRequest, EchoResponse)

ACT = "/machine/01/cycle"

with robotos.Node("cycle_client") as node:
    cli = node.action_client(ACT, EchoRequest, EchoRequest,
                             EchoResponse)

    goal_id = None
    for _ in range(30):                       # wait for server
        try:
            goal_id = cli.send_goal(
                EchoRequest(text="start cycle", sequence=1),
                timeout_ms=500)
            break
        except robotos.RobotosError as e:
            if e.status != 10:                # UNAVAILABLE → retry
                raise
            time.sleep(0.3)
    if goal_id is None:
        print("server never came up — is 04-cycle_server.py running?")
        cli.close()
        raise SystemExit(1)
    print(f"goal accepted: {goal_id}")

    deadline = time.time() + 15
    while time.time() < deadline:
        fb = cli.feedback_recv(goal_id, 300)
        if fb is not None:
            print(f"  feedback: {fb.text}")
        try:
            state, res = cli.result(goal_id, 10)
            print(f"result: {state.name} — '{res.text}'")
            break
        except robotos.RobotosError:
            continue                          # still running
    cli.close()
```

## Step 3 — Run and watch

> New terminal? See [Every new terminal](README.md#every-new-terminal-copy-paste)
> (venv + `robotos` on PATH, work from `code/`).

```bash
# macOS / Linux
cd code
python3 04-cycle_server.py     # terminal 1
python3 04-cycle_client.py     # terminal 2
```

```powershell
# Windows PowerShell — python, not python3
cd code
python 04-cycle_server.py      # terminal 1
python 04-cycle_client.py      # terminal 2
```

Client: goal accepted → feedback step 1/5 … 5/5 → result SUCCEEDED.

## Step 4 — Cancel a running goal

Modify the client loop to cancel after the first feedback:

```python
    fb = cli.feedback_recv(goal_id, 300)
    if fb is not None:
        print(f"  feedback: {fb.text}")
        cli.cancel(goal_id)                    # ← abort mid-cycle
```

Run again — the server sees `cancel_requested()` and returns
`"aborted"`; the client reports the cancelled state instead of
SUCCEEDED. That's the difference between an action and a fire-and-forget
topic: **the goal has a lifecycle of its own.**

The complete exchange, in time order:

```
client            action          cycle_server       handler loop
   |               |                   |                  |
   |- send_goal -->|-- dispatch ------>|-- handler() ---->|
   |<- goal_id ----|                   |                  |
   |               |                   |                  |- step 1
   |               |<-- feedback -------------------------|
   |<- fb_recv ----|                   |                  |- step 2
   |               |                   |                  |  ...
   |- cancel() --->|-- flag set ------------------------->|
   |               |                   |                  |- sees flag
   |               |                   |                  |- "aborted"
   |<- result --------------------------------------------|
   |   CANCELED    |                   |                  |
```

## ✅ Checkpoint

- [ ] Client prints `goal accepted` with a real `goal_id`
- [ ] Feedback arrives `step 1/5` through `step 5/5`, one per second
- [ ] Result is `SUCCEEDED — 'cycle complete'`
- [ ] With the cancel edit, result is `CANCELED` and the server
      returned `"aborted"` — proof the loop checked the flag
- [ ] You can name the three channels: goal, feedback, result

## 🔧 Troubleshooting

| Symptom | Try |
|---|---|
| `robotos` not recognized | new terminal lost PATH — [Every new terminal](README.md#every-new-terminal-copy-paste) |
| `server never came up` message | start `04-cycle_server.py` first — the client's 30 retries exhaust in ~15 s |
| Goal accepted but no feedback | server died after accepting — check its terminal |
| `send_goal` throws immediately | server not discovered yet — that's the `UNAVAILABLE` retry path |

## ➡️ Next

Workshop 05 — parameters: reconfigure a running node from the CLI.

<sub>[← Workshop list](README.md)</sub>
