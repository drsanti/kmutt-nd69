# Building robotos

Status: v0.1 feature-complete — Rust pub/sub, C ABI, C++20 SDK with
cross-language interop tests, presence/graph announcements, and the
`robotos` CLI. See `docs/implementation-status.md` for the honest
acceptance checklist.

## Prerequisites

- `rustup` — the pinned toolchain (`1.97.1`, see `rust-toolchain.toml`)
  installs automatically on first `cargo` invocation.
- A C linker (Xcode CLT on macOS, MSVC build tools on Windows,
  `build-essential` on Linux) — required by dependencies.
- For the C++ SDK only: CMake ≥ 3.21, C++20 toolchain, protobuf
  (`brew install protobuf` / `apt install protobuf-compiler
  libprotobuf-dev` / `vcpkg install protobuf:x64-windows`).

No system `protoc`, ROS 2, Docker, or WSL needed for the **Rust** side:
`protoc` is vendored via the `protoc-bin-vendored` crate (ADR 0001).

## Build / test / lint

```bash
cargo build --workspace --release
cargo test --workspace
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
```

`cargo test --workspace` covers: topic/name validation, envelope
roundtrip, schema-mismatch rejection, drop-oldest/drop-newest queue
policies, shutdown semantics, presence announce/leave/expiry
(`tests/graph.rs`), publisher death + session restart survival
(`tests/recovery.rs`), the C ABI surface (`tests/ffi_api.rs`), and a
real Zenoh TCP loopback exchange between two sessions.

One test is `#[ignore]`d because multicast discovery can be flaky on
isolated machines — run it explicitly to check discovery on your network:

```bash
cargo test -p robotos-zenoh -- --ignored
```

## C++ SDK

```bash
cargo build --release -p robotos-ffi        # produces librobotos_ffi
cmake -S sdk/cpp -B build/cpp -DCMAKE_BUILD_TYPE=Release
cmake --build build/cpp --config Release --parallel
ctest --test-dir build/cpp -C Release --output-on-failure
```

CTest runs `abi_smoke` (C ABI lifecycle/publish/receive/free — with
`-DROBOTOS_ENABLE_ASAN=ON` it's instrumented with ASan+UBSan), the
pub/sub exchanges (`run_interop.sh`, POSIX only: C++↔Rust both
directions + callback), and the **RPC interop** scenarios
(`run_rpc.sh`): Rust/C++ service ↔ client in all four combinations.
The C ABI surface is described in `docs/adr/0006-c-abi-v0.md` and
`crates/robotos-ffi/include/robotos/robotos.h`.

## Two-process localhost demo

```bash
cargo run -p rust-subscriber   # terminal 1
cargo run -p rust-publisher    # terminal 2
```

Default topology is Zenoh peer mode with multicast discovery (ADR 0002).
For networks without multicast, configure endpoints explicitly:

```bash
ROBOTOS_LISTEN=tcp/0.0.0.0:7447  cargo run -p rust-subscriber
ROBOTOS_CONNECT=tcp/<host>:7447  cargo run -p rust-publisher
```

For a strict loopback-only check on one machine:

```bash
ROBOTOS_LISTEN=tcp/127.0.0.1:7447 ROBOTOS_MULTICAST=0 cargo run -p rust-subscriber
ROBOTOS_CONNECT=tcp/127.0.0.1:7447 ROBOTOS_MULTICAST=0 cargo run -p rust-publisher
```

Other env vars: `ROBOTOS_DOMAIN` (u16 cluster isolation, default 0),
`ROBOTOS_MULTICAST=0` (disable scouting).

## `robotos` CLI

Every node announces its presence on the reserved meta topic
`/_graph/announce` (ADR 0007); the CLI reads the local graph cache.
Presence data is self-reported and unauthenticated — trusted networks
only.

```bash
robotos version
robotos doctor                       # config, env, node-create + graph probe
robotos node list [--settle-ms N]    # discovered nodes (wait ≥1 s)
robotos node info <name|uuid-prefix>
robotos topic list                   # pubs/subs per topic
robotos topic info <topic>
robotos topic echo <topic> [--count N] [--schema ID]
```

`topic echo` discovers the schema from publisher announcements (or
`--schema`), decodes known messages (`robotos.sensor.v1.*`,
`robotos.graph.v1.*`), and prints a hex fallback — it never guesses a
decoder.

## Packaging

```bash
./scripts/package.sh   # → dist/robotos-v<ver>-<os>-<arch>.tar.gz + sha256
```

The tarball bundles the CLI, `librobotos_ffi`, C/C++ headers, the Rust
examples, README and BUILD docs — one artifact per host OS/arch, no
universal binaries. The script prints the dynamic-library audit; on
macOS only system frameworks are linked (no third-party dylibs).

## Layout

| Path | Role |
|---|---|
| `crates/robotos-core` | IDs, validated topic/node names, config, error model |
| `crates/robotos-protocol` | protobuf codegen + wire envelope + schema IDs |
| `crates/robotos-transport` | `Transport` traits, bounded queues, `LocalTransport` |
| `crates/robotos-zenoh` | Zenoh adapter (only crate importing `zenoh`) |
| `crates/robotos-runtime` | `Node`, `Publisher<M>`/`RawPublisher`, `Subscriber<M>`/`RawSubscriber`, presence/`GraphWatcher`, shutdown |
| `crates/robotos-cli` | `robotos` binary: `node list/info`, `topic list/info/echo`, `doctor` |
| `crates/robotos-ffi` | C ABI (`cdylib`), opaque handles, poll + callback delivery |
| `sdk/rust/robotos` | user-facing Rust facade crate |
| `sdk/cpp` | C++20 RAII SDK + interop tests |
| `interfaces/` | `.proto` schemas (envelope, sensor/v1) |
| `examples/` | Rust and C++ demo binaries |
| `docs/adr/` | implementation decisions pending owner review |

## Verified on

- macOS 26 ARM64 (`aarch64-apple-darwin`), Rust 1.97.1, Apple Clang 21,
  protobuf 36.2 — all Rust tests (incl. graph/presence, restart
  survival), all C++ builds, `abi_smoke` under ASan/UBSan, and all
  four cross-language CTest interop scenarios pass. Live `robotos
  node list`/`topic echo` against a running publisher verified.
  Other OS targets are CI'd but not yet validated by hand.
