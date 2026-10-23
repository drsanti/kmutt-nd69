# ND03 — Week 03: Hands-on Workshops

> From concepts to hands-on — each workshop is a step-by-step
> guide you can follow directly and see real results on your machine.

All workshops run **entirely on your laptop** — the ESP32-S3 board
arrives next week. Everything here uses local transport, so no
network or hardware is needed.

## 📚 Workshop list

| # | Workshop | What you get |
|---|---|---|
| 01 | [Getting started — install and see the graph](01-getting-started.md) | CLI + inspector + your first node |
| 02 | [Publish & Subscribe — your first topic](02-pub-sub.md) | publisher + subscriber in Python, live messages in the inspector |
| 03 | [Service calls — commanding a node](03-services.md) | request/response, CLI `service call` |
| 04 | [Actions — long-running goals](04-actions.md) | goal/feedback/cancel — the long-job pattern |
| 05 | [Parameters — reconfigure a node live](05-parameters.md) | declare/set/watch/save/load + lifecycle states |
| 06 | [Record & replay — the historian pattern](06-record-replay.md) | `.rbag` capture, `bag info`, replay + presence |
| 07 | [Capstone: build a mini digital twin](07-mini-digital-twin.md) | twin-as-consumer, command path back, replay for safe testing |

## ⚙️ Prerequisites

| Item | Why | Where to get it |
|---|---|---|
| robotos package | CLI + shared library | bundled in [`code/`](code/) — `robotos-v*/` |
| robotos Python SDK | workshop language SDK | bundled wheel — `code/robotos-0.3.0-*.whl` |
| Python ≥ 3.10 | primary workshop language | python.org or system package |
| A single machine | local transport needs no network | — |

> [!IMPORTANT]
> **No ESP32-S3 board required this week** — the board arrives next
> week. Everything here runs on your laptop via local transport.
> No Rust toolchain or compilation needed either.

> [!TIP]
> **Runnable scripts live in [`code/`](code/)** — every workshop
> program has a ready-to-run `.py` file (e.g. `code/02-sim_sensor.py`).
> Type the code yourself for learning, or run the files directly.

## 🗺️ How the week maps to week02

| Week02 concept | Workshop |
|---|---|
| The graph (nodes, topics) | 01–02 |
| Messages & schema | 02 |
| Services & actions | 03–04 |
| Parameters & lifecycle | 05 |
| Observe & debug / record / presence | 06 |
| Digital twin | 07 (capstone) |

> [!NOTE]
> **Concept-only this week:** QoS presets and TF frames.
> QoS exists in the design but isn't exposed in the Python SDK yet;
> TF is a ROS concept robotos doesn't implement — both stay
> conceptual by design.

<sub>[← Week 03](../README.md)</sub>
