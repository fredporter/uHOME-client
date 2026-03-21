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

python3 - <<'PY'
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
  if grep -R -nE '/Users/fredbook/Code|~/Users/fredbook/Code' \
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

python3 "$REPO_ROOT/scripts/smoke/session_offer.py" --json >/dev/null
python3 "$REPO_ROOT/scripts/smoke/session_offer.py" --json --local-app >/dev/null
python3 "$REPO_ROOT/scripts/smoke/session_offer.py" --json --local-app --control-brief >/dev/null
python3 "$REPO_ROOT/scripts/smoke/session_offer.py" --surface remote-runtime-bridge --json --wizard-local-app --remote-bridge-brief >/dev/null
python3 -m unittest discover -s tests -p 'test_*.py'

echo "uHOME-client checks passed"
