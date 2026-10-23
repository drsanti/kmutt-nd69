# Workshop 05 — Parameters: reconfigure a node live

> **Goal:** give a node named configuration values, then change them
> from the CLI while the node is running — the equivalent of editing
> a PLC tag table online instead of redeploying.

**Requirements:** workshop 02 done

---

## Parameter vs topic (recap)

- **topic** = process data, flows constantly → sensor values
- **parameter** = configuration, node-owned, changes rarely →
  setpoints, thresholds, mode switches

A parameter belongs to its node — you read/write it through the
node, not a shared table.

## Where parameters live

```
┌─────────────┐                    ┌─────────────────────────────┐
│ robotos CLI │  param set         │       tuning_node           │
│ (any node)  │ ─────────────────► │  ┌────────────────────────┐ │
└─────────────┘                    │  │  param store (owned)   │ │
        ▲                          │  │  setpoint=42 mode=auto │ │
        │                          │  └───────────┬────────────┘ │
   reply│(or denied)               │              │ param_get    │
        │                          │              ▼              │
   allow_remote_params             │  main loop reads fresh      │
   must be TRUE on the node        │  values each iteration      │
                                   └─────────────────────────────┘
```

Two deliberate design choices:

- **Node-owned, not global.** There's no shared config server —
  each node declares and owns its parameters. A `set` goes *to the
  node*, gets validated there, and the node's next `param_get`
  sees the new value. Ownership keeps authority in one place.
- **Remote writes are opt-in.** `set_allow_remote_params(True)`
  exists because a parameter can move a machine — the safety
  default is *read-only from outside*. You saw the same gate on
  lifecycle (`allow_remote_lifecycle`) and you'll see it again on
  replayed commands (`--allow-commands`).

## Step 1 — A node with parameters

`code/05-tuning_node.py`:

```python
import time
import robotos

with robotos.Node("tuning_node") as node:
    node.declare_parameter("setpoint", 42)        # i64/f64/bool/string
    node.declare_parameter("mode", "auto")
    node.set_allow_remote_params(True)            # let CLI write them

    print("running — change params from the CLI")
    while True:
        sp = node.param_get("setpoint")
        mode = node.param_get("mode")
        print(f"  setpoint={sp}  mode={mode}")
        time.sleep(2)
```

Three calls do the work: `declare_parameter` (name + default),
`set_allow_remote_params(True)` (opt-in to remote writes — safety),
`param_get` (read the current committed value).

## Step 2 — Drive it from the CLI

```bash
cd code
python3 05-tuning_node.py       # terminal 1 — prints setpoint=42

robotos param list tuning_node              # declared params
robotos param get tuning_node setpoint      # → 42
robotos param set tuning_node setpoint 77   # write it live
robotos param get tuning_node setpoint      # → 77
```

Watch terminal 1 — the printed value changes **without restarting
the node**. That's the online tag-edit pattern, over the graph.

## Step 3 — Watch and persist

```bash
robotos param watch tuning_node            # live param-change events
robotos param save tuning_node tune.toml   # snapshot to TOML file
cat tune.toml
robotos param load tuning_node tune.toml   # restore a saved config
```

The historian/config-management parallel: parameters aren't
ephemeral — save a known-good configuration, reload it later or
on another machine.

## Step 4 — Lifecycle: read-only for now

```bash
robotos lifecycle get tuning_node     # current state → active
robotos lifecycle set tuning_node inactive
# → error: node is unmanaged (auto-active)
```

Lifecycle is the "managed node" idea from week02: a managed node
moves through `Created → Inactive → Active`, and remote transitions
are opt-in (`allow_remote_lifecycle`). But `lifecycle set` fails
honestly here — **Python SDK nodes are *unmanaged*** in this
release: they behave as if always `Active` and reject transitions.
The managed lifecycle state machine exists for Rust-SDK and embedded
nodes — `lifecycle get` still reports the auto-active state, which
is why the read works while the write refuses.

## One `param set`, in time order

```
you (CLI)        transport        tuning_node        main loop
   |                |                |                  |
   |- param set --->|                |                  |
   |  setpoint 77   |- route ------->|                  |
   |                |                |- validate+store->|
   |                |                |                  |
   |<- ok ----------|<- reply -------|                  |
   |                |                |                  |- param_get()
   |                |                |                  |  → 77
   |                |                |<-----------------|
   |                |                |  next print:     |
   |                |                |  setpoint=77     |
```

## ✅ Checkpoint

- [ ] `param list tuning_node` shows `setpoint` and `mode`
- [ ] `param set tuning_node setpoint 77` succeeds remotely
- [ ] Terminal 1's printout changes to `setpoint=77` — no restart
- [ ] `param watch` prints the change event live
- [ ] `param save` → `param load` round-trips a config file
- [ ] `lifecycle get tuning_node` reports `active`, and `set` is
      refused — you can explain `unmanaged (auto-active)`

## 🔧 Troubleshooting

| Symptom | Try |
|---|---|
| `param list` errors | it needs the node **name** — `param list tuning_node`, not the topic |
| `param set` denied | node didn't opt in — `set_allow_remote_params(True)` required |
| `lifecycle set` → `unmanaged` | expected — Python nodes are auto-active; managed lifecycle is for Rust/embedded nodes |
| `node not found` | node name typo, or the node exited — `robotos node list` |

## ➡️ Next

Workshop 06 — record live traffic and replay it later.

<sub>[← Workshop list](README.md)</sub>
