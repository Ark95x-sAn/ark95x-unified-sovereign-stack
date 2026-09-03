"""ARK95X n8n Dispatch Adapter
The code-side mirror of workflows/ark_failover_dispatch_v1.json: that
workflow runs `router/failover.py` on an hourly trigger, then branches on
`result["status"]` to (a) commit+push ARK-STATE.json on a successful
dispatch, (b) alert on failure/no-backend, or (c) log on idle. This module
handles the exact same branching, but reports/gates through the control
plane instead of Discord/Sheets -- so the same dispatch result can be fed
through here whether it came from a live n8n instance's Execute Command
node or from calling router.failover.FailoverRouter.dispatch_next()
directly in-process.

n8n is transport, not the brain (docs/control-plane-pass-1.md invariant 7):
a successful dispatch's "commit + push ARK-STATE.json" step is a real
account-changing write to the repository's remote, so it is requested as
an `account_change` action -- always queued for human approval -- rather
than committed on n8n's own authority. Idle/failure/no-backend outcomes
are just evidence and are reported directly.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("ark95x.n8n.dispatch_adapter")


class N8nDispatchAdapter:
    """Reports/gates the outcome of one failover-dispatch workflow run."""

    def __init__(self, control_plane: Any = None):
        self.control_plane = control_plane
        self._pending: Dict[str, Dict[str, Any]] = {}

    def handle_dispatch_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Branches on router.failover.FailoverRouter.dispatch_next()'s
        result exactly like the n8n workflow's Check_Dispatch_Status
        switch node."""
        status = result.get("status")
        if status == "dispatched":
            return self._request_genome_commit(result)
        if status in ("no_backend_available", "dispatch_failed"):
            return self._report(status="alert", payload=result)
        return self._report(status="idle", payload=result)  # no_pending_tasks

    def _request_genome_commit(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if self.control_plane is None:
            return {"disposition": "no_control_plane", **result}

        request = self.control_plane.request_action(
            agent_id="n8n",
            action=f"commit_genome_update:{result.get('task_id')}",
            action_class="account_change",
            payload={
                "task_id": result.get("task_id"),
                "backend": result.get("backend"),
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        if request["disposition"] == "queued_for_human_approval":
            self._pending[request["request_id"]] = result
        return request

    def approve_pending_commit(self, request_id: str) -> Dict[str, Any]:
        """A human approves the genome commit+push; reports the outcome
        back through the control plane (the actual `git commit && git
        push` is workflows/ark_failover_dispatch_v1.json's
        Commit_Genome_Update node -- this records that it happened)."""
        pending = self._pending.pop(request_id, None)
        if pending is None:
            raise KeyError(f"No pending n8n dispatch commit for request_id {request_id}")

        payload = {
            "request_id": request_id,
            "task_id": pending.get("task_id"),
            "backend": pending.get("backend"),
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
        if self.control_plane is not None:
            self.control_plane.report(agent_id="n8n", status="completed", payload=payload)
        return payload

    def _report(self, status: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.control_plane is None:
            return None
        return self.control_plane.report(agent_id="n8n", status=status, payload=payload)
