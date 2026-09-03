"""ARK95X Passive Income Engine
Records real dollar ledger entries against a starting balance and exposes
the rollup numbers (total P&L, ROI%, payback status) that drive the
cockpit's ROI ledger and leverage meter.

Produces `ledger_entry` records matching contracts/ark-state.schema.json.
snapshot()/encode() and restore()/decode() are a lossless round-trip pair
(the EQCV-style state serialization pattern) so ledger state can be
persisted and rebuilt exactly, independent of which backend is used.

Two optional, independent persistence sinks:
  - persist_path: a JSON file (the original, still-supported backend)
  - postgres_url: a real Postgres database (ledger_state + ledger_entries
    tables), for when a JSON file on disk isn't durable/queryable enough.
If both are given, Postgres is authoritative for restore-on-init since
it's the durable store; JSON keeps being written on every entry too.
"""
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # pragma: no cover - psycopg2 is optional, only needed for postgres_url
    psycopg2 = None

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
        postgres_url: Optional[str] = None,
    ):
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.breakeven_cost_usd = breakeven_cost_usd
        self.entries: List[LedgerEntry] = []
        self.persist_path = persist_path
        self.postgres_url = postgres_url
        self._pg_conn = None

        if persist_path and Path(persist_path).exists():
            restored = self.decode(Path(persist_path).read_text())
            self.starting_balance = restored.starting_balance
            self.balance = restored.balance
            self.breakeven_cost_usd = restored.breakeven_cost_usd
            self.entries = restored.entries
            logger.info(f"Restored ledger state from {persist_path} ({len(self.entries)} entries)")

        if postgres_url:
            if psycopg2 is None:
                raise RuntimeError("postgres_url given but psycopg2 is not installed")
            self._pg_ensure_schema()
            restored_from_pg = self._pg_load_state()
            if restored_from_pg:
                logger.info(f"Restored ledger state from Postgres ({len(self.entries)} entries)")
            else:
                self._pg_save_initial_state()

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
        if self.postgres_url:
            self._pg_persist_entry(entry)
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

    # ------------------------------------------------------------------
    # Real persistent storage: Postgres, in place of a JSON file
    # ------------------------------------------------------------------
    def _pg_connection(self):
        if self._pg_conn is None or self._pg_conn.closed:
            self._pg_conn = psycopg2.connect(self.postgres_url)
        return self._pg_conn

    def _pg_ensure_schema(self):
        with self._pg_connection() as conn, conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ledger_state (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    starting_balance DOUBLE PRECISION NOT NULL,
                    balance DOUBLE PRECISION NOT NULL,
                    breakeven_cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0,
                    CONSTRAINT ledger_state_single_row CHECK (id = 1)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ledger_entries (
                    entry_id UUID PRIMARY KEY,
                    type TEXT NOT NULL,
                    amount_usd DOUBLE PRECISION NOT NULL,
                    balance_after_usd DOUBLE PRECISION NOT NULL,
                    source_module TEXT NOT NULL,
                    status TEXT NOT NULL,
                    "timestamp" TIMESTAMPTZ NOT NULL,
                    order_id TEXT,
                    signal_id TEXT,
                    symbol TEXT,
                    notes TEXT
                )
            """)

    def _pg_load_state(self) -> bool:
        """Loads state from Postgres if a ledger_state row exists. Returns
        True if state was restored, False if this is a fresh database."""
        with self._pg_connection() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT starting_balance, balance, breakeven_cost_usd FROM ledger_state WHERE id = 1")
            row = cur.fetchone()
            if row is None:
                return False
            self.starting_balance = row["starting_balance"]
            self.balance = row["balance"]
            self.breakeven_cost_usd = row["breakeven_cost_usd"]

            cur.execute("""
                SELECT entry_id, type, amount_usd, balance_after_usd, source_module,
                       status, "timestamp", order_id, signal_id, symbol, notes
                FROM ledger_entries ORDER BY "timestamp" ASC
            """)
            self.entries = [
                LedgerEntry(
                    entry_id=str(r["entry_id"]), type=r["type"], amount_usd=r["amount_usd"],
                    balance_after_usd=r["balance_after_usd"], source_module=r["source_module"],
                    status=r["status"], timestamp=r["timestamp"].isoformat(),
                    order_id=r["order_id"], signal_id=r["signal_id"], symbol=r["symbol"], notes=r["notes"],
                )
                for r in cur.fetchall()
            ]
            return True

    def _pg_save_initial_state(self):
        with self._pg_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ledger_state (id, starting_balance, balance, breakeven_cost_usd) "
                "VALUES (1, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                (self.starting_balance, self.balance, self.breakeven_cost_usd),
            )

    def _pg_persist_entry(self, entry: LedgerEntry):
        with self._pg_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ledger_entries "
                "(entry_id, type, amount_usd, balance_after_usd, source_module, status, "
                "\"timestamp\", order_id, signal_id, symbol, notes) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    entry.entry_id, entry.type, entry.amount_usd, entry.balance_after_usd,
                    entry.source_module, entry.status, entry.timestamp,
                    entry.order_id, entry.signal_id, entry.symbol, entry.notes,
                ),
            )
            cur.execute("UPDATE ledger_state SET balance = %s WHERE id = 1", (self.balance,))
