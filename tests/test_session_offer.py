import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class SessionOfferTests(unittest.TestCase):
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
