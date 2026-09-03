"""ARK95X NetX Signal Engine
Signal ingestion and pub/sub for the Command Ledger data flow.
Produces `signal` records matching contracts/ark-state.schema.json.
"""
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("ark95x.netx.signal_engine")

VALID_SIDES = {"long", "short", "buy", "sell", "flat"}


@dataclass
class Signal:
    """Mirrors the `signal` definition in contracts/ark-state.schema.json."""
    signal_id: str
    source: str
    symbol: str
    side: str
    strategy: str
    entry_price: float
    stop_price: float
    timestamp: str
    confidence: Optional[float] = None
    take_profit_price: Optional[float] = None
    timeframe: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    kind: str = "signal"

    def __post_init__(self):
        if self.side not in VALID_SIDES:
            raise ValueError(f"Invalid side '{self.side}', must be one of {VALID_SIDES}")
        if self.entry_price <= 0 or self.stop_price <= 0:
            raise ValueError("entry_price and stop_price must be > 0")

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "kind": self.kind,
            "signal_id": self.signal_id,
            "source": self.source,
            "symbol": self.symbol,
            "side": self.side,
            "strategy": self.strategy,
            "entry_price": self.entry_price,
            "stop_price": self.stop_price,
            "timestamp": self.timestamp,
        }
        if self.confidence is not None:
            d["confidence"] = self.confidence
        if self.take_profit_price is not None:
            d["take_profit_price"] = self.take_profit_price
        if self.timeframe is not None:
            d["timeframe"] = self.timeframe
        if self.raw:
            d["raw"] = self.raw
        return d

    @classmethod
    def from_webhook_payload(cls, payload: Dict[str, Any], source: str = "netx") -> "Signal":
        """Build a Signal from a raw NetX / n8n webhook POST body.

        Accepts loosely-typed upstream payloads and normalizes them into the
        strict `signal` contract, keeping the untouched original under `raw`.
        """
        return cls(
            signal_id=str(payload.get("signal_id") or payload.get("id") or uuid.uuid4()),
            source=payload.get("source", source),
            symbol=str(payload["symbol"]),
            side=str(payload["side"]).lower(),
            strategy=str(payload.get("strategy", "unknown")),
            entry_price=float(payload["entry_price"]),
            stop_price=float(payload["stop_price"]),
            timestamp=payload.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            confidence=payload.get("confidence"),
            take_profit_price=payload.get("take_profit_price"),
            timeframe=payload.get("timeframe"),
            raw=payload,
        )


class SignalBus:
    """In-process async pub/sub so command_ledger can subscribe to NetX signals."""

    def __init__(self):
        self._queues: List[asyncio.Queue] = []
        self.history: List[Signal] = []

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._queues:
            self._queues.remove(q)

    async def publish(self, signal: Signal):
        self.history.append(signal)
        logger.info(f"Signal published: {signal.signal_id} {signal.symbol} {signal.side}")
        for q in self._queues:
            await q.put(signal)

    async def listen(self, q: asyncio.Queue):
        """Async generator yielding signals as they arrive on a subscribed queue."""
        while True:
            signal = await q.get()
            yield signal
