"""ARK95X Passive Income Engine
Records real dollar ledger entries against a starting balance and exposes
the rollup numbers (total P&L, ROI%, payback status) that drive the
cockpit's ROI ledger and leverage meter.

Produces `ledger_entry` records matching contracts/ark-state.schema.json.
snapshot()/encode() and restore()/decode() are a lossless round-trip pair
(the EQCV-style state serialization pattern) so ledger state can be
persisted and rebuilt exactly.
"""
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field

logger = logging.getLogger("ark95x.passive_income_engine")

VALID_ENTRY_TYPES = {
    "realized_pnl", "unrealized_pnl", "fee", "funding",
    "deposit", "withdrawal", "adjustment",
}
VALID_SOURCE_MODULES = {
    "netx", "risk_calculator", "passive_income_engine",
    "smart_home_bridge", "command_ledger", "manual",
}
VALID_STATUSES = {"pending", "confirmed", "reconciled", "voided"}


@dataclass
class LedgerEntry:
    """Mirrors the `ledger_entry` definition in contracts/ark-state.schema.json."""
    entry_id: str
    type: str
    amount_usd: float
    balance_after_usd: float
    source_module: str
    status: str
    timestamp: str
    order_id: Optional[str] = None
    signal_id: Optional[str] = None
    symbol: Optional[str] = None
    notes: Optional[str] = None
    kind: str = "ledger_entry"

    def __post_init__(self):
        if self.type not in VALID_ENTRY_TYPES:
            raise ValueError(f"Invalid entry type '{self.type}'")
        if self.source_module not in VALID_SOURCE_MODULES:
            raise ValueError(f"Invalid source_module '{self.source_module}'")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{self.status}'")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}


class PassiveIncomeEngine:
    """Tracks real ledger entries and the running balance they produce."""

    def __init__(
        self,
        starting_balance: float,
        breakeven_cost_usd: float = 0.0,
        persist_path: Optional[str] = None,
    ):
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.breakeven_cost_usd = breakeven_cost_usd
        self.entries: List[LedgerEntry] = []
        self.persist_path = persist_path

        if persist_path and Path(persist_path).exists():
            restored = self.decode(Path(persist_path).read_text())
            self.starting_balance = restored.starting_balance
            self.balance = restored.balance
            self.breakeven_cost_usd = restored.breakeven_cost_usd
            self.entries = restored.entries
            logger.info(f"Restored ledger state from {persist_path} ({len(self.entries)} entries)")

    def record_entry(
        self,
        *,
        entry_type: str,
        amount_usd: float,
        source_module: str,
        order_id: Optional[str] = None,
        signal_id: Optional[str] = None,
        symbol: Optional[str] = None,
        status: str = "confirmed",
        notes: Optional[str] = None,
    ) -> LedgerEntry:
        self.balance += amount_usd
        entry = LedgerEntry(
            entry_id=str(uuid.uuid4()),
            type=entry_type,
            amount_usd=amount_usd,
            balance_after_usd=self.balance,
            source_module=source_module,
            status=status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            order_id=order_id,
            signal_id=signal_id,
            symbol=symbol,
            notes=notes,
        )
        self.entries.append(entry)
        logger.info(f"Ledger entry recorded: {entry.entry_id} {entry_type} ${amount_usd:.2f} -> balance ${self.balance:.2f}")
        if self.persist_path:
            path = Path(self.persist_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.encode())
        return entry

    @property
    def total_pnl_usd(self) -> float:
        return self.balance - self.starting_balance

    @property
    def realized_pnl_usd(self) -> float:
        return sum(e.amount_usd for e in self.entries if e.type == "realized_pnl")

    @property
    def unrealized_pnl_usd(self) -> float:
        return sum(e.amount_usd for e in self.entries if e.type == "unrealized_pnl")

    def roi_pct(self) -> float:
        if self.starting_balance <= 0:
            return 0.0
        return (self.total_pnl_usd / self.starting_balance) * 100.0

    def payback_status(self) -> str:
        if self.breakeven_cost_usd <= 0:
            return "achieved"
        if self.total_pnl_usd <= 0:
            return "not_started"
        if self.total_pnl_usd >= self.breakeven_cost_usd:
            return "achieved"
        return "in_progress"

    def leverage_ratio(self, open_notional_usd: float = 0.0) -> float:
        if self.balance <= 0:
            return 0.0
        return open_notional_usd / self.balance

    # ------------------------------------------------------------------
    # Lossless state round-trip (snapshot/restore, encode/decode)
    # ------------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        return {
            "starting_balance": self.starting_balance,
            "balance": self.balance,
            "breakeven_cost_usd": self.breakeven_cost_usd,
            "entries": [asdict(e) for e in self.entries],
        }

    def encode(self) -> str:
        return json.dumps(self.snapshot(), sort_keys=True)

    @classmethod
    def restore(cls, snapshot: Dict[str, Any]) -> "PassiveIncomeEngine":
        engine = cls(
            starting_balance=snapshot["starting_balance"],
            breakeven_cost_usd=snapshot.get("breakeven_cost_usd", 0.0),
        )
        engine.balance = snapshot["balance"]
        engine.entries = [LedgerEntry(**e) for e in snapshot["entries"]]
        return engine

    @classmethod
    def decode(cls, encoded: str) -> "PassiveIncomeEngine":
        return cls.restore(json.loads(encoded))
