"""ARK95X Devices Adapter
Scoped local execution against the docker-compose data stack
(docker-compose.yml's postgres/mongodb/redis/qdrant/n8n services).

Status checks (`check_service_status`) are a real but read-only
`docker compose ps` call -- observation, not mutation -- and report
directly through the control plane without a gate, matching devices'
"inventory"/"heartbeat" capabilities.

Restarting a service is real system mutation. It follows the same
request/approve shape as ledger/command_ledger.py's financial gate:
`request_restart` always queues for human approval (`system_mutation` is
in control_plane.APPROVAL_REQUIRED_ACTION_CLASSES), and only
`approve_pending_action` actually runs `docker compose restart` and
reports the real outcome back. Nothing here bypasses that gate.
"""
from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("ark95x.devices.local_exec")

CommandRunner = Callable[[list], "subprocess.CompletedProcess"]


class DevicesAdapter:
    """Approved local execution lane for the docker-compose data stack."""

    def __init__(
        self,
        control_plane: Any = None,
        repo_path: str = ".",
        runner: Optional[CommandRunner] = None,
    ):
        self.control_plane = control_plane
        self.repo_path = Path(repo_path)
        # Injectable so tests can prove the request/approve wiring without
        # depending on a live docker-compose stack; production callers get
        # a real subprocess by default.
        self._run: CommandRunner = runner or self._default_runner
        self._pending: Dict[str, Dict[str, Any]] = {}

    def _default_runner(self, args: list) -> "subprocess.CompletedProcess":
        return subprocess.run(args, cwd=self.repo_path, capture_output=True, text=True, timeout=30)

    def check_service_status(self, service_name: str) -> Dict[str, Any]:
        """Real, ungated `docker compose ps` observation."""
        try:
            result = self._run(["docker", "compose", "ps", service_name, "--format", "json"])
            reachable = result.returncode == 0
            output = result.stdout.strip()
        except Exception as exc:  # pragma: no cover - environment dependent
            reachable = False
            output = str(exc)

        payload = {
            "service": service_name,
            "reachable": reachable,
            "raw_output": output[:2000],
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.control_plane is not None:
            self.control_plane.report(
                agent_id="devices",
                status="online" if reachable else "unreachable",
                payload=payload,
            )
        return payload

    def request_restart(self, service_name: str) -> Dict[str, Any]:
        """Requests a real restart -- always queued for human approval."""
        if self.control_plane is None:
            raise ValueError("DevicesAdapter.request_restart requires a control_plane")

        request = self.control_plane.request_action(
            agent_id="devices",
            action=f"restart_service:{service_name}",
            action_class="system_mutation",
            payload={"service": service_name},
        )
        if request["disposition"] == "queued_for_human_approval":
            self._pending[request["request_id"]] = {"service": service_name}
        return request

    def approve_pending_action(self, request_id: str) -> Dict[str, Any]:
        """Executes a previously queued restart and reports the real
        outcome back to the control plane."""
        pending = self._pending.pop(request_id, None)
        if pending is None:
            raise KeyError(f"No pending device action for request_id {request_id}")

        service = pending["service"]
        try:
            result = self._run(["docker", "compose", "restart", service])
            succeeded = result.returncode == 0
            stdout, stderr = result.stdout, result.stderr
        except Exception as exc:  # pragma: no cover - environment dependent
            succeeded = False
            stdout, stderr = "", str(exc)

        payload = {
            "request_id": request_id,
            "service": service,
            "succeeded": succeeded,
            "stdout": stdout[-2000:],
            "stderr": stderr[-2000:],
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.control_plane is not None:
            self.control_plane.report(
                agent_id="devices",
                status="completed" if succeeded else "failed",
                payload=payload,
            )
        return payload
