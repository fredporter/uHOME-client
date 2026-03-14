import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from client_adapter import (
    attach_runtime_targets,
    build_offer,
    probe_local_server_app,
    probe_runtime_targets,
)


class SessionOfferTests(unittest.TestCase):
    def test_adapter_attaches_runtime_targets(self) -> None:
        offer = build_offer(REPO_ROOT, surface_name="remote-control")
        self.assertEqual(offer["version"], "v2.0.2")
        self.assertEqual(offer["foundation_version"], "v2.0.1")
        self.assertTrue(offer["runtime_service_source"].endswith("uDOS-core/contracts/runtime-services.json"))
        runtime_service_keys = {service["key"] for service in offer["runtime_services"]}
        self.assertIn("runtime.command-registry", runtime_service_keys)
        self.assertIn("runtime.capability-registry", runtime_service_keys)
        enriched = attach_runtime_targets(offer, base_url="http://runtime.local")
        target_names = [target["name"] for target in enriched["runtime_targets"]]
        self.assertIn("runtime_ready", target_names)
        self.assertIn("launcher_status", target_names)
        self.assertIn("household_status", target_names)

    def test_adapter_probes_runtime_targets_with_stub_fetcher(self) -> None:
        offer = build_offer(REPO_ROOT, surface_name="controller-browser")
        enriched = attach_runtime_targets(offer, base_url="http://runtime.local")

        def _fetch(url: str, method: str, payload) -> dict:
            return {"url": url, "method": method, "payload": payload, "ok": True}

        probed = probe_runtime_targets(enriched, fetcher=_fetch)
        self.assertEqual(len(probed["runtime_probe"]), len(enriched["runtime_targets"]))
        self.assertTrue(all(item["ok"] for item in probed["runtime_probe"]))
        self.assertIn("POST", [item["method"] for item in probed["runtime_probe"]])

    def test_adapter_probes_local_server_app(self) -> None:
        offer = build_offer(REPO_ROOT, surface_name="controller-browser")
        enriched = attach_runtime_targets(offer, base_url="http://127.0.0.1:8000")
        probed = probe_local_server_app(enriched, workspace_root=REPO_ROOT.parent)
        self.assertEqual(len(probed["local_runtime_probe"]), len(enriched["runtime_targets"]))
        self.assertTrue(all(item["status_code"] == 200 for item in probed["local_runtime_probe"]))

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
        self.assertEqual(payload["surface"], "living-room-kiosk")
        self.assertEqual(payload["runtime_owner"], "uHOME-server")
        self.assertIn("session.launch", payload["capabilities"])
        self.assertEqual(payload["version"], "v2.0.2")
        self.assertEqual(payload["foundation_version"], "v2.0.1")
        self.assertTrue(payload["runtime_service_source"].endswith("uDOS-core/contracts/runtime-services.json"))
        self.assertIn("runtime_services", payload)
        self.assertIn("runtime_targets", payload)

    def test_session_offer_script_renders_remote_control_surface(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "smoke" / "session_offer.py"),
                "--surface",
                "remote-control",
                "--json",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["transport"], "wizard-assisted")
        self.assertEqual(payload["shell_adapter"], "uDOS-shell")


if __name__ == "__main__":
    unittest.main()
