"""ARK95X NetX Risk Calculator
Sizes a Signal into a risk-managed order.
position_size = account_capital * (risk_pct / 100) / stop_distance
Produces `risk_sized_order` records matching contracts/ark-state.schema.json.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from dataclasses import dataclass

from netx.signal_engine import Signal

logger = logging.getLogger("ark95x.netx.risk_calculator")


@dataclass
class RiskSizedOrder:
    """Mirrors the `risk_sized_order` definition in contracts/ark-state.schema.json."""
    order_id: str
    signal_id: str
    symbol: str
    side: str
    account_capital: float
    risk_pct: float
    stop_distance: float
    position_size: float
    max_loss_usd: float
    entry_price: float
    stop_price: float
    approved: bool
    timestamp: str
    notional_value: Optional[float] = None
    take_profit_price: Optional[float] = None
    rejection_reason: Optional[str] = None
    kind: str = "risk_sized_order"

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "kind": self.kind,
            "order_id": self.order_id,
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "side": self.side,
            "account_capital": self.account_capital,
            "risk_pct": self.risk_pct,
            "stop_distance": self.stop_distance,
            "position_size": self.position_size,
            "max_loss_usd": self.max_loss_usd,
            "entry_price": self.entry_price,
            "stop_price": self.stop_price,
            "approved": self.approved,
            "timestamp": self.timestamp,
        }
        if self.notional_value is not None:
            d["notional_value"] = self.notional_value
        if self.take_profit_price is not None:
            d["take_profit_price"] = self.take_profit_price
        if self.rejection_reason is not None:
            d["rejection_reason"] = self.rejection_reason
        return d


class RiskCalculator:
    """Position sizing gate: rejects orders that would risk more than allowed."""

    def __init__(self, max_risk_pct: float = 2.0, max_position_notional_pct: float = 50.0):
        self.max_risk_pct = max_risk_pct
        self.max_position_notional_pct = max_position_notional_pct

    def size_order(
        self,
        signal: Signal,
        account_capital: float,
        risk_pct: float,
    ) -> RiskSizedOrder:
        order_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        stop_distance = abs(signal.entry_price - signal.stop_price)

        if stop_distance <= 0:
            return RiskSizedOrder(
                order_id=order_id, signal_id=signal.signal_id, symbol=signal.symbol,
                side=signal.side, account_capital=account_capital, risk_pct=risk_pct,
                stop_distance=stop_distance, position_size=0.0, max_loss_usd=0.0,
                entry_price=signal.entry_price, stop_price=signal.stop_price,
                approved=False, timestamp=timestamp,
                rejection_reason="stop_distance must be > 0",
            )

        if risk_pct <= 0 or risk_pct > self.max_risk_pct:
            return RiskSizedOrder(
                order_id=order_id, signal_id=signal.signal_id, symbol=signal.symbol,
                side=signal.side, account_capital=account_capital, risk_pct=risk_pct,
                stop_distance=stop_distance, position_size=0.0, max_loss_usd=0.0,
                entry_price=signal.entry_price, stop_price=signal.stop_price,
                approved=False, timestamp=timestamp,
                rejection_reason=f"risk_pct must be in (0, {self.max_risk_pct}]",
            )

        max_loss_usd = account_capital * (risk_pct / 100.0)
        position_size = max_loss_usd / stop_distance
        notional_value = position_size * signal.entry_price

        max_notional = account_capital * (self.max_position_notional_pct / 100.0)
        if notional_value > max_notional:
            return RiskSizedOrder(
                order_id=order_id, signal_id=signal.signal_id, symbol=signal.symbol,
                side=signal.side, account_capital=account_capital, risk_pct=risk_pct,
                stop_distance=stop_distance, position_size=position_size,
                notional_value=notional_value, max_loss_usd=max_loss_usd,
                entry_price=signal.entry_price, stop_price=signal.stop_price,
                take_profit_price=signal.take_profit_price,
                approved=False, timestamp=timestamp,
                rejection_reason=(
                    f"notional_value {notional_value:.2f} exceeds "
                    f"{self.max_position_notional_pct}% of capital ({max_notional:.2f})"
                ),
            )

        order = RiskSizedOrder(
            order_id=order_id, signal_id=signal.signal_id, symbol=signal.symbol,
            side=signal.side, account_capital=account_capital, risk_pct=risk_pct,
            stop_distance=stop_distance, position_size=position_size,
            notional_value=notional_value, max_loss_usd=max_loss_usd,
            entry_price=signal.entry_price, stop_price=signal.stop_price,
            take_profit_price=signal.take_profit_price,
            approved=True, timestamp=timestamp,
        )
        logger.info(
            f"Order sized: {order.order_id} {order.symbol} size={position_size:.4f} "
            f"max_loss=${max_loss_usd:.2f}"
        )
        return order
