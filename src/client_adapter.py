from __future__ import annotations

import json
from pathlib import Path
from typing import Callable
from urllib.request import urlopen


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


def attach_runtime_targets(offer: dict, base_url: str) -> dict:
    endpoints = [{"name": "runtime_ready", "url": f"{base_url}/api/runtime/ready"}]

    capabilities = set(offer["capabilities"])
    if "session.launch" in capabilities:
        endpoints.append({"name": "launcher_status", "url": f"{base_url}/api/launcher/status"})
        endpoints.append({"name": "launcher_start", "url": f"{base_url}/api/launcher/start"})
    if {"media.browse", "controller.navigate"} & capabilities:
        endpoints.append({"name": "household_browse", "url": f"{base_url}/api/household/browse"})
        endpoints.append({"name": "household_status", "url": f"{base_url}/api/household/status"})

    enriched = dict(offer)
    enriched["runtime_targets"] = endpoints
    return enriched


def probe_runtime_targets(
    offer: dict,
    fetcher: Callable[[str], dict] | None = None,
) -> dict:
    fetch = fetcher or _default_fetcher
    results = []
    for endpoint in offer.get("runtime_targets", []):
        payload = fetch(endpoint["url"])
        results.append(
            {
                "name": endpoint["name"],
                "url": endpoint["url"],
                "ok": True,
                "keys": sorted(payload.keys()),
            }
        )

    probed = dict(offer)
    probed["runtime_probe"] = results
    return probed


def _default_fetcher(url: str) -> dict:
    with urlopen(url, timeout=2) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))
