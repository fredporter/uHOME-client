#!/usr/bin/env bash

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SHARED_PYTHON_BIN="${UDOS_SHARED_PYTHON_BIN:-}"
USE_SHARED_RESOURCES="${UDOS_USE_SHARED_RESOURCES:-1}"
VENV_DIR="${UDOS_VENV_DIR:-$HOME/.udos/venv/uhome-client}"
BASE_PYTHON_BIN=""
PYTHON_BIN="$VENV_DIR/bin/python"

pick_python() {
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

require_file() {
  if [ ! -f "$1" ]; then
    echo "missing required file: $1" >&2
    exit 1
  fi
}

cd "$REPO_ROOT"
mkdir -p "$VENV_DIR"

if [ "$USE_SHARED_RESOURCES" = "1" ] && [ -z "$SHARED_PYTHON_BIN" ]; then
  FAMILY_HELPER="$REPO_ROOT/../scripts/lib/family-python.sh"
  if [ -f "$FAMILY_HELPER" ]; then
    # shellcheck source=/dev/null
    . "$FAMILY_HELPER"
    ensure_shared_python
    SHARED_PYTHON_BIN="${UDOS_SHARED_PYTHON_BIN:-}"
  fi
fi

BASE_PYTHON_BIN="$(pick_python)"
if [ -z "$BASE_PYTHON_BIN" ]; then
  echo "no python interpreter available" >&2
  exit 1
fi

if [ -n "$SHARED_PYTHON_BIN" ] && [ -x "$SHARED_PYTHON_BIN" ]; then
  PYTHON_BIN="$SHARED_PYTHON_BIN"
elif [ ! -x "$PYTHON_BIN" ]; then
  "$BASE_PYTHON_BIN" -m venv "$VENV_DIR"
fi

if ! "$PYTHON_BIN" -c 'import cryptography, fastapi, httpx, pydantic, uvicorn' >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel >/dev/null
  "$PYTHON_BIN" -m pip install cryptography fastapi httpx pydantic uvicorn >/dev/null
fi

require_file "$REPO_ROOT/README.md"
require_file "$REPO_ROOT/docs/architecture.md"
require_file "$REPO_ROOT/docs/boundary.md"
require_file "$REPO_ROOT/docs/getting-started.md"
require_file "$REPO_ROOT/docs/examples.md"
require_file "$REPO_ROOT/docs/activation.md"
require_file "$REPO_ROOT/docs/v2.0.1-client-alignment.md"
require_file "$REPO_ROOT/src/README.md"
require_file "$REPO_ROOT/src/runtime-profile-contract.json"
require_file "$REPO_ROOT/src/runtime-profile-map.json"
require_file "$REPO_ROOT/scripts/README.md"
require_file "$REPO_ROOT/scripts/smoke/session_offer.py"
require_file "$REPO_ROOT/scripts/smoke/live_server_smoke.py"
require_file "$REPO_ROOT/scripts/smoke/live_server_gate.py"
require_file "$REPO_ROOT/tests/README.md"
require_file "$REPO_ROOT/config/README.md"
require_file "$REPO_ROOT/examples/README.md"
require_file "$REPO_ROOT/examples/basic-client-runtime.json"

"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

repo_root = Path(".").resolve()
source = json.loads((repo_root / "src" / "runtime-profile-contract.json").read_text(encoding="utf-8"))
profile_map = json.loads((repo_root / "src" / "runtime-profile-map.json").read_text(encoding="utf-8"))
example = json.loads((repo_root / "examples" / "basic-client-runtime.json").read_text(encoding="utf-8"))

required = {"profile", "transport", "server_contract", "capability_profile"}
for name, payload in {"src/runtime-profile-contract.json": source, "examples/basic-client-runtime.json": example}.items():
    missing = sorted(required - payload.keys())
    if missing:
        raise SystemExit(f"{name} missing required fields: {missing}")
    if not isinstance(payload["capability_profile"], list) or not all(isinstance(item, str) for item in payload["capability_profile"]):
        raise SystemExit(f"{name} capability_profile must be a list of strings")

if profile_map.get("version") != "v2.0.3":
    raise SystemExit("src/runtime-profile-map.json version must be v2.0.3")

if sorted(profile_map.get("family_modes", [])) != ["integrated-udos", "standalone-uhome"]:
    raise SystemExit("src/runtime-profile-map.json family_modes must include standalone-uhome and integrated-udos")

profiles = profile_map.get("profiles")
if not isinstance(profiles, list) or not profiles:
    raise SystemExit("src/runtime-profile-map.json profiles must be a non-empty array")

for profile in profiles:
    if not {"profile", "surface_key", "transport", "runtime_owner", "shell_adapter", "deployment_modes", "app_targets", "capability_profile"} <= profile.keys():
        raise SystemExit(f"profile entry missing required fields: {profile}")
    if not isinstance(profile["capability_profile"], list) or not all(isinstance(item, str) for item in profile["capability_profile"]):
        raise SystemExit("profile entry capability_profile must be a list of strings")
    if not isinstance(profile["app_targets"], list) or not all(isinstance(item, str) for item in profile["app_targets"]):
        raise SystemExit("profile entry app_targets must be a list of strings")
    if sorted(profile["deployment_modes"]) != ["integrated-udos", "standalone-uhome"]:
        raise SystemExit("profile entry deployment_modes must include standalone-uhome and integrated-udos")
PY

if command -v rg >/dev/null 2>&1; then
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
else
  if grep -RInE -I --exclude-dir='__pycache__' '/Users/fredbook/Code|~/Users/fredbook/Code' \
    "$REPO_ROOT/README.md" \
    "$REPO_ROOT/docs" \
    "$REPO_ROOT/src" \
    "$REPO_ROOT/tests" \
    "$REPO_ROOT/examples" \
    "$REPO_ROOT/config" >/dev/null 2>&1; then
    echo "private local-root reference found in uHOME-client" >&2
    exit 1
  fi
fi

"$PYTHON_BIN" "$REPO_ROOT/scripts/smoke/session_offer.py" --json >/dev/null
"$PYTHON_BIN" "$REPO_ROOT/scripts/smoke/session_offer.py" --json --local-app >/dev/null
"$PYTHON_BIN" "$REPO_ROOT/scripts/smoke/session_offer.py" --json --local-app --control-brief >/dev/null
"$PYTHON_BIN" "$REPO_ROOT/scripts/smoke/session_offer.py" --surface remote-runtime-bridge --json --wizard-local-app --remote-bridge-brief >/dev/null
"$PYTHON_BIN" -m unittest discover -s tests -p 'test_*.py'

echo "uHOME-client checks passed"
