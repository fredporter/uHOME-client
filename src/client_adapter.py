from __future__ import annotations

import json
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen
import sys


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_runtime_services(repo_root: Path) -> tuple[dict, list[dict]]:
    manifest_path = repo_root.parent / "uDOS-core" / "contracts" / "runtime-services.json"
    manifest = load_json(manifest_path)
    services = [
        {
            "key": service["key"],
            "owner": service["owner"],
            "route": service["route"],
            "stability": service["stability"],
            "consumer": "uHOME-client",
            "usage": _usage_for_service(service["key"]),
        }
        for service in manifest["services"]
        if "uHOME-client" in service.get("consumers", [])
    ]
    return manifest, services


def _usage_for_service(key: str) -> str:
    if key == "runtime.command-registry":
        return "server endpoint coverage for interactive client surfaces"
    if key == "runtime.capability-registry":
        return "capability alignment between session contracts and shell routing"
    return "shared platform contract consumption"


def build_offer(repo_root: Path, surface_name: str | None = None) -> dict:
    session_contract = load_json(repo_root / "src" / "session-contract.json")
    surface_map = load_json(repo_root / "src" / "surface-map.json")
    runtime_manifest, runtime_services = load_runtime_services(repo_root)

    surfaces = surface_map["surfaces"]
    if surface_name is None:
        surface = next(item for item in surfaces if item["surface"] == session_contract["surface"])
    else:
        surface = next(item for item in surfaces if item["surface"] == surface_name)

    capabilities = sorted(set(session_contract["capabilities"]) | set(surface["capabilities"]))

    return {
        "version": runtime_manifest["version"],
        "foundation_version": surface_map["version"],
        "runtime_service_source": str(repo_root.parent / "uDOS-core" / "contracts" / "runtime-services.json"),
        "surface": surface["surface"],
        "transport": surface["transport"],
        "runtime_owner": surface["runtime_owner"],
        "shell_adapter": surface["shell_adapter"],
        "server_contract": session_contract["server_contract"],
        "capabilities": capabilities,
        "runtime_services": runtime_services,
        "status": "starter-offer",
    }


def attach_runtime_targets(offer: dict, base_url: str) -> dict:
    endpoints = [
        {"name": "runtime_ready", "url": f"{base_url}/api/runtime/ready", "method": "GET"},
        {"name": "runtime_info", "url": f"{base_url}/api/runtime/info", "method": "GET"},
        {"name": "dashboard_summary", "url": f"{base_url}/api/dashboard/summary", "method": "GET"},
    ]

    capabilities = set(offer["capabilities"])
    if "session.launch" in capabilities:
        endpoints.append({"name": "launcher_status", "url": f"{base_url}/api/launcher/status", "method": "GET"})
        endpoints.append(
            {
                "name": "launcher_start",
                "url": f"{base_url}/api/launcher/start",
                "method": "POST",
                "json": {},
            }
        )
    if {"media.browse", "controller.navigate"} & capabilities:
        endpoints.append({"name": "household_browse", "url": f"{base_url}/api/household/browse", "method": "GET"})
        endpoints.append({"name": "household_status", "url": f"{base_url}/api/household/status", "method": "GET"})

    enriched = dict(offer)
    enriched["runtime_targets"] = endpoints
    return enriched


def attach_wizard_targets(offer: dict, wizard_url: str) -> dict:
    enriched = dict(offer)
    targets = []
    if offer.get("transport") == "wizard-assisted":
        surface = offer.get("surface", "remote-control")
        targets.append(
            {
                "name": "wizard_dispatch",
                "url": f"{wizard_url}/orchestration/dispatch?task={surface}&mode=auto&surface=remote-control",
                "method": "GET",
            }
        )
    enriched["wizard_targets"] = targets
    return enriched


def probe_runtime_targets(
    offer: dict,
    fetcher: Callable[[str], dict] | None = None,
) -> dict:
    fetch = fetcher or _default_fetcher
    results = []
    for endpoint in offer.get("runtime_targets", []):
        payload = fetch(endpoint["url"], endpoint.get("method", "GET"), endpoint.get("json"))
        results.append(
            {
                "name": endpoint["name"],
                "url": endpoint["url"],
                "method": endpoint.get("method", "GET"),
                "ok": True,
                "keys": sorted(payload.keys()),
                "payload": payload,
            }
        )

    probed = dict(offer)
    probed["runtime_probe"] = results
    return probed


def _default_fetcher(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=2) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def probe_local_server_app(offer: dict, workspace_root: Path) -> dict:
    from fastapi.testclient import TestClient

    server_repo = workspace_root / "uHOME-server"
    sys.path.insert(0, str(server_repo / "src"))
    from uhome_server.app import create_app  # type: ignore

    client = TestClient(create_app())
    results = []
    for endpoint in offer.get("runtime_targets", []):
        path = endpoint["url"].replace("http://127.0.0.1:8000", "")
        method = endpoint.get("method", "GET")
        if method == "POST":
            response = client.post(path, json=endpoint.get("json"))
        else:
            response = client.get(path)
        payload = response.json()
        results.append(
            {
                "name": endpoint["name"],
                "path": path,
                "method": method,
                "status_code": response.status_code,
                "keys": sorted(payload.keys()),
                "payload": payload,
            }
        )

    probed = dict(offer)
    probed["local_runtime_probe"] = results
    return probed


def probe_local_wizard_app(offer: dict, workspace_root: Path) -> dict:
    from fastapi.testclient import TestClient

    wizard_repo = workspace_root / "uDOS-wizard"
    sys.path.insert(0, str(wizard_repo))
    from wizard.main import app  # type: ignore

    client = TestClient(app)
    results = []
    for endpoint in offer.get("wizard_targets", []):
        path = endpoint["url"].replace("http://127.0.0.1:8787", "")
        response = client.get(path)
        payload = response.json()
        results.append(
            {
                "name": endpoint["name"],
                "path": path,
                "method": endpoint.get("method", "GET"),
                "status_code": response.status_code,
                "keys": sorted(payload.keys()),
                "payload": payload,
            }
        )

    probed = dict(offer)
    probed["local_wizard_probe"] = results
    return probed


def build_control_session_brief(offer: dict, probe_key: str = "runtime_probe") -> dict:
    probes = {item["name"]: item for item in offer.get(probe_key, [])}
    readiness = probes.get("runtime_ready", {}).get("payload", {})
    runtime_info = probes.get("runtime_info", {}).get("payload", {})
    dashboard = probes.get("dashboard_summary", {}).get("payload", {})
    launcher_status = probes.get("launcher_status", {}).get("payload", {})

    defaults = (
        dashboard.get("workspace_runtime", {})
        .get("components", {})
        .get("uhome", {})
        .get("defaults", {})
    )
    preferred_presentation = defaults.get("presentation", {}).get(
        "value",
        launcher_status.get("preferred_presentation"),
    )
    node_role = defaults.get("node_role", {}).get("value", launcher_status.get("node_role"))
    running = bool(launcher_status.get("running"))

    if not readiness.get("ok", False):
        recommended_action = "inspect_runtime"
    elif not running:
        recommended_action = "start_launcher"
    else:
        recommended_action = "maintain_session"

    control_brief = {
        "surface": offer["surface"],
        "runtime_status": readiness.get("status", "unknown"),
        "server_app": runtime_info.get("app", "unknown"),
        "recommended_action": recommended_action,
        "preferred_presentation": preferred_presentation,
        "node_role": node_role,
        "running": running,
        "available_targets": [target["name"] for target in offer.get("runtime_targets", [])],
    }

    if recommended_action == "start_launcher":
        control_brief["launch_request"] = {
            "target": "launcher_start",
            "presentation": preferred_presentation,
        }

    enriched = dict(offer)
    enriched["control_session_brief"] = control_brief
    return enriched


def build_remote_control_bridge_brief(offer: dict, probe_key: str = "local_wizard_probe") -> dict:
    probes = {item["name"]: item for item in offer.get(probe_key, [])}
    dispatch = probes.get("wizard_dispatch", {}).get("payload", {})
    bridge_brief = {
        "surface": offer.get("surface", "remote-control"),
        "recommended_action": "request_remote_dispatch" if dispatch else "wizard_unavailable",
        "provider": dispatch.get("provider", "unknown"),
        "executor": dispatch.get("executor", "unknown"),
        "transport": dispatch.get("transport", "unknown"),
        "surface_route": dispatch.get("surface", "remote-control"),
    }
    if dispatch:
        bridge_brief["dispatch_request"] = {
            "target": "wizard_dispatch",
            "task": dispatch.get("task", offer.get("surface", "remote-control")),
            "mode": dispatch.get("mode", "auto"),
            "surface": dispatch.get("surface", "remote-control"),
        }

    enriched = dict(offer)
    enriched["remote_control_bridge_brief"] = bridge_brief
    return enriched
