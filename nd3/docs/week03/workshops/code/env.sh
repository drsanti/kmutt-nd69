#!/usr/bin/env bash
# Source from code/:  source ./env.sh
set -euo pipefail
if [[ ! -f .venv/bin/activate ]]; then
  echo "No .venv here - cd to workshops/code and create it (workshop 02)." >&2
  return 1 2>/dev/null || exit 1
fi
# shellcheck disable=SC1091
source .venv/bin/activate
if [[ -d robotos-v0.3.0-macos-arm64/bin ]]; then
  export PATH="$PWD/robotos-v0.3.0-macos-arm64/bin:$PATH"
elif [[ -d robotos-v0.3.0-linux-x64/bin ]]; then
  export PATH="$PWD/robotos-v0.3.0-linux-x64/bin:$PATH"
else
  echo "No robotos-v0.3.0-macos-arm64 or -linux-x64 package in this folder." >&2
  return 1 2>/dev/null || exit 1
fi
echo "OK  venv + robotos on PATH  ($(robotos version))"
