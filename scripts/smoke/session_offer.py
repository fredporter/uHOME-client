#!/usr/bin/env python3
"""Render a starter client session offer from the checked-in contract assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_offer(repo_root: Path, surface_name: str | None = None) -> dict:
    session_contract = load_json(repo_root / "src" / "session-contract.json")
    surface_map = load_json(repo_root / "src" / "surface-map.json")

    surfaces = surface_map["surfaces"]
    if surface_name is None:
        surface = next(item for item in surfaces if item["surface"] == session_contract["surface"])
    else:
        surface = next(item for item in surfaces if item["surface"] == surface_name)

    capabilities = sorted(set(session_contract["capabilities"]) | set(surface["capabilities"]))

    return {
        "version": surface_map["version"],
        "surface": surface["surface"],
        "transport": surface["transport"],
        "runtime_owner": surface["runtime_owner"],
        "shell_adapter": surface["shell_adapter"],
        "server_contract": session_contract["server_contract"],
        "capabilities": capabilities,
        "status": "starter-offer",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a uHOME-client starter session offer")
    parser.add_argument("--surface", help="Surface name to render")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    offer = build_offer(repo_root, surface_name=args.surface)

    if args.json:
        print(json.dumps(offer, indent=2))
    else:
        print(f"surface={offer['surface']}")
        print(f"transport={offer['transport']}")
        print(f"runtime_owner={offer['runtime_owner']}")
        print(f"shell_adapter={offer['shell_adapter']}")
        print(f"capabilities={','.join(offer['capabilities'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
