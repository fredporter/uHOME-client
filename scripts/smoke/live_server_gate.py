#!/usr/bin/env python3
"""Run and validate the client-to-server live smoke as a release-style gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


EXPECTED_KEYS = {
    "runtime_ready": {"checks", "ok", "status", "summary", "timestamp"},
    "runtime_info": {"app", "cwd", "platform", "platform_release", "python_version", "repo_root", "settings", "timestamp"},
    "dashboard_summary": {"bridge", "ok", "subsystems", "summary", "timestamp", "workspace_runtime"},
    "launcher_status": {
        "active_presentation",
        "node_role",
        "node_role_source",
        "preferred_presentation",
        "preferred_presentation_source",
        "running",
        "session_id",
        "state_path",
        "supported_node_roles",
        "supported_presentations",
        "updated_at",
    },
    "launcher_start": {"active_presentation", "node_role", "session_id", "status", "updated_at"},
    "household_browse": {"count", "hidden_count", "items", "query", "safe_mode", "timestamp", "total"},
    "household_status": {
        "active_media",
        "active_media_count",
        "hidden_media_count",
        "issue",
        "jellyfin_configured",
        "jellyfin_reachable",
        "node_role",
        "note",
        "preferred_target_client",
        "presentation_mode",
        "safe_mode",
        "timestamp",
    },
}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    smoke_script = repo_root / "scripts" / "smoke" / "live_server_smoke.py"

    proc = subprocess.run(
        [sys.executable, str(smoke_script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "live server smoke failed")

    payload = json.loads(proc.stdout)
    probes = payload.get("runtime_probe", [])
    if len(probes) != len(EXPECTED_KEYS):
        raise RuntimeError(f"expected {len(EXPECTED_KEYS)} runtime probes, got {len(probes)}")

    seen = set()
    for probe in probes:
        name = probe["name"]
        seen.add(name)
        expected = EXPECTED_KEYS.get(name)
        if expected is None:
            raise RuntimeError(f"unexpected runtime probe {name}")
        actual = set(probe["keys"])
        missing = sorted(expected - actual)
        if missing:
            raise RuntimeError(f"{name} missing keys: {missing}")

    if seen != set(EXPECTED_KEYS):
        raise RuntimeError(f"probe coverage mismatch: expected {sorted(EXPECTED_KEYS)}, got {sorted(seen)}")

    brief = payload.get("runtime_session_brief", {})
    if brief.get("recommended_action") not in {"start_launcher", "maintain_session", "inspect_runtime"}:
        raise RuntimeError("runtime_session_brief missing valid recommended_action")

    print(json.dumps({"status": "PASS", "checked": sorted(seen)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
