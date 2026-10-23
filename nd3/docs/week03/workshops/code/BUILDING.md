# Building the bundled robotos packages (for maintainers/agents)

This folder ships prebuilt robotos packages to students. The
workshop docs reference these exact directory names — keep them:

```
code/
├── robotos-v<ver>-macos-arm64/   ← bin/robotos, lib/librobotos_ffi.dylib, …
├── robotos-v<ver>-linux-x64/     ← bin/robotos, lib/librobotos_ffi.so, …
├── robotos-v<ver>-windows-x64/   ← bin/robotos.exe, lib/robotos_ffi.dll  (MISSING — build on a Windows machine)
└── robotos-<ver>-py3-none-any.whl
```

`ver` = the workspace version in `robotos/Cargo.toml`
(`workspace.package.version`, currently `0.3.0`). Build all bundles
**from the same commit** and bump `0.x.0` strings in
`workshops/*.md` to match (`robotos version`, `pip install` lines).

---

## ⚠️ Two things every agent must know

1. **The wheel is NOT platform-neutral** despite the `py3-none-any`
   tag — it embeds `robotos/_native/librobotos_ffi.<ext>`. A wheel
   built on macOS contains a `.dylib` and fails on Windows with
   "librobotos_ffi not found". Each OS needs its own wheel build
   (same filename — keep per-platform copies separate and drop the
   right one per class, or see the ROBOTOS_FFI_LIB workaround below).
2. **Do NOT cross-build the Windows bundle on macOS/Linux** — the
   CI recipe targets `x86_64-pc-windows-msvc` and is designed to run
   on a Windows host (GitHub `windows-latest`). Build it on the
   Windows machine.

---

## macOS package (rebuilt 2026-10-23, verified)

```bash
cd <robotos repo>
cd ui && pnpm install --frozen-lockfile && pnpm build && cd ..
ROBOTOS_EMBED_UI=1 cargo build --release -p robotos-cli -p robotos-ffi
PKG_NAME=robotos-v0.3.0-macos-arm64 ./scripts/package.sh
# → dist/robotos-v0.3.0-macos-arm64{,.tar.gz,.sha256}
```

Package script stages bin/lib/include/proto/examples + C++ SDK
statics (needs cmake + protobuf installed for those).

## Python wheel — per OS!

```bash
cd <robotos repo>
cargo build --release -p robotos-ffi          # native lib first
cp target/release/librobotos_ffi.dylib sdk/python/robotos/_native/
codesign --sign - --force sdk/python/robotos/_native/librobotos_ffi.dylib   # macOS only, REQUIRED (dlopen SIGKILLs unsigned copies)
cd sdk/python && python -m venv /tmp/we && /tmp/we/bin/pip install build
/tmp/we/bin/python -m build --wheel
# → dist/robotos-0.3.0-py3-none-any.whl  (contains that OS's lib)
```

On Windows the same steps produce a wheel embedding
`robotos_ffi.dll` (no codesign step; run in PowerShell/CMD with
`py -m build`).

## Linux package (rebuilt via Docker on macOS 2026-10-23)

```bash
# in the robotos repo on the mac (uses linux/amd64 emulation — slow, ~2h)
docker run -d --name rb-linux --platform linux/amd64 -v "$PWD:/src" -w /src rust:slim bash -c "
  apt-get update -qq > /dev/null 2>&1 &&
  apt-get install -qq -y build-essential protobuf-compiler pkg-config clang cmake > /dev/null 2>&1 &&
  rustup default 1.97.1 > /dev/null 2>&1 &&
  ROBOTOS_EMBED_UI=1 cargo build --release --target x86_64-unknown-linux-gnu -p robotos-cli -p robotos-ffi 2>&1 | tail -15"
# after it finishes, stage + strip + tar ON THE HOST (llvm-strip handles ELF):
/opt/homebrew/opt/llvm/bin/llvm-strip \
  target/x86_64-unknown-linux-gnu/release/robotos \
  target/x86_64-unknown-linux-gnu/release/librobotos_ffi.so
# then copy into dist/robotos-v0.3.0-linux-x64/ like the release
# workflow does (bin, lib, include/robotos, proto, lib/cmake,
# examples/src, README, LICENSE*, BUILD.md) and tar + shasum.
# NOTE: package.sh can't run on the host for a foreign target —
# it hard-runs `cargo build --target $TARGET` unconditionally.
```

Gotchas hit on 2026-10-23: builds eat disk (`target/debug` alone
was 28 GB — check `df -h` first); the pkg script re-runs
`cargo build` so run it inside the container, not on the host.

## Windows package — TODO on a Windows machine

The workshop expects `robotos-v<ver>-windows-x64/` with
`bin/robotos.exe`, `lib/robotos_ffi.dll` (+ `robotos_ffi.lib`),
`include/robotos/{robotos.h,robotos.hpp}`, `proto/robotos/`,
`lib/cmake/robotos/robotosConfig.cmake`, `examples/`, `README.md`,
`LICENSE*`, `BUILD.md`.

Recipe (mirrors `.github/workflows/release.yml` windows job):

```powershell
cd <robotos repo>
cd ui; pnpm install --frozen-lockfile; pnpm build; cd ..
$env:ROBOTOS_EMBED_UI = "1"
cargo build --release -p robotos-cli -p robotos-ffi

# package.sh runs under Git Bash — MINGW case sets os=windows:
PKG_NAME=robotos-v0.3.0-windows-x64 TARGET=x86_64-pc-windows-msvc bash scripts/package.sh
# (TARGET makes it reuse the just-built target/release instead of
# recompiling for a triple — it also copies .dll/.lib via its
# windows branch; verify robotos.exe + robotos_ffi.dll landed.)
# → dist/robotos-v0.3.0-windows-x64{,.tar.gz,.sha256}
```

If `package.sh` misbehaves on Windows, the pwsh block in
`.github/workflows/release.yml` ("package (windows)") is the exact
file list — copy it by hand.

Prereqs on the Windows machine: Git for Windows (bash), rustup
(the pinned toolchain installs itself from `rust-toolchain.toml`),
Node + pnpm (UI embed), cmake + protoc only if you also want the
C++ static libs (macOS bundle has them; Linux bundle currently
doesn't — that's a known gap).

**Then rebuild the wheel on Windows too** (see above) so Windows
students get a wheel embedding `robotos_ffi.dll`.

Workaround if only one wheel is shipped: leave the macOS wheel in
place and have Windows students do
`pip install robotos-*.whl` then
`$env:ROBOTOS_FFI_LIB = "<extracted-pkg>\lib\robotos_ffi.dll"`.

---

## After staging

```bash
cd kmutt-nd69
git add nd3/docs/week03/workshops/code/
git commit -m "nd3 week03: bump bundled robotos to v<ver> (platforms)"
git push
```
