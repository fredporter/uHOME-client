#!/usr/bin/env python3
"""Run a live-process smoke against a sibling uHOME-server instance."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_http(url: str, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1) as response:  # noqa: S310
                if response.status < 500:
                    return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def _server_python(server_repo: Path) -> str:
    candidate = Path.home() / ".udos" / "venv" / "uhome-server" / "bin" / "python"
    if candidate.exists():
        return str(candidate)
    return sys.executable


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    workspace_root = repo_root.parent
    server_repo = workspace_root / "uHOME-server"
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    health_url = f"{base_url}/api/runtime/ready"

    env = dict(os.environ)
    env["PYTHONPATH"] = str(server_repo / "src")

    process = subprocess.Popen(
        [
            _server_python(server_repo),
            "-m",
            "uvicorn",
            "uhome_server.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=server_repo,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_http(health_url)
        probe = subprocess.run(
            [
                sys.executable,
                str(repo_root / "scripts" / "smoke" / "session_offer.py"),
                "--json",
                "--probe",
                "--control-brief",
                "--server-url",
                base_url,
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode != 0:
            raise RuntimeError(probe.stderr or probe.stdout or "session offer probe failed")
        payload = json.loads(probe.stdout)
        print(json.dumps(payload, indent=2))
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
