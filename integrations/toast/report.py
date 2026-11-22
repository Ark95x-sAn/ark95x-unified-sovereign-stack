"""Summarize Toast orders + cash into a structured daily baseline report."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional


@dataclass
class SalesDaySummary:
    business_date: str
    order_count: int = 0
    check_count: int = 0
    voided_order_count: int = 0
    deleted_order_count: int = 0
    excess_food_order_count: int = 0
    net_sales: float = 0.0
    tax_total: float = 0.0
    tip_total: float = 0.0
    payment_total: float = 0.0
    payment_by_type: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


@dataclass
class CashDaySummary:
    business_date: str
    entry_count: int = 0
    deposit_count: int = 0
    entries_net_amount: float = 0.0
    deposits_total: float = 0.0
    by_type: Dict[str, Dict[str, float]] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


@dataclass
class DailyBaselineReport:
    """Structured report printed by the CLI, then the process stops."""

    generated_at: str
    restaurant_guid_masked: str
    mode: str
    days: List[Dict[str, Any]] = field(default_factory=list)
    exclusions: List[str] = field(
        default_factory=lambda: [
            "inventory automation",
            "order adjustments (writes)",
            "bank sweeps",
            "velocity banking",
            "Home Assistant",
            "Frigate",
            "Alexa",
            "Beekeeper/hive.db",
            "write/mutation endpoints",
        ]
    )
    auth: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def business_dates_yesterday_and_today(
    today: Optional[date] = None,
) -> List[str]:
    """Return [yesterday, today] as Toast businessDate strings (yyyyMMdd)."""
    anchor = today or datetime.now(timezone.utc).date()
    yesterday = anchor - timedelta(days=1)
    return [_fmt_business_date(yesterday), _fmt_business_date(anchor)]


def mask_guid(guid: str) -> str:
    value = (guid or "").strip()
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}…{value[-4:]}"


def summarize_sales(
    business_date: str, orders: Iterable[Mapping[str, Any]]
) -> SalesDaySummary:
    """Approximate net sales per Toast orders API guidance (check.amount)."""
    summary = SalesDaySummary(business_date=business_date)
    payment_types: Counter[str] = Counter()
    payment_amounts: Dict[str, float] = {}

    for order in orders:
        summary.order_count += 1
        if order.get("voided") is True:
            summary.voided_order_count += 1
            continue
        if order.get("deleted") is True:
            summary.deleted_order_count += 1
            continue
        if order.get("excessFood") is True:
            summary.excess_food_order_count += 1
            continue

        checks = order.get("checks") or []
        if not isinstance(checks, list):
            continue
        for check in checks:
            if not isinstance(check, Mapping):
                continue
            if check.get("voided") is True or check.get("deleted") is True:
                continue
            summary.check_count += 1
            net = _net_sales_for_check(check)
            summary.net_sales += net
            summary.tax_total += _safe_float(check.get("taxAmount"))
            for payment in check.get("payments") or []:
                if not isinstance(payment, Mapping):
                    continue
                if payment.get("voidDate"):
                    continue
                tip = _safe_float(payment.get("tipAmount"))
                amount = _safe_float(payment.get("amount"))
                summary.tip_total += tip
                summary.payment_total += amount
                ptype = str(payment.get("type") or payment.get("cardType") or "UNKNOWN")
                payment_types[ptype] += 1
                payment_amounts[ptype] = payment_amounts.get(ptype, 0.0) + amount

    summary.payment_by_type = {
        key: round(value, 2) for key, value in sorted(payment_amounts.items())
    }
    summary.net_sales = round(summary.net_sales, 2)
    summary.tax_total = round(summary.tax_total, 2)
    summary.tip_total = round(summary.tip_total, 2)
    summary.payment_total = round(summary.payment_total, 2)
    summary.notes.append(
        "net_sales follows Toast guidance: start from check.amount, exclude "
        "voided/deleted/excessFood, deferred selections, house-account payoffs, "
        "fundraising service charges, and refund.refundAmount."
    )
    return summary


def summarize_cash(
    business_date: str,
    entries: Iterable[Mapping[str, Any]],
    deposits: Iterable[Mapping[str, Any]],
) -> CashDaySummary:
    summary = CashDaySummary(business_date=business_date)
    by_type: Dict[str, Dict[str, float]] = {}

    for entry in entries:
        summary.entry_count += 1
        amount = _safe_float(entry.get("amount"))
        summary.entries_net_amount += amount
        etype = str(entry.get("type") or "UNKNOWN")
        bucket = by_type.setdefault(etype, {"count": 0.0, "amount": 0.0})
        bucket["count"] += 1
        bucket["amount"] = round(bucket["amount"] + amount, 2)

    for deposit in deposits:
        summary.deposit_count += 1
        summary.deposits_total += _safe_float(deposit.get("amount"))

    summary.by_type = {key: by_type[key] for key in sorted(by_type)}
    summary.entries_net_amount = round(summary.entries_net_amount, 2)
    summary.deposits_total = round(summary.deposits_total, 2)
    summary.notes.append(
        "Cash flow from GET cashmgmt/v1/entries and cashmgmt/v1/deposits only."
    )
    return summary


def _net_sales_for_check(check: Mapping[str, Any]) -> float:
    amount = _safe_float(check.get("amount"))
    for selection in check.get("selections") or []:
        if not isinstance(selection, Mapping):
            continue
        if selection.get("deferred") is True:
            amount -= _safe_float(selection.get("price"))
        if selection.get("selectionType") == "HOUSE_ACCOUNT_PAY_BALANCE":
            amount -= _safe_float(selection.get("price"))
    for charge in check.get("appliedServiceCharges") or []:
        if not isinstance(charge, Mapping):
            continue
        if charge.get("serviceChargeCategory") == "FUNDRAISING_CAMPAIGN":
            amount -= _safe_float(charge.get("chargeAmount"))
    for payment in check.get("payments") or []:
        if not isinstance(payment, Mapping):
            continue
        refund = payment.get("refund")
        if isinstance(refund, Mapping):
            amount -= _safe_float(refund.get("refundAmount"))
    return amount


def _safe_float(value: Any) -> float:
    if value is None or value is False:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fmt_business_date(value: date) -> str:
    return value.strftime("%Y%m%d")
