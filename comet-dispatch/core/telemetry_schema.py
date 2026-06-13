# COMET OS — Telemetry Schema (Gate #10)
# Both teams must emit into this schema.
# ARK95X | AMARA.O1//ROOT | ARC.FLAME.ID-08AUG1993

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Literal, Optional, Any
import uuid
import json


@dataclass
class COMETEvent:
    """Unified telemetry event schema for all COMET crew actions."""

    # Core identifiers
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    crew_id: Literal["VANGUARD", "HERALD", "FORGE", "WRAITH", "COUNCIL", "SYSTEM"] = "SYSTEM"
    timestamp_iso: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Action classification
    action_type: Literal[
        "dispatch_suggestion",
        "route_registered",
        "model_classified",
        "data_extracted",
        "gate_status_change",
        "council_vote",
        "kill_switch_trigger",
        "boot_test_result",
        "surface_publish",
        "crew_deployed",
        "ambiguity_flagged",
        "roi_log"
    ] = "dispatch_suggestion"

    # Payload
    payload_json: Optional[dict] = None

    # Data integrity
    confidence_score: float = 0.0  # 0.0 - 1.0
    data_source: Literal["synthetic", "live", "unknown"] = "synthetic"

    # Authority flags
    ark95x_approval_required: bool = False
    kill_switch_candidate: bool = False  # True if confidence > 0.80 on synthetic

    # Context
    session_id: Optional[str] = None
    gate_number: Optional[int] = None  # Which gate this event contributes to
    surface: Optional[str] = None  # OWUI, Notion, ChatGPT, Gmail, Drive

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)

    def validate(self) -> list[str]:
        """Returns list of validation errors. Empty = valid."""
        errors = []
        if not (0.0 <= self.confidence_score <= 1.0):
            errors.append(f"confidence_score out of range: {self.confidence_score}")
        if self.data_source == "synthetic" and self.confidence_score > 0.80:
            errors.append(
                f"KILL SWITCH CANDIDATE: synthetic data with confidence {self.confidence_score:.2f} > 0.80. "
                "ARK95X approval required before auto-execution."
            )
            self.kill_switch_candidate = True
            self.ark95x_approval_required = True
        if self.payload_json is None:
            errors.append("payload_json is None — events must carry payload")
        return errors


class ROITracker:
    """Gate #11: ROITracker.log_task() receiving non-null data."""

    def __init__(self):
        self._log: list[dict] = []
        self._total_time_saved_min: float = 0.0

    def log_task(
        self,
        task_id: str,
        crew: str,
        time_saved_min: float,
        action_type: str,
        source: Literal["synthetic", "live"] = "synthetic"
    ) -> COMETEvent:
        """Log a completed task and its time-saved contribution."""
        if task_id is None or crew is None or time_saved_min is None:
            raise ValueError("ROITracker.log_task() received null data — Gate #11 FAIL")

        event = COMETEvent(
            crew_id=crew,
            action_type="roi_log",
            payload_json={
                "task_id": task_id,
                "crew": crew,
                "time_saved_min": time_saved_min,
                "action_type": action_type,
                "source": source,
            },
            confidence_score=0.95 if source == "live" else 0.50,
            data_source=source,
        )

        self._log.append(asdict(event))
        self._total_time_saved_min += time_saved_min
        return event

    @property
    def total_hours_saved(self) -> float:
        return self._total_time_saved_min / 60.0

    @property
    def weekly_target_met(self) -> bool:
        """Gate #25: North Star — >10 hours/week saved."""
        return self.total_hours_saved >= 10.0

    def summary(self) -> dict:
        return {
            "total_tasks_logged": len(self._log),
            "total_time_saved_min": self._total_time_saved_min,
            "total_hours_saved": self.total_hours_saved,
            "weekly_target_met": self.weekly_target_met,
            "data_source_breakdown": {
                "live": sum(1 for e in self._log if e["data_source"] == "live"),
                "synthetic": sum(1 for e in self._log if e["data_source"] == "synthetic"),
            },
        }


# Example usage
if __name__ == "__main__":
    tracker = ROITracker()

    # VANGUARD op
    e = tracker.log_task(
        task_id="OP-001",
        crew="VANGUARD",
        time_saved_min=45,
        action_type="route_clear",
        source="live"
    )
    errors = e.validate()
    if errors:
        print("VALIDATION ERRORS:", errors)
    else:
        print("Event valid:", e.event_id)

    print("ROI Summary:", json.dumps(tracker.summary(), indent=2))
    print("Gate #25 North Star met:", tracker.weekly_target_met)
