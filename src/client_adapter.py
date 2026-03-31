from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen
import sys


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_code_root(repo_root: Path) -> Path:
    candidate = repo_root.resolve()
    if candidate.name in {"uHOME-client", "uHOME-server", "uHOME-matter", "uHOME-app-android", "uHOME-app-ios"}:
        return candidate.parents[1]
    if candidate.name in {"uHOME-family", "uDOS-family", "sonic-family"}:
        return candidate.parent
    return candidate.parents[1]


def get_uhome_family_root(repo_root: Path) -> Path:
    candidate = repo_root.resolve()
    if candidate.name == "uHOME-family":
        return candidate
    explicit = os.environ.get("UHOME_FAMILY_ROOT") or os.environ.get("UDOS_UHOME_FAMILY_ROOT")
    if explicit:
        return Path(explicit)
    return get_code_root(candidate) / "uHOME-family"


def get_uhome_server_root(repo_root: Path) -> Path:
    return get_uhome_family_root(repo_root) / "uHOME-server"


def get_runtime_services_manifest_path(repo_root: Path) -> Path:
    env = os.environ.get("UHOME_RUNTIME_SERVICES_JSON", "").strip()
    if env:
        return Path(env)
    return repo_root / "src" / "runtime-services.json"


def load_runtime_services(repo_root: Path) -> tuple[dict, list[dict]]:
    manifest_path = get_runtime_services_manifest_path(repo_root)
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
        return "server endpoint coverage for app-consumed client runtime profiles"
    if key == "runtime.capability-registry":
        return "capability alignment between runtime profiles and kiosk routing"
    return "uHOME platform contract consumption"


def build_offer(repo_root: Path, surface_name: str | None = None) -> dict:
    runtime_contract = load_json(repo_root / "src" / "runtime-profile-contract.json")
    profile_map = load_json(repo_root / "src" / "runtime-profile-map.json")
    runtime_manifest, runtime_services = load_runtime_services(repo_root)

    profiles = profile_map["profiles"]
    if surface_name is None:
        profile = next(item for item in profiles if item["profile"] == runtime_contract["profile"])
    else:
        profile = next(
            item
            for item in profiles
            if item["profile"] == surface_name or item.get("surface_key") == surface_name
        )

    capabilities = sorted(set(runtime_contract["capability_profile"]) | set(profile["capability_profile"]))

    return {
        "version": runtime_manifest["version"],
        "foundation_version": profile_map["version"],
        "runtime_service_source": str(get_runtime_services_manifest_path(repo_root).resolve()),
        "family_modes": profile_map.get("family_modes", []),
        "profile": profile["profile"],
        "surface": profile["surface_key"],
        "transport": profile["transport"],
        "runtime_owner": profile["runtime_owner"],
        "shell_adapter": profile["shell_adapter"],
        "deployment_modes": profile.get("deployment_modes", []),
        "server_contract": runtime_contract["server_contract"],
        "app_targets": profile.get("app_targets", []),
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
    """Optional external orchestration targets (legacy name). Empty unless enabled explicitly."""
    enriched = dict(offer)
    targets = []
    contract_path_str = os.environ.get("UH_EXTERNAL_ORCHESTRATION_CONTRACT_PATH", "").strip()
    if offer.get("transport") == "orchestration-assisted" and contract_path_str:
        contract_source = Path(contract_path_str).resolve()
        contract = load_json(contract_source)
        routes = contract["routes"]
        surface = offer.get("surface", "remote-control")
        targets.append(
            {
                "name": "orchestration_dispatch",
                "url": f"{wizard_url}{routes['dispatch']['path']}?task={surface}&mode=auto&surface=remote-control",
                "method": routes["dispatch"]["method"],
            }
        )
        targets.append(
            {
                "name": "orchestration_workflow_plan",
                "url": f"{wizard_url}{routes['workflow_plan']['path']}?objective=shared-remote-flow&mode=auto",
                "method": routes["workflow_plan"]["method"],
            }
        )
        enriched["orchestration_contract_source"] = str(contract_source)
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

    server_repo = get_uhome_server_root(workspace_root)
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
    """Probe an optional external orchestration app; no uDOS checkout is implied."""
    _ = workspace_root
    probed = dict(offer)
    probed.setdefault("local_wizard_probe", [])
    return probed


def build_runtime_session_brief(offer: dict, probe_key: str = "runtime_probe") -> dict:
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

    runtime_brief = {
        "profile": offer.get("profile", offer["surface"]),
        "surface": offer["surface"],
        "runtime_status": readiness.get("status", "unknown"),
        "server_app": runtime_info.get("app", "unknown"),
        "recommended_action": recommended_action,
        "preferred_presentation": preferred_presentation,
        "node_role": node_role,
        "running": running,
        "available_targets": [target["name"] for target in offer.get("runtime_targets", [])],
        "app_targets": offer.get("app_targets", []),
    }

    if recommended_action == "start_launcher":
        runtime_brief["launch_request"] = {
            "target": "launcher_start",
            "presentation": preferred_presentation,
        }

    enriched = dict(offer)
    enriched["runtime_session_brief"] = runtime_brief
    return enriched


def build_remote_runtime_bridge_brief(offer: dict, probe_key: str = "local_wizard_probe") -> dict:
    probes = {item["name"]: item for item in offer.get(probe_key, [])}
    dispatch = probes.get("orchestration_dispatch", probes.get("wizard_dispatch", {})).get("payload", {})
    workflow_plan = probes.get(
        "orchestration_workflow_plan",
        probes.get("wizard_workflow_plan", {}),
    ).get("payload", {})
    contract_src = offer.get("orchestration_contract_source") or offer.get("wizard_contract_source")
    bridge_brief = {
        "profile": offer.get("profile", offer.get("surface", "remote-runtime-bridge")),
        "surface": offer.get("surface", "remote-control"),
        "recommended_action": "request_remote_dispatch" if dispatch else "orchestration_unavailable",
        "dispatch_version": dispatch.get("dispatch_version", "unknown"),
        "provider": dispatch.get("provider", "unknown"),
        "executor": dispatch.get("executor", "unknown"),
        "transport": dispatch.get("transport", "unknown"),
        "surface_route": dispatch.get("route_contract", {}).get("surface", dispatch.get("surface", "remote-control")),
        "workflow_plan_version": workflow_plan.get("plan_version", "unknown"),
        "workflow_step_count": workflow_plan.get("step_count", 0),
        "orchestration_contract_source": contract_src,
        "wizard_contract_source": contract_src,
    }
    if dispatch:
        bridge_brief["dispatch_request"] = {
            "target": "orchestration_dispatch",
            "task": dispatch.get("request", {}).get("task", offer.get("surface", "remote-control")),
            "mode": dispatch.get("request", {}).get("mode", "auto"),
            "surface": dispatch.get("request", {}).get("surface", "remote-control"),
        }
        bridge_brief["dispatch_id"] = dispatch.get("dispatch_id")
        bridge_brief["callback_contract"] = dispatch.get("callback_contract")

    enriched = dict(offer)
    enriched["remote_runtime_bridge_brief"] = bridge_brief
    return enriched


def build_control_session_brief(offer: dict, probe_key: str = "runtime_probe") -> dict:
    enriched = build_runtime_session_brief(offer, probe_key=probe_key)
    enriched["control_session_brief"] = enriched["runtime_session_brief"]
    return enriched


def build_remote_control_bridge_brief(offer: dict, probe_key: str = "local_wizard_probe") -> dict:
    enriched = build_remote_runtime_bridge_brief(offer, probe_key=probe_key)
    enriched["remote_control_bridge_brief"] = enriched["remote_runtime_bridge_brief"]
    return enriched
