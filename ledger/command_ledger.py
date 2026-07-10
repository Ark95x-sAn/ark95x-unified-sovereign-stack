"""ARK95X Command Ledger
Subscribes to NetX signals, sizes them through the risk calculator, records
real ledger entries via passive_income_engine, and emits telemetry_event
updates (ROI ledger + leverage meter + Aura state) for the cockpit.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, Optional, Tuple

from netx.signal_engine import Signal, SignalBus
from netx.risk_calculator import RiskCalculator, RiskSizedOrder
from passive_income_engine import PassiveIncomeEngine, LedgerEntry
from ledger.telemetry_event import TelemetryEvent

logger = logging.getLogger("ark95x.ledger.command_ledger")

TelemetryCallback = Callable[[Dict], Awaitable[None]]


class CommandLedger:
    """Orchestrates the signal -> risk -> ledger -> telemetry pipeline."""

    def __init__(
        self,
        engine: PassiveIncomeEngine,
        risk_calculator: Optional[RiskCalculator] = None,
        risk_pct: float = 1.0,
        signal_bus: Optional[SignalBus] = None,
        on_telemetry: Optional[TelemetryCallback] = None,
    ):
        self.engine = engine
        self.risk_calculator = risk_calculator or RiskCalculator()
        self.risk_pct = risk_pct
        self.signal_bus = signal_bus or SignalBus()
        self.on_telemetry = on_telemetry
        self.open_orders: Dict[str, RiskSizedOrder] = {}
        self._open_notional_usd = 0.0

    def size_signal(self, signal: Signal) -> RiskSizedOrder:
        order = self.risk_calculator.size_order(
            signal, account_capital=self.engine.balance, risk_pct=self.risk_pct
        )
        if order.approved:
            self.open_orders[order.order_id] = order
            self._open_notional_usd += order.notional_value or 0.0
        return order

    def close_order(self, order_id: str, exit_price: float) -> LedgerEntry:
        order = self.open_orders.pop(order_id, None)
        if order is None:
            raise KeyError(f"No open order with id {order_id}")
        self._open_notional_usd -= order.notional_value or 0.0
        direction = 1 if order.side in ("long", "buy") else -1
        pnl = order.position_size * (exit_price - order.entry_price) * direction
        return self.engine.record_entry(
            entry_type="realized_pnl",
            amount_usd=pnl,
            source_module="command_ledger",
            order_id=order.order_id,
            signal_id=order.signal_id,
            symbol=order.symbol,
            notes=f"closed {order.symbol} {order.side} at {exit_price}",
        )

    def build_telemetry_event(
        self, event_type: str = "roi_update", source_entry_id: Optional[str] = None
    ) -> TelemetryEvent:
        snapshot = {
            "total_pnl_usd": self.engine.total_pnl_usd,
            "realized_pnl_usd": self.engine.realized_pnl_usd,
            "unrealized_pnl_usd": self.engine.unrealized_pnl_usd,
            "roi_pct": self.engine.roi_pct(),
            "payback_status": self.engine.payback_status(),
            "leverage_ratio": self.engine.leverage_ratio(self._open_notional_usd),
            "open_risk_usd": self._open_notional_usd,
        }
        aura_state, intensity = self._derive_aura(snapshot)
        return TelemetryEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            ledger_snapshot=snapshot,
            aura_state=aura_state,
            intensity=intensity,
            source_entry_id=source_entry_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _derive_aura(snapshot: Dict) -> Tuple[str, float]:
        """Maps real P&L / leverage into the Aura flow/stress vocabulary."""
        roi = snapshot["roi_pct"]
        leverage = snapshot["leverage_ratio"]
        if leverage > 3.0:
            return "stress", min(1.0, leverage / 10.0)
        if roi > 20:
            return "surge", min(1.0, roi / 50.0)
        if roi > 0:
            return "flow", min(1.0, roi / 20.0)
        if roi < -20:
            return "drain", min(1.0, abs(roi) / 50.0)
        if roi < 0:
            return "stress", min(1.0, abs(roi) / 20.0)
        return "neutral", 0.0

    async def _emit(self, event: TelemetryEvent):
        event.broadcast = self.on_telemetry is not None
        if self.on_telemetry:
            await self.on_telemetry(event.to_dict())

    async def handle_signal(self, signal: Signal) -> RiskSizedOrder:
        order = self.size_signal(signal)
        event = self.build_telemetry_event(event_type="leverage_update")
        await self._emit(event)
        return order

    async def close_order_and_emit(self, order_id: str, exit_price: float) -> LedgerEntry:
        entry = self.close_order(order_id, exit_price)
        event = self.build_telemetry_event(event_type="roi_update", source_entry_id=entry.entry_id)
        await self._emit(event)
        return entry

    async def run(self):
        """Continuously consume signals published on the SignalBus."""
        q = self.signal_bus.subscribe()
        try:
            async for signal in self.signal_bus.listen(q):
                await self.handle_signal(signal)
        finally:
            self.signal_bus.unsubscribe(q)
