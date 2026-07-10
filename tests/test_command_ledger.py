"""ARK95X Command Ledger - Unit + Round-Trip Tests
Covers netx/signal_engine.py, netx/risk_calculator.py,
passive_income_engine.py, and ledger/command_ledger.py.
"""
import asyncio
import pytest

from netx.signal_engine import Signal, SignalBus
from netx.risk_calculator import RiskCalculator
from passive_income_engine import PassiveIncomeEngine
from ledger.command_ledger import CommandLedger


def make_signal(**overrides):
    defaults = dict(
        signal_id="sig-1", source="netx", symbol="BTCUSD", side="long",
        strategy="trend", entry_price=100.0, stop_price=95.0,
        timestamp="2026-07-10T00:00:00Z",
    )
    defaults.update(overrides)
    return Signal(**defaults)


class TestSignal:
    def test_valid_signal_serializes(self):
        s = make_signal()
        assert s.to_dict()["kind"] == "signal"
        assert s.to_dict()["symbol"] == "BTCUSD"

    def test_invalid_side_rejected(self):
        with pytest.raises(ValueError):
            make_signal(side="sideways")

    def test_invalid_prices_rejected(self):
        with pytest.raises(ValueError):
            make_signal(entry_price=0)

    def test_from_webhook_payload_normalizes(self):
        payload = {"symbol": "ETHUSD", "side": "SHORT", "entry_price": 50, "stop_price": 55}
        s = Signal.from_webhook_payload(payload)
        assert s.side == "short"
        assert s.raw == payload


class TestRiskCalculator:
    def test_position_size_formula(self):
        calc = RiskCalculator()
        signal = make_signal(entry_price=100.0, stop_price=95.0)
        order = calc.size_order(signal, account_capital=10000, risk_pct=1.0)
        assert order.approved
        assert order.max_loss_usd == pytest.approx(100.0)     # 10000 * 1%
        assert order.position_size == pytest.approx(20.0)     # 100 / 5
        assert order.notional_value == pytest.approx(2000.0)  # 20 * 100

    def test_rejects_excessive_risk_pct(self):
        calc = RiskCalculator(max_risk_pct=2.0)
        order = calc.size_order(make_signal(), account_capital=10000, risk_pct=5.0)
        assert not order.approved
        assert "risk_pct" in order.rejection_reason

    def test_rejects_zero_stop_distance(self):
        calc = RiskCalculator()
        signal = make_signal(entry_price=100.0, stop_price=100.0)
        order = calc.size_order(signal, account_capital=10000, risk_pct=1.0)
        assert not order.approved
        assert "stop_distance" in order.rejection_reason

    def test_rejects_oversized_notional(self):
        calc = RiskCalculator(max_risk_pct=5.0, max_position_notional_pct=10.0)
        signal = make_signal(entry_price=100.0, stop_price=99.0)
        order = calc.size_order(signal, account_capital=10000, risk_pct=2.0)
        assert not order.approved
        assert "notional_value" in order.rejection_reason


class TestPassiveIncomeEngine:
    def test_record_entry_updates_balance(self):
        engine = PassiveIncomeEngine(starting_balance=1000.0)
        entry = engine.record_entry(entry_type="realized_pnl", amount_usd=50.0, source_module="manual")
        assert engine.balance == 1050.0
        assert entry.balance_after_usd == 1050.0
        assert engine.total_pnl_usd == 50.0
        assert engine.roi_pct() == pytest.approx(5.0)

    def test_payback_status_transitions(self):
        engine = PassiveIncomeEngine(starting_balance=1000.0, breakeven_cost_usd=100.0)
        assert engine.payback_status() == "not_started"
        engine.record_entry(entry_type="realized_pnl", amount_usd=50.0, source_module="manual")
        assert engine.payback_status() == "in_progress"
        engine.record_entry(entry_type="realized_pnl", amount_usd=60.0, source_module="manual")
        assert engine.payback_status() == "achieved"

    def test_lossless_round_trip(self):
        """Snapshot/restore (encode/decode) must reproduce identical state."""
        engine = PassiveIncomeEngine(starting_balance=5000.0, breakeven_cost_usd=250.0)
        engine.record_entry(
            entry_type="realized_pnl", amount_usd=120.5, source_module="command_ledger",
            order_id="o1", signal_id="s1", symbol="BTCUSD",
        )
        engine.record_entry(entry_type="fee", amount_usd=-2.25, source_module="netx")

        encoded = engine.encode()
        restored = PassiveIncomeEngine.decode(encoded)

        assert restored.snapshot() == engine.snapshot()
        assert restored.balance == engine.balance
        assert restored.roi_pct() == pytest.approx(engine.roi_pct())
        assert restored.encode() == encoded  # re-encoding is byte-identical


class TestCommandLedger:
    def test_handle_signal_emits_telemetry(self):
        engine = PassiveIncomeEngine(starting_balance=10000.0)
        received = []

        async def on_telemetry(event):
            received.append(event)

        ledger = CommandLedger(engine=engine, risk_pct=1.0, on_telemetry=on_telemetry)
        order = asyncio.run(ledger.handle_signal(make_signal()))

        assert order.approved
        assert len(received) == 1
        assert received[0]["kind"] == "telemetry_event"
        assert received[0]["event_type"] == "leverage_update"
        assert received[0]["broadcast"] is True

    def test_close_order_records_real_pnl(self):
        engine = PassiveIncomeEngine(starting_balance=10000.0)
        received = []

        async def on_telemetry(event):
            received.append(event)

        ledger = CommandLedger(engine=engine, risk_pct=1.0, on_telemetry=on_telemetry)
        signal = make_signal(entry_price=100.0, stop_price=95.0, side="long")
        order = asyncio.run(ledger.handle_signal(signal))

        entry = asyncio.run(ledger.close_order_and_emit(order.order_id, exit_price=110.0))

        # position_size = 20 (see risk calculator test); pnl = 20 * (110 - 100) = 200
        assert entry.amount_usd == pytest.approx(200.0)
        assert engine.balance == pytest.approx(10200.0)
        assert received[-1]["event_type"] == "roi_update"
        assert received[-1]["ledger_snapshot"]["realized_pnl_usd"] == pytest.approx(200.0)

    def test_signal_bus_end_to_end(self):
        engine = PassiveIncomeEngine(starting_balance=10000.0)
        received = []

        async def on_telemetry(event):
            received.append(event)

        bus = SignalBus()
        ledger = CommandLedger(engine=engine, signal_bus=bus, on_telemetry=on_telemetry)

        async def scenario():
            task = asyncio.create_task(ledger.run())
            await asyncio.sleep(0)  # let run() reach subscribe() before we publish
            await bus.publish(make_signal())
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(scenario())
        assert len(received) == 1
        assert len(ledger.open_orders) == 1
