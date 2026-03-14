#!/usr/bin/env python3
"""Render a starter client session offer from the checked-in contract assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from client_adapter import attach_runtime_targets, build_offer, probe_runtime_targets

def main() -> int:
    parser = argparse.ArgumentParser(description="Render a uHOME-client starter session offer")
    parser.add_argument("--surface", help="Surface name to render")
    parser.add_argument("--server-url", default="http://127.0.0.1:8000", help="uHOME-server base URL")
    parser.add_argument("--probe", action="store_true", help="Probe runtime targets")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    offer = build_offer(REPO_ROOT, surface_name=args.surface)
    offer = attach_runtime_targets(offer, base_url=args.server_url)
    if args.probe:
        offer = probe_runtime_targets(offer)

    if args.json:
        print(json.dumps(offer, indent=2))
    else:
        print(f"surface={offer['surface']}")
        print(f"transport={offer['transport']}")
        print(f"runtime_owner={offer['runtime_owner']}")
        print(f"shell_adapter={offer['shell_adapter']}")
        print(f"capabilities={','.join(offer['capabilities'])}")
        print(f"runtime_targets={','.join(target['name'] for target in offer['runtime_targets'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
