"""ARK95X Memory Cortex Adapter
Proposes real patches to ARK-STATE.json -- a new `known_gaps` entry, or a
new `todo_queue` task -- through the control plane instead of writing the
genome directly.

`memory_update` is deliberately absent from
control_plane.APPROVAL_REQUIRED_ACTION_CLASSES, so a proposal auto-queues
as `queued_for_control_plane` rather than `queued_for_human_approval`. This
adapter is what actually applies the patch once the plane accepts it, and
reports the real outcome back -- matching
docs/control-plane-pass-1.md's invariant 6: "Memory Cortex proposes
changes; the control plane accepts or rejects them."
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("ark95x.memory_cortex.proposals")

DEFAULT_STATE_PATH = "ARK-STATE.json"


class MemoryCortexAdapter:
    """Gate around real writes to ARK-STATE.json's memory (known_gaps,
    todo_queue), routed through a ControlPlane."""

    def __init__(self, control_plane: Any, state_path: str = DEFAULT_STATE_PATH):
        self.control_plane = control_plane
        self.state_path = Path(state_path)

    def propose_known_gap(self, gap: str) -> Dict[str, Any]:
        """Proposes appending one sentence to ARK-STATE.json's known_gaps."""
        return self._propose(
            action=f"add_known_gap:{gap[:60]}",
            payload={"patch_type": "known_gaps_add", "value": gap},
        )

    def propose_todo_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Proposes appending one task dict to ARK-STATE.json's todo_queue."""
        return self._propose(
            action=f"add_todo_task:{task.get('id')}",
            payload={"patch_type": "todo_queue_add", "value": task},
        )

    def _propose(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = self.control_plane.request_action(
            agent_id="memory_cortex",
            action=action,
            action_class="memory_update",
            payload=payload,
        )

        if request["disposition"] == "queued_for_control_plane":
            applied = self._apply_patch(payload)
            self.control_plane.report(
                agent_id="memory_cortex",
                status="accepted" if applied else "rejected_duplicate",
                payload={
                    "request_id": request["request_id"],
                    "patch_type": payload["patch_type"],
                    "applied": applied,
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            request = dict(request, executed=applied, applied=applied)

        return request

    def _apply_patch(self, payload: Dict[str, Any]) -> bool:
        """Writes the real ARK-STATE.json (or whichever state_path this
        adapter was built with). Returns False for a no-op duplicate."""
        state = json.loads(self.state_path.read_text())
        patch_type = payload["patch_type"]

        if patch_type == "known_gaps_add":
            gaps = state.setdefault("known_gaps", [])
            if payload["value"] in gaps:
                return False
            gaps.append(payload["value"])
        elif patch_type == "todo_queue_add":
            queue = state.setdefault("todo_queue", [])
            task = payload["value"]
            if any(t.get("id") == task.get("id") for t in queue):
                return False
            queue.append(task)
        else:
            logger.warning("Unknown memory patch_type: %s", patch_type)
            return False

        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.state_path.write_text(json.dumps(state, indent=2) + "\n")
        return True
