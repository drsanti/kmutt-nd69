# robotos

Cross-platform robotics middleware — an independent, lightweight,
ROS 2–inspired framework. Rust core (Tokio), Zenoh transport behind an
abstraction layer, Protocol Buffers messages, and native builds on
Windows, macOS (Intel + Apple Silicon), and Linux. **No ROS 2 required.**

> Status: **v0.2 feature-complete** — typed pub/sub, unary services
> (with cancellation), parameters (declare/get/set/watch + versioned
> save/load), lifecycle, actions (goal/feedback/cancel/result), QoS
> presets, `.rbag` record/replay, presence/graph, inspector UI
> (`robotos ui`), `robotos` CLI, and C ABI + C++20 / Python /
> TypeScript SDKs (`sdk/`). Cross-language interop tests pass on
> macOS ARM64; multi-OS is CI-only. **ROS 2 interop verified** —
> `robotos bridge ros2` exchanges topics with real ROS 2 Jazzy
> under both FastDDS (default) and Cyclone RMWs; service calls work
> under Cyclone (`docs/interop/ros2-docker.md`).
> See `docs/implementation-status.md` for the honest acceptance
> checklist and `docs/adr/` for the design records.

## Quick start (Rust)

```bash
cargo run -p rust-subscriber   # terminal 1
cargo run -p rust-publisher    # terminal 2
```

```rust
use robotos::{Node, Result};
use robotos::messages::sensor::v1::Imu;

#[tokio::main]
async fn main() -> Result<()> {
    let node = Node::new("imu_sensor").await?;
    let publisher = node.publisher::<Imu>("/robot/01/sensor/imu").await?;
    publisher.publish(&Imu::default()).await?;
    node.shutdown().await
}
```

## Quick start (C++)

```bash
cargo build --release -p robotos-ffi
cmake -S sdk/cpp -B build/cpp -DCMAKE_BUILD_TYPE=Release
cmake --build build/cpp --parallel
./build/cpp/cpp-subscriber &  # then ./build/cpp/cpp-publisher
```

```cpp
robotos::Node node("imu_sensor_cpp");
auto pub = node.create_publisher<robotos::sensor::v1::Imu>("/robot/01/sensor/imu");
pub.publish(msg);  // Status::Ok = accepted for local transport
```

C++ subscribers support both blocking `recv(msg, &meta, timeout)` and
`on_message(callback)` delivery (ADR 0006). Requires CMake ≥ 3.21,
C++20, and a system protobuf.

## SDK examples

Every SDK ships the same trio — `publisher`, `subscriber`, `presence`:

```bash
cargo run -p robotos --example publisher     # sdk/rust/robotos/examples/
./build/cpp/cpp-publisher                    # sdk/cpp/examples/ (built above)
python3 sdk/python/examples/publisher.py     # sdk/python/  (protobuf pb2)
npx tsx sdk/typescript/examples/publisher.ts # sdk/typescript/  (protobufjs)
```

`sfx_compose` (all four SDKs) uploads + plays a custom melody —
note strings (`"E5/160 G5/160 C6/480"`) → SfxProg → the board's seq
engine. `led_fx` (all four SDKs) drives the board's WS2812 — solid/off/
blink-N/fade-N/rainbow via LedCmd + WaveCmd (the 3 wave channels run
the RGB). `mic_dump` (all four SDKs) streams the board's mic: publishes
MicCmd{enable,stream} then writes MicPcm chunks to a .wav (16 kHz mono).

Top-level `examples/` keeps the heavier demos (rpc-echo, action-demo,
serial-bridge, interop harnesses).

## CLI

Nodes announce themselves on `/_graph/announce` (ADR 0007); the
`robotos` binary inspects the local graph cache:

```bash
cargo build --release -p robotos-cli   # → target/release/robotos

robotos doctor                       # config + graph probe
robotos node list                    # discovered nodes
robotos node info <name>
robotos topic list                   # topics with pub/sub counts
robotos topic echo /robot/01/sensor/imu
robotos presence --get               # liveliness tokens (ROBOTOS_MODE=client for listener relays)
```

Presence is self-reported/unauthenticated — diagnostics only.

## Services (v0.2)

Unary RPC over Zenoh queryables (ADR 0008/0009) — responder
ambiguity is an error, never a silent pick:

```rust
let svc = node.service::<EchoRequest, EchoResponse, _, _>(
    "/robot/01/service/echo",
    |req| async move { Ok(reply) },
).await?;
let client = node.client::<EchoRequest, EchoResponse>("/robot/01/service/echo")?;
let rep = client.call(&req, Duration::from_secs(5)).await?;
```

C++ equivalents: `node.create_service<Req,Rep>` /
`create_client<Req,Rep>`. CLI: `robotos service list|info|call`.
Cancellable calls: `client.call_cancelable(req, timeout, &token)` —
advisory `CancelRequest` on `{svc}/_cancel` aborts the server handler
task (ADR 0009 §Cancellation).

## Actions, params, lifecycle (v0.2)

```rust
// actions: goal → feedback → cancel/result
let srv = node.action_server::<Goal, Fb, Result_, _, _>(
    "/act/move", |goal, ctx| async move { /* … */ }).await?;
let cli = node.action_client::<Goal, Fb, Result_>("/act/move").await?;
let handle = cli.send_goal(&goal, timeout).await?;

// params: typed, descriptor-validated, remote opt-in
node.declare_parameter("control.kp", 1.5f64, ParamDescriptor::default())?;
node.param_set("control.kp", ParamValue::F64(2.0)).await?;
node.save_params("params.toml")?;           // versioned TOML
let report = node.load_params("params.toml").await?;
```

CLI: `robotos param list|get|set|watch|save|load <node>`,
`robotos lifecycle ...`, `robotos ui` for the browser inspector.
C ABI: `robotos_param_*`, `robotos_lifecycle_*`,
`robotos_action_*`; C++: `create_action_{server,client}`.

## Semantics (honest version)

- Delivery is **best-effort**: `publish` Ok = accepted for local
  transport. No guaranteed delivery, global ordering, or exactly-once.
- Subscriber queues are bounded (default depth 32, drop-oldest);
  overflow and schema mismatches are counted, never silent.
- Schema identity = canonical protobuf name; incompatible payloads are
  rejected, not misdecoded.
- Trusted-network only: no authentication or encryption in v0.1.
  Metadata and data are not authorized. Not production-secure.
- No hard real-time guarantees.

## Docs

- `docs/build.md` — prerequisites, build/test commands, network config
- `docs/adr/` — architecture decision records
- `docs/robotos_v0.1_architecture_v0.1_development_plan.md` — full design + roadmap

## License

Licensed under either of [Apache-2.0](LICENSE-APACHE) or
[MIT](LICENSE-MIT), at your option. Third-party components carry their
own notices — see `THIRD_PARTY_NOTICES.md` (the shipped firmware
archive embeds nanopb, zlib license).
