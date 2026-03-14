#!/usr/bin/env bash

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

require_file() {
  if [ ! -f "$1" ]; then
    echo "missing required file: $1" >&2
    exit 1
  fi
}

cd "$REPO_ROOT"

require_file "$REPO_ROOT/README.md"
require_file "$REPO_ROOT/docs/architecture.md"
require_file "$REPO_ROOT/docs/boundary.md"
require_file "$REPO_ROOT/docs/getting-started.md"
require_file "$REPO_ROOT/docs/examples.md"
require_file "$REPO_ROOT/docs/activation.md"
require_file "$REPO_ROOT/docs/v2.0.1-client-alignment.md"
require_file "$REPO_ROOT/src/README.md"
require_file "$REPO_ROOT/src/session-contract.json"
require_file "$REPO_ROOT/src/surface-map.json"
require_file "$REPO_ROOT/scripts/README.md"
require_file "$REPO_ROOT/tests/README.md"
require_file "$REPO_ROOT/config/README.md"
require_file "$REPO_ROOT/examples/README.md"
require_file "$REPO_ROOT/examples/basic-client-session.json"

python3 - <<'PY'
import json
from pathlib import Path

repo_root = Path(".").resolve()
source = json.loads((repo_root / "src" / "session-contract.json").read_text(encoding="utf-8"))
surface_map = json.loads((repo_root / "src" / "surface-map.json").read_text(encoding="utf-8"))
example = json.loads((repo_root / "examples" / "basic-client-session.json").read_text(encoding="utf-8"))

required = {"surface", "transport", "server_contract", "capabilities"}
for name, payload in {"src/session-contract.json": source, "examples/basic-client-session.json": example}.items():
    missing = sorted(required - payload.keys())
    if missing:
        raise SystemExit(f"{name} missing required fields: {missing}")
    if not isinstance(payload["capabilities"], list) or not all(isinstance(item, str) for item in payload["capabilities"]):
        raise SystemExit(f"{name} capabilities must be a list of strings")

if surface_map.get("version") != "v2.0.1":
    raise SystemExit("src/surface-map.json version must be v2.0.1")

surfaces = surface_map.get("surfaces")
if not isinstance(surfaces, list) or not surfaces:
    raise SystemExit("src/surface-map.json surfaces must be a non-empty array")

for surface in surfaces:
    if not {"surface", "transport", "runtime_owner", "shell_adapter", "capabilities"} <= surface.keys():
        raise SystemExit(f"surface entry missing required fields: {surface}")
    if not isinstance(surface["capabilities"], list) or not all(isinstance(item, str) for item in surface["capabilities"]):
        raise SystemExit("surface entry capabilities must be a list of strings")
PY

if rg -n '/Users/fredbook/Code|~/Users/fredbook/Code' \
  "$REPO_ROOT/README.md" \
  "$REPO_ROOT/docs" \
  "$REPO_ROOT/src" \
  "$REPO_ROOT/tests" \
  "$REPO_ROOT/examples" \
  "$REPO_ROOT/config"; then
  echo "private local-root reference found in uHOME-client" >&2
  exit 1
fi

echo "uHOME-client checks passed"
