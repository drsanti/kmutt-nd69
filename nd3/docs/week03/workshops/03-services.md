# Workshop 03 — Service calls: request/response

> **Goal:** create a service that answers requests — the equivalent
> of a PLC function block call — and call it from another node.

**Requirements:** workshop 02 done

---

## When to use a service (recap)

- **topic** = continuous stream, fire-and-forget → sensor data, status
- **service** = one question, one answer → "reset counter", "get config", "move to position X"

The decision rule is about *shape*, not speed:

| You want… | Use | Because |
|---|---|---|
| every sample | topic | fire-and-forget, fans out to any number of listeners |
| one answer to one caller | service | request/response is a pair — exactly one reply per request |
| confirmation it happened | service | the reply *is* the ack; topics can't tell you who got what |
| progress over minutes | action (w04) | a service that takes minutes is an action wearing a disguise |

## What we're building

```
┌────────┐    request     ┌───────────────────┐    request    ┌─────────────┐
│ client │ ─────────────► │    /test/echo     │ ────────────► │ echo_server │
│ (node) │                │     (service)     │               │   (node)    │
│        │ ◄───────────── │                   │ ◄──────────── │             │
└────────┘    response    └───────────────────┘    response   └─────────────┘
```

The client addresses the *service name*, not the server node —
same decoupling rule as topics: whoever serves `/test/echo` gets
the call, the client never learns which node answered.

## Step 1 — The service server

`code/03-echo_server.py`:

```python
import sys, time
import robotos
from robotos.messages.robotos.test.v1.echo_pb2 import (
    EchoRequest, EchoResponse)

SVC = "/test/echo"

with robotos.Node("echo_server") as node:
    def echo(req: EchoRequest) -> EchoResponse:
        print(f"request: '{req.text}' (seq {req.sequence})")
        return EchoResponse(text=req.text, sequence=req.sequence)

    node.create_service(SVC, EchoRequest, EchoResponse, echo)
    print(f"serving {SVC} — Ctrl-C to stop")
    while True:
        time.sleep(1)
```

`create_service(name, ReqType, RespType, handler)` — the handler
receives a decoded request and returns a decoded response.

## Step 2 — The client

`code/03-client.py`:

```python
import sys, time
import robotos
from robotos.messages.robotos.test.v1.echo_pb2 import (
    EchoRequest, EchoResponse)

SVC = "/test/echo"

with robotos.Node("client") as node:
    for attempt in range(30):
        try:
            resp = node.call(
                SVC, EchoRequest, EchoResponse,
                EchoRequest(text="hello robotos", sequence=1),
                timeout_ms=2000)
            print(f"reply: '{resp.text}' (seq {resp.sequence})")
            break
        except robotos.RobotosError as e:
            if e.status != 10:     # UNAVAILABLE — server not up yet
                raise
            time.sleep(0.3)
    else:
        print("no responder")
```

## Step 3 — Run it

```bash
cd code
python3 03-echo_server.py      # terminal 1
python3 03-client.py           # terminal 2
# server prints the request, client prints the reply
```

> [!NOTE]
> The retry loop exists because service discovery takes a moment —
> a call made before the server is announced returns `UNAVAILABLE`.
> Same concept as a fieldbus device that hasn't been scanned yet.

## Step 4 — Inspect it

```bash
robotos service list           # → /test/echo
robotos service info /test/echo   # → which node serves it
```

The CLI can also call a service without writing a client — but it
sends **raw payload bytes**, so you build the request as hex-encoded
protobuf. `EchoRequest(text="hi", sequence=1)` encodes to `0a0268691001`:

```bash
robotos service call /test/echo \
  --req-schema robotos.test.v1.EchoRequest \
  --rep-schema robotos.test.v1.EchoResponse \
  --data-hex 0a0268691001
# → reply bytes printed as hex (same schema, decode mentally or in Python)
```

For day-to-day work the Python client is easier — the raw-bytes form
exists for quick reachability checks and scripting.

## The call, in time order

```
client           transport        echo_server        handler
   |                |                  |                |
   |- call(req) --->|                  |                |
   |                |- route to ------>|                |
   |                |   responder      |- echo(req) --->|
   |  (blocks,      |                  |                |- build resp
   |   waiting)     |                  |<- returns -----|
   |                |<-- reply --------|                |
   |<- resp --------|                  |                |
   |- returns to    |                  |                |
   |  your code     |                  |                |
```

## ✅ Checkpoint

- [ ] `service list` shows `/test/echo` while the server runs
- [ ] `service info` names `echo_server` as the responder
- [ ] Client prints `reply: 'hello robotos' (seq 1)`
- [ ] Server logs each request it received
- [ ] You can explain the UNAVAILABLE retry loop in the client

## 🔧 Troubleshooting

| Symptom | Try |
|---|---|
| Client prints `no responder` | server not running, or discovery too slow — start `03-echo_server.py` first |
| `service call` errors about schemas | it needs `--req-schema`/`--rep-schema` + `--data-hex` — see Step 4 |
| Server exits immediately | port/service already served by a leftover process — check `node list` |

## ➡️ Next

Workshop 04 — actions: goals, feedback, and cancellation.

<sub>[← Workshop list](README.md)</sub>
