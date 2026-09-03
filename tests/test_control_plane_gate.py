"""ARK95X Control Plane <-> Command Ledger integration tests.
Proves the authority gate has real teeth: a financial action (closing a
position) does not move money until a human approves it through the
control plane, and the outcome reports back through the same plane.
"""
import asyncio

import pytest

from control_plane import build_default_control_plane
from netx.signal_engine import Signal
from netx.risk_calculator import RiskCalculator
from passive_income_engine import PassiveIncomeEngine
from ledger.command_ledger import CommandLedger


def make_signal(**overrides):
    defaults = dict(
        signal_id="sig-1", source="netx", symbol="BTCUSD", side="long",
        strategy="trend", entry_price=100.0, stop_price=95.0,
        timestamp="2026-09-03T00:00:00Z",
    )
    defaults.update(overrides)
    return Signal(**defaults)


def make_ledger(control_plane=None):
    engine = PassiveIncomeEngine(starting_balance=10000.0)
    ledger = CommandLedger(engine=engine, risk_calculator=RiskCalculator(), risk_pct=1.0, control_plane=control_plane)
    order = asyncio.run(ledger.handle_signal(make_signal()))
    return engine, ledger, order


class TestUngatedBehaviorUnchanged:
    def test_no_control_plane_executes_immediately(self):
        engine, ledger, order = make_ledger(control_plane=None)

        result = asyncio.run(ledger.request_close_order(order.order_id, exit_price=110.0))

        assert result["disposition"] == "executed_no_gate"
        assert engine.balance == pytest.approx(10200.0)  # 20 * (110-100)


class TestControlPlaneGate:
    def test_financial_action_queues_for_human_approval(self):
        plane = build_default_control_plane()
        engine, ledger, order = make_ledger(control_plane=plane)

        result = asyncio.run(ledger.request_close_order(order.order_id, exit_price=110.0))

        assert result["disposition"] == "queued_for_human_approval"
        assert "request_id" in result
        # Money has NOT moved yet -- this is the whole point of the gate.
        assert engine.balance == pytest.approx(10000.0)
        assert order.order_id in ledger.open_orders  # not yet closed, just queued

    def test_order_remains_open_until_approved(self):
        plane = build_default_control_plane()
        engine, ledger, order = make_ledger(control_plane=plane)

        asyncio.run(ledger.request_close_order(order.order_id, exit_price=110.0))

        # Since it's only queued, close_order() has not run yet, so the
        # order is still tracked as open.
        assert order.order_id in ledger.open_orders
        assert engine.balance == pytest.approx(10000.0)

    def test_approving_executes_and_reports_back_through_the_plane(self):
        plane = build_default_control_plane()
        engine, ledger, order = make_ledger(control_plane=plane)

        request = asyncio.run(ledger.request_close_order(order.order_id, exit_price=110.0))
        entry = asyncio.run(ledger.approve_pending_action(request["request_id"]))

        # Now the money has actually moved.
        assert entry.amount_usd == pytest.approx(200.0)
        assert engine.balance == pytest.approx(10200.0)
        assert order.order_id not in ledger.open_orders

        # And the control plane has a record of business_ops reporting completion.
        agent = plane.agents["business_ops"]
        assert agent.state == "completed"
        assert agent.last_report["entry_id"] == entry.entry_id
        assert agent.last_report["amount_usd"] == pytest.approx(200.0)

    def test_approving_unknown_request_id_raises(self):
        plane = build_default_control_plane()
        _, ledger, _ = make_ledger(control_plane=plane)

        with pytest.raises(KeyError):
            asyncio.run(ledger.approve_pending_action("not-a-real-request-id"))

    def test_two_pending_closures_are_independent(self):
        plane = build_default_control_plane()
        engine = PassiveIncomeEngine(starting_balance=10000.0)
        ledger = CommandLedger(engine=engine, risk_calculator=RiskCalculator(), risk_pct=1.0, control_plane=plane)

        order1 = asyncio.run(ledger.handle_signal(make_signal(signal_id="s1", symbol="BTCUSD")))
        order2 = asyncio.run(ledger.handle_signal(make_signal(signal_id="s2", symbol="ETHUSD", entry_price=50.0, stop_price=48.0)))

        req1 = asyncio.run(ledger.request_close_order(order1.order_id, exit_price=110.0))
        req2 = asyncio.run(ledger.request_close_order(order2.order_id, exit_price=55.0))

        # Approve only the second one.
        entry2 = asyncio.run(ledger.approve_pending_action(req2["request_id"]))

        assert order1.order_id in ledger.open_orders  # still pending, untouched
        assert order2.order_id not in ledger.open_orders  # executed
        assert entry2.symbol == "ETHUSD"
        assert req1["request_id"] in ledger._pending_closures  # req1 still awaiting approval
        assert req1["request_id"] != req2["request_id"]
