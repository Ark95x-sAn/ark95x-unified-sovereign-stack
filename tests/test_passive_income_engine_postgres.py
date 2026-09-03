"""ARK95X Passive Income Engine - Postgres backend tests
Proves ledger state is durable across process restarts when backed by a
real Postgres database (the data stack's postgres service), not just a
JSON file. Skips gracefully if no Postgres is reachable -- this repo's CI
doesn't run docker-compose, so these only run where the data stack is up.
"""
import os

import pytest

from passive_income_engine import PassiveIncomeEngine

TEST_POSTGRES_URL = os.getenv(
    "TEST_POSTGRES_URL", "postgresql://ark95x:ark95x_pass@localhost:5432/sovereign"
)


def _postgres_available() -> bool:
    try:
        import psycopg2
    except ImportError:
        return False
    try:
        conn = psycopg2.connect(TEST_POSTGRES_URL, connect_timeout=2)
        conn.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _postgres_available(),
    reason="no live Postgres reachable at TEST_POSTGRES_URL -- start the data stack (docker compose up -d postgres) to run these",
)


@pytest.fixture
def clean_postgres():
    """Drops the ledger tables before and after each test for isolation."""
    import psycopg2

    def _drop():
        conn = psycopg2.connect(TEST_POSTGRES_URL)
        with conn, conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS ledger_entries, ledger_state")
        conn.close()

    _drop()
    yield
    _drop()


def test_postgres_backend_persists_across_process_restarts(clean_postgres):
    engine1 = PassiveIncomeEngine(
        starting_balance=10000.0, breakeven_cost_usd=500.0, postgres_url=TEST_POSTGRES_URL,
    )
    engine1.record_entry(entry_type="realized_pnl", amount_usd=250.0, source_module="command_ledger", symbol="BTCUSD")
    engine1.record_entry(entry_type="fee", amount_usd=-5.0, source_module="netx")

    # A brand new instance, same postgres_url -- simulates a process restart.
    # starting_balance=1.0 here should be IGNORED: Postgres is authoritative.
    engine2 = PassiveIncomeEngine(starting_balance=1.0, postgres_url=TEST_POSTGRES_URL)

    assert engine2.starting_balance == 10000.0
    assert engine2.balance == pytest.approx(10245.0)
    assert engine2.breakeven_cost_usd == 500.0
    assert len(engine2.entries) == 2
    assert engine2.total_pnl_usd == pytest.approx(245.0)
    assert engine2.roi_pct() == pytest.approx(2.45)


def test_postgres_backend_matches_json_backend_semantics(clean_postgres, tmp_path):
    """Same operations against JSON and Postgres backends must produce
    identical externally-observable results."""
    json_engine = PassiveIncomeEngine(
        starting_balance=5000.0, persist_path=str(tmp_path / "ledger.json"),
    )
    pg_engine = PassiveIncomeEngine(
        starting_balance=5000.0, postgres_url=TEST_POSTGRES_URL,
    )

    for engine in (json_engine, pg_engine):
        engine.record_entry(entry_type="realized_pnl", amount_usd=120.0, source_module="command_ledger", symbol="ETHUSD")
        engine.record_entry(entry_type="realized_pnl", amount_usd=-30.0, source_module="command_ledger", symbol="ETHUSD")

    assert json_engine.balance == pg_engine.balance
    assert json_engine.total_pnl_usd == pg_engine.total_pnl_usd
    assert json_engine.roi_pct() == pg_engine.roi_pct()
    assert len(json_engine.entries) == len(pg_engine.entries)


def test_postgres_data_is_queryable_with_plain_sql(clean_postgres):
    """The whole point: real SQL can see this data, not just this process."""
    import psycopg2

    engine = PassiveIncomeEngine(starting_balance=1000.0, postgres_url=TEST_POSTGRES_URL)
    entry = engine.record_entry(entry_type="deposit", amount_usd=500.0, source_module="manual")

    conn = psycopg2.connect(TEST_POSTGRES_URL)
    with conn, conn.cursor() as cur:
        cur.execute("SELECT amount_usd, balance_after_usd FROM ledger_entries WHERE entry_id = %s", (entry.entry_id,))
        row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == 500.0
    assert row[1] == 1500.0
