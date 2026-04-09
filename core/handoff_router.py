#!/usr/bin/env python3
"""ArcX Handoff Router - 9-Brain Council Task Distribution Engine"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("handoff_router")

class BrainID(Enum):
    GREY = "grey_01"
    BLACK = "black_02"
    RED = "red_03"
    GREEN = "green_04"
    BLUE = "blue_05"
    WHITE = "white_06"
    GOLD = "gold_07"
    VIOLET = "violet_08"
    SILVER = "silver_09"

BRAIN_CAPABILITIES = {
    BrainID.GREY: ["research", "intel", "extraction", "analysis"],
    BrainID.BLACK: ["security", "encryption", "threat_detection", "audit"],
    BrainID.RED: ["trading", "financial", "market_analysis", "alerts"],
    BrainID.GREEN: ["growth", "marketing", "outreach", "social"],
    BrainID.BLUE: ["legal", "compliance", "contracts", "disputes"],
    BrainID.WHITE: ["operations", "scheduling", "coordination", "logistics"],
    BrainID.GOLD: ["strategy", "planning", "architecture", "vision"],
    BrainID.VIOLET: ["creative", "design", "content", "branding"],
    BrainID.SILVER: ["monitoring", "health_check", "diagnostics", "recovery"]
}

BRAIN_PRIORITY = {
    BrainID.GREY: 1, BrainID.BLACK: 2, BrainID.RED: 3,
    BrainID.GREEN: 4, BrainID.BLUE: 5, BrainID.WHITE: 6,
    BrainID.GOLD: 7, BrainID.VIOLET: 8, BrainID.SILVER: 9
}

class Task:
    def __init__(self, task_id, category, payload, priority=5, source="user"):
        self.task_id = task_id
        self.category = category
        self.payload = payload
        self.priority = priority
        self.source = source
        self.timestamp = datetime.utcnow().isoformat()
        self.status = "pending"
        self.assigned_brain = None
        self.result = None

    def to_dict(self):
        return vars(self)

class HandoffRouter:
    def __init__(self):
        self.task_queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.completed: List[Task] = []
        self.brain_load: Dict[BrainID, int] = {b: 0 for b in BrainID}

    def route(self, task: Task) -> BrainID:
        candidates = []
        for brain, caps in BRAIN_CAPABILITIES.items():
            if task.category in caps:
                candidates.append(brain)
        if not candidates:
            candidates = [BrainID.GOLD]
        best = min(candidates, key=lambda b: (
            self.brain_load[b], BRAIN_PRIORITY[b]
        ))
        task.assigned_brain = best.value
        task.status = "routed"
        self.brain_load[best] += 1
        self.active_tasks[task.task_id] = task
        logger.info(f"Task {task.task_id} routed to {best.value}")
        return best

    def complete(self, task_id: str, result: dict):
        task = self.active_tasks.pop(task_id, None)
        if not task:
            return None
        task.status = "completed"
        task.result = result
        brain = BrainID(task.assigned_brain)
        self.brain_load[brain] = max(0, self.brain_load[brain] - 1)
        self.completed.append(task)
        return task

    def handoff(self, task_id: str, from_brain: str, to_brain: str, reason: str):
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        old_brain = BrainID(from_brain)
        new_brain = BrainID(to_brain)
        self.brain_load[old_brain] = max(0, self.brain_load[old_brain] - 1)
        self.brain_load[new_brain] += 1
        task.assigned_brain = to_brain
        logger.info(f"Handoff {task_id}: {from_brain} -> {to_brain} ({reason})")
        return task

    def status(self):
        return {
            "queued": len(self.task_queue),
            "active": len(self.active_tasks),
            "completed": len(self.completed),
            "brain_load": {b.value: l for b, l in self.brain_load.items()}
        }

if __name__ == "__main__":
    router = HandoffRouter()
    t = Task("test_001", "research", {"query": "sovereign stack deployment"})
    brain = router.route(t)
    print(f"Routed to: {brain.value}")
    print(json.dumps(router.status(), indent=2))
