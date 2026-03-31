#!/usr/bin/env python3
"""Render a starter client runtime offer from the checked-in contract assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from client_adapter import (
    attach_runtime_targets,
    attach_wizard_targets,
    build_remote_runtime_bridge_brief,
    build_runtime_session_brief,
    build_offer,
    probe_local_server_app,
    probe_local_wizard_app,
    probe_runtime_targets,
)

def main() -> int:
    parser = argparse.ArgumentParser(description="Render a uHOME-client starter runtime offer")
    parser.add_argument("--surface", "--profile", dest="surface", help="Runtime profile or surface key to render")
    parser.add_argument("--server-url", default="http://127.0.0.1:8000", help="uHOME-server base URL")
    parser.add_argument(
        "--wizard-url",
        default="http://127.0.0.1:8787",
        help="Optional external orchestration base URL (only if UH_EXTERNAL_ORCHESTRATION_CONTRACT_PATH is set)",
    )
    parser.add_argument("--probe", action="store_true", help="Probe runtime targets")
    parser.add_argument("--local-app", action="store_true", help="Probe an in-process sibling uHOME-server app")
    parser.add_argument(
        "--wizard-local-app",
        action="store_true",
        help="Legacy flag; optional orchestration in-process probe (no default checkout)",
    )
    parser.add_argument("--control-brief", action="store_true", help="Build a runtime-session brief from probe output")
    parser.add_argument("--remote-bridge-brief", action="store_true", help="Build a Wizard-assisted remote-runtime bridge brief")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    offer = build_offer(REPO_ROOT, surface_name=args.surface)
    offer = attach_runtime_targets(offer, base_url=args.server_url)
    offer = attach_wizard_targets(offer, wizard_url=args.wizard_url)
    if args.probe:
        offer = probe_runtime_targets(offer)
    if args.local_app:
        offer = probe_local_server_app(offer, workspace_root=REPO_ROOT.parent)
    if args.wizard_local_app:
        offer = probe_local_wizard_app(offer, workspace_root=REPO_ROOT.parent)
    if args.control_brief:
        probe_key = "local_runtime_probe" if args.local_app else "runtime_probe"
        offer = build_runtime_session_brief(offer, probe_key=probe_key)
    if args.remote_bridge_brief:
        probe_key = "local_wizard_probe" if args.wizard_local_app else "wizard_probe"
        offer = build_remote_runtime_bridge_brief(offer, probe_key=probe_key)

    if args.json:
        print(json.dumps(offer, indent=2))
    else:
        print(f"profile={offer['profile']}")
        print(f"surface={offer['surface']}")
        print(f"transport={offer['transport']}")
        print(f"runtime_owner={offer['runtime_owner']}")
        print(f"shell_adapter={offer['shell_adapter']}")
        print(f"deployment_modes={','.join(offer.get('deployment_modes', []))}")
        print(f"app_targets={','.join(offer.get('app_targets', []))}")
        print(f"capabilities={','.join(offer['capabilities'])}")
        print(f"runtime_targets={','.join(target['name'] for target in offer['runtime_targets'])}")
        if offer.get("wizard_targets"):
            print(f"wizard_targets={','.join(target['name'] for target in offer['wizard_targets'])}")
        if "runtime_session_brief" in offer:
            print(f"recommended_action={offer['runtime_session_brief']['recommended_action']}")
        if "remote_runtime_bridge_brief" in offer:
            print(f"remote_bridge_action={offer['remote_runtime_bridge_brief']['recommended_action']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
