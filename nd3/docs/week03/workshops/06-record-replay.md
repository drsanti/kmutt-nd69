# Workshop 06 — Record & replay: the historian pattern

> **Goal:** capture live topic traffic into a `.rbag` file, inspect
> it, and play it back — like pulling a historian trend and
> re-running the shift offline.

**Requirements:** workshops 02–04 done (you'll reuse their programs)

---

## Why record (recap)

The debugging problem from week02: distributed systems have no
single program to step through. Recording gives you the *real*
traffic — same timestamps, same order — to replay as many times as
you need.

## The two roles of a bag file

```
record (live traffic → file)              replay (file → live traffic)

┌───────────┐                             ┌───────────┐
│ sim_sensor│                             │ monitor   │
│ (node)    │                             │ (node)    │
└─────┬─────┘                             └─────┴─────┘
      │ publish                                 ▲ subscribe
      ▼                                         │
┌───────────┐        time passes          ┌─────┴─────┐
│ transport │ ──────────────────────────► │ transport │
│  (topic)  │                             │  (topic)  │
└─────┬─────┘                             └─────┴─────┘
      │ snoop                                   ▲ republish
      ▼                                         │
┌───────────┐                             ┌───────────┐
│ robotos   │   msg + timestamp + schema  │ robotos   │
│ record    │────────────────────────────►│ play      │
└───────────┘      machine_run.rbag       └───────────┘
```

The recorder is just a hidden subscriber; the player is just a
publisher. Nothing about `.rbag` is special to the graph — it's
a *tap* on the wire, not a change to it.

## Step 1 — Generate traffic

```bash
python3 sim_sensor.py         # terminal 1 — Imu at 10 Hz (workshop 02)
robotos ui                    # optional — watch while recording
```

## Step 2 — Record

```bash
robotos record /machine/01/sensor/imu -o machine_run.rbag --duration-s 10
```

Records all messages on that topic for 10 seconds into
`machine_run.rbag`. Without `--duration-s` it runs until Ctrl-C.

## Step 3 — Inspect the bag

```bash
robotos bag info machine_run.rbag
# → header, duration, message count, per-topic stats
```

A bag file is self-contained: the schema ID travels with the data,
so a replay on another machine still decodes correctly.

## Step 4 — Replay

Stop the publisher first — the point of replay is replaying *without*
the original producer:

```bash
robotos play machine_run.rbag               # recorded pacing
robotos play machine_run.rbag --rate 2.0    # 2× speed
robotos play machine_run.rbag --dry-run     # plan only, nothing sent
```

Now run `monitor.py` (workshop 02) — it receives the **replayed**
messages exactly as if the sensor were live. The subscriber cannot
tell the difference — that's the point: the graph doesn't care who
publishes, only what's on the topic.

## What replay actually does, in time order

```
.rbag file       robotos play      transport        monitor
     |               |                |               |
     |- msg@t=0 ---->|                |               |
     |               |- publish ----->|-- deliver --->|- on_message
     |- msg@t=100ms->|                |               |
     |               |  (sleeps       |               |
     |               |   ~100ms)      |               |
     |               |- publish ----->|-- deliver --->|- on_message
     |- msg@t=200ms->|                |               |
     |               |                |               |
```

Replay preserves **relative timing** — the gaps between messages,
not the wall-clock moment they were recorded. `--rate 2.0` halves
the gaps. `--dry-run` shows the schedule without touching the
graph. That timing fidelity is what makes replay useful for
debugging: a race that happened live reproduces in the replay.

One honest caveat: replayed messages get **new** publish
timestamps — the original `ts` fields inside the *payload* (like
`Imu.timestamp_ns`) survive, but the wire-level arrival time is
fresh. Tools that stamp on receipt see the replay, not the past.

## Step 5 — Presence (bonus observation)

While nodes come and go:

```bash
robotos presence               # watch nodes join/leave live
robotos presence --get         # one-shot list of who's alive
```
