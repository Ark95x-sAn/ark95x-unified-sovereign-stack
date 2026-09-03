"""ARK95X Command Ledger
Subscribes to NetX signals, sizes them through the risk calculator, records
real ledger entries via passive_income_engine, and emits telemetry_event
updates (ROI ledger + leverage meter + Aura state) for the cockpit.

When a control_plane is supplied, closing a position (a "financial" action
under control_plane's authority invariants) is gated: it is queued for
human approval instead of executing immediately, and only recorded once
approve_pending_action() is called. This is the "next adjustment pass"
docs/control-plane-pass-1.md calls for -- the ledger is where an approved
control-plane action actually moves real money.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from netx.signal_engine import Signal, SignalBus
from netx.risk_calculator import RiskCalculator, RiskSizedOrder
from passive_income_engine import PassiveIncomeEngine, LedgerEntry
from ledger.telemetry_event import TelemetryEvent
from control_plane import ControlPlane

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
        control_plane: Optional[ControlPlane] = None,
        requesting_agent_id: str = "business_ops",
    ):
        self.engine = engine
        self.risk_calculator = risk_calculator or RiskCalculator()
        self.risk_pct = risk_pct
        self.signal_bus = signal_bus or SignalBus()
        self.on_telemetry = on_telemetry
        self.control_plane = control_plane
        self.requesting_agent_id = requesting_agent_id
        self.open_orders: Dict[str, RiskSizedOrder] = {}
        self._open_notional_usd = 0.0
        self._pending_closures: Dict[str, Dict[str, Any]] = {}

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

    async def request_close_order(self, order_id: str, exit_price: float) -> Dict[str, Any]:
        """Closes a position immediately if ungated, or queues it for human
        approval when a control_plane is attached (financial actions always
        require approval under control_plane's authority invariants)."""
        if order_id not in self.open_orders:
            raise KeyError(f"No open order with id {order_id}")

        if self.control_plane is None:
            entry = await self.close_order_and_emit(order_id, exit_price)
            return {"disposition": "executed_no_gate", "entry": entry.to_dict()}

        order = self.open_orders[order_id]
        request = self.control_plane.request_action(
            agent_id=self.requesting_agent_id,
            action=f"close_order:{order_id}",
            action_class="financial",
            payload={
                "order_id": order_id,
                "exit_price": exit_price,
                "symbol": order.symbol,
                "side": order.side,
                "position_size": order.position_size,
            },
        )

        if request["disposition"] == "queued_for_human_approval":
            self._pending_closures[request["request_id"]] = {
                "order_id": order_id,
                "exit_price": exit_price,
            }
        elif request["disposition"] == "queued_for_control_plane":
            # Not a consequential action class under this control plane's
            # current rules -- safe to execute without a human in the loop.
            entry = await self.close_order_and_emit(order_id, exit_price)
            self.control_plane.report(
                agent_id=self.requesting_agent_id,
                status="completed",
                payload={"request_id": request["request_id"], "entry_id": entry.entry_id},
            )
            request = dict(request, executed=True, entry=entry.to_dict())
        # "rejected_out_of_scope": nothing to execute; return the rejection as-is.

        return request

    async def approve_pending_action(self, request_id: str) -> LedgerEntry:
        """Executes a previously queued close_order request and reports the
        real outcome back to the control plane."""
        pending = self._pending_closures.pop(request_id, None)
        if pending is None:
            raise KeyError(f"No pending closure for request_id {request_id}")

        entry = await self.close_order_and_emit(pending["order_id"], pending["exit_price"])

        if self.control_plane is not None:
            self.control_plane.report(
                agent_id=self.requesting_agent_id,
                status="completed",
                payload={
                    "request_id": request_id,
                    "evidence_ref": entry.entry_id,
                    "entry_id": entry.entry_id,
                    "amount_usd": entry.amount_usd,
                    "observed_at": entry.timestamp,
                },
            )

        return entry

    async def run(self):
        """Continuously consume signals published on the SignalBus."""
        q = self.signal_bus.subscribe()
        try:
            async for signal in self.signal_bus.listen(q):
                await self.handle_signal(signal)
        finally:
            self.signal_bus.unsubscribe(q)
