"""ARK95X Cockpit Telemetry Event
Mirrors the `telemetry_event` definition in contracts/ark-state.schema.json.
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

VALID_EVENT_TYPES = {"roi_update", "leverage_update", "aura_state", "agent_vote", "system_health"}
VALID_AURA_STATES = {"flow", "stress", "neutral", "surge", "drain"}


@dataclass
class TelemetryEvent:
    event_id: str
    event_type: str
    aura_state: str
    timestamp: str
    ledger_snapshot: Optional[Dict[str, Any]] = None
    intensity: Optional[float] = None
    source_entry_id: Optional[str] = None
    broadcast: bool = False
    kind: str = "telemetry_event"

    def __post_init__(self):
        if self.event_type not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type '{self.event_type}'")
        if self.aura_state not in VALID_AURA_STATES:
            raise ValueError(f"Invalid aura_state '{self.aura_state}'")

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "kind": self.kind,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aura_state": self.aura_state,
            "timestamp": self.timestamp,
            "broadcast": self.broadcast,
        }
        if self.ledger_snapshot is not None:
            d["ledger_snapshot"] = self.ledger_snapshot
        if self.intensity is not None:
            d["intensity"] = self.intensity
        if self.source_entry_id is not None:
            d["source_entry_id"] = self.source_entry_id
        return d
