import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from client_adapter import (
    attach_runtime_targets,
    attach_wizard_targets,
    build_remote_runtime_bridge_brief,
    build_runtime_session_brief,
    build_offer,
    probe_local_server_app,
    probe_runtime_targets,
)


class SessionOfferTests(unittest.TestCase):
    def test_adapter_attaches_runtime_targets(self) -> None:
        offer = build_offer(REPO_ROOT, surface_name="remote-runtime-bridge")
        self.assertEqual(offer["version"], "v2.0.2")
        self.assertEqual(offer["foundation_version"], "v2.0.3")
        self.assertTrue(offer["runtime_service_source"].endswith("runtime-services.json"))
        self.assertEqual(offer["profile"], "remote-runtime-bridge")
        self.assertEqual(
            sorted(offer["family_modes"]),
            ["integrated-udos", "standalone-uhome"],
        )
        runtime_service_keys = {service["key"] for service in offer["runtime_services"]}
        self.assertIn("runtime.command-registry", runtime_service_keys)
        self.assertIn("runtime.capability-registry", runtime_service_keys)
        enriched = attach_runtime_targets(offer, base_url="http://runtime.local")
        target_names = [target["name"] for target in enriched["runtime_targets"]]
        self.assertIn("runtime_ready", target_names)
        self.assertIn("runtime_info", target_names)
        self.assertIn("dashboard_summary", target_names)
        self.assertIn("launcher_status", target_names)
        self.assertIn("household_status", target_names)
        wizarded = attach_wizard_targets(offer, wizard_url="http://wizard.local")
        self.assertEqual(wizarded["wizard_targets"], [])

    def test_adapter_probes_runtime_targets_with_stub_fetcher(self) -> None:
        offer = build_offer(REPO_ROOT, surface_name="shared-mobile-runtime")
        enriched = attach_runtime_targets(offer, base_url="http://runtime.local")

        def _fetch(url: str, method: str, payload) -> dict:
            return {"url": url, "method": method, "payload": payload, "ok": True}

        probed = probe_runtime_targets(enriched, fetcher=_fetch)
        self.assertEqual(len(probed["runtime_probe"]), len(enriched["runtime_targets"]))
        self.assertTrue(all(item["ok"] for item in probed["runtime_probe"]))
        self.assertIn("POST", [item["method"] for item in probed["runtime_probe"]])
        self.assertTrue(all("payload" in item for item in probed["runtime_probe"]))

    def test_adapter_probes_local_server_app(self) -> None:
        offer = build_offer(REPO_ROOT, surface_name="shared-mobile-runtime")
        enriched = attach_runtime_targets(offer, base_url="http://127.0.0.1:8000")
        probed = probe_local_server_app(enriched, workspace_root=REPO_ROOT.parent)
        self.assertEqual(len(probed["local_runtime_probe"]), len(enriched["runtime_targets"]))
        self.assertTrue(all(item["status_code"] == 200 for item in probed["local_runtime_probe"]))
        self.assertTrue(all("payload" in item for item in probed["local_runtime_probe"]))

    def test_runtime_session_brief_local_app_reflects_running_session(self) -> None:
        offer = build_offer(REPO_ROOT, surface_name="shared-tablet-runtime")
        enriched = attach_runtime_targets(offer, base_url="http://127.0.0.1:8000")
        probed = probe_local_server_app(enriched, workspace_root=REPO_ROOT.parent)
        briefed = build_runtime_session_brief(probed, probe_key="local_runtime_probe")
        brief = briefed["runtime_session_brief"]
        self.assertEqual(brief["profile"], "shared-tablet-runtime")
        self.assertEqual(brief["surface"], "living-room-kiosk")
        self.assertEqual(brief["runtime_status"], "ready")
        self.assertEqual(brief["recommended_action"], "maintain_session")
        self.assertIn("launcher_start", brief["available_targets"])
        self.assertTrue(brief["running"])

    def test_runtime_session_brief_recommends_launcher_start_when_not_running(self) -> None:
        offer = {
            "profile": "shared-tablet-runtime",
            "surface": "living-room-kiosk",
            "runtime_targets": [{"name": "launcher_start"}],
            "runtime_probe": [
                {"name": "runtime_ready", "payload": {"ok": True, "status": "ready"}},
                {"name": "runtime_info", "payload": {"app": "uHOME Server"}},
                {
                    "name": "dashboard_summary",
                    "payload": {
                        "workspace_runtime": {
                            "components": {
                                "uhome": {
                                    "defaults": {
                                        "presentation": {"value": "thin-gui"},
                                        "node_role": {"value": "server"},
                                    }
                                }
                            }
                        }
                    },
                },
                {"name": "launcher_status", "payload": {"running": False, "preferred_presentation": "thin-gui"}},
            ],
        }
        brief = build_runtime_session_brief(offer)["runtime_session_brief"]
        self.assertEqual(brief["recommended_action"], "start_launcher")
        self.assertEqual(brief["launch_request"]["presentation"], "thin-gui")

    def test_remote_runtime_bridge_brief_from_orchestration_probe_payload(self) -> None:
        offer = {
            "profile": "remote-runtime-bridge",
            "surface": "remote-control",
            "orchestration_contract_source": "/tmp/orchestration-contract.json",
            "local_wizard_probe": [
                {
                    "name": "orchestration_dispatch",
                    "payload": {
                        "dispatch_version": "v2.0.2",
                        "dispatch_id": "dispatch:test-1",
                        "provider": "test",
                        "executor": "test",
                        "transport": "http",
                        "request": {
                            "task": "remote-control",
                            "mode": "auto",
                            "surface": "remote-control",
                        },
                        "callback_contract": {"route": "/orchestration/callback"},
                    },
                },
                {
                    "name": "orchestration_workflow_plan",
                    "payload": {"plan_version": "v2.0.2", "step_count": 2},
                },
            ],
        }
        brief = build_remote_runtime_bridge_brief(offer)["remote_runtime_bridge_brief"]
        self.assertEqual(brief["recommended_action"], "request_remote_dispatch")
        self.assertEqual(brief["dispatch_version"], "v2.0.2")
        self.assertEqual(brief["dispatch_id"], "dispatch:test-1")
        self.assertEqual(brief["workflow_plan_version"], "v2.0.2")
        self.assertEqual(brief["workflow_step_count"], 2)
        self.assertEqual(brief["dispatch_request"]["target"], "orchestration_dispatch")
        self.assertEqual(brief["dispatch_request"]["surface"], "remote-control")
        self.assertEqual(brief["callback_contract"]["route"], "/orchestration/callback")
        self.assertEqual(brief["orchestration_contract_source"], "/tmp/orchestration-contract.json")

    def test_session_offer_script_renders_default_surface(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "smoke" / "session_offer.py"), "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["profile"], "shared-tablet-runtime")
        self.assertEqual(payload["surface"], "living-room-kiosk")
        self.assertEqual(payload["runtime_owner"], "uHOME-server")
        self.assertIn("session.launch", payload["capabilities"])
        self.assertEqual(payload["version"], "v2.0.2")
        self.assertEqual(payload["foundation_version"], "v2.0.3")
        self.assertTrue(payload["runtime_service_source"].endswith("runtime-services.json"))
        self.assertEqual(
            sorted(payload["deployment_modes"]),
            ["integrated-udos", "standalone-uhome"],
        )
        self.assertEqual(sorted(payload["app_targets"]), ["uHOME-app-android", "uHOME-app-ios"])
        self.assertIn("runtime_services", payload)
        self.assertIn("runtime_targets", payload)

    def test_session_offer_script_renders_remote_control_surface(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "smoke" / "session_offer.py"),
                "--surface",
                "remote-runtime-bridge",
                "--json",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["profile"], "remote-runtime-bridge")
        self.assertEqual(payload["transport"], "local-network")
        self.assertEqual(payload["shell_adapter"], "thin-kiosk")

    def test_session_offer_script_renders_control_brief(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "smoke" / "session_offer.py"),
                "--json",
                "--local-app",
                "--control-brief",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertIn("runtime_session_brief", payload)
        self.assertEqual(payload["runtime_session_brief"]["runtime_status"], "ready")

    def test_session_offer_script_renders_remote_bridge_brief(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "smoke" / "session_offer.py"),
                "--surface",
                "remote-runtime-bridge",
                "--json",
                "--wizard-local-app",
                "--remote-bridge-brief",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertIn("remote_runtime_bridge_brief", payload)
        self.assertEqual(payload["remote_runtime_bridge_brief"]["recommended_action"], "orchestration_unavailable")


if __name__ == "__main__":
    unittest.main()
