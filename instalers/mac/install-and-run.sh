#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT="$(pwd)"
bash "$ROOT/instalers/mac/setup-runtime.sh"
PY="$ROOT/instalers/runtime/macos/python/bin/python3"
exec "$PY" "$ROOT/instalers/common/bootstrap.py" launch
