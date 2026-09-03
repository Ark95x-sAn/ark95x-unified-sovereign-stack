"""ARK95X Monitoring Adapter tests. Uses real TCP sockets (an actual bound
localhost server for the "up" case, an actual closed port for the "down"
case) rather than mocking socket.create_connection, so the check itself is
exercised for real."""
import socket
import contextlib

import pytest

from control_plane import build_default_control_plane
from monitoring.health import run_health_check


@contextlib.contextmanager
def open_tcp_port():
    """Binds a real listening socket on an ephemeral localhost port."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    try:
        yield server.getsockname()[1]
    finally:
        server.close()


def closed_port() -> int:
    """A real localhost port nothing is listening on."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()  # closed immediately -- nothing accepts connections here
    return port


class FakeEngine:
    def __init__(self, balance):
        self.balance = balance


class BrokenEngine:
    @property
    def balance(self):
        raise RuntimeError("ledger unreachable")


def test_reports_service_up_for_a_real_open_port():
    with open_tcp_port() as port:
        report = run_health_check(targets={"fake_service": ("127.0.0.1", port)})
    assert report.checks["fake_service"] is True


def test_reports_service_down_for_a_real_closed_port():
    port = closed_port()
    report = run_health_check(targets={"fake_service": ("127.0.0.1", port)})
    assert report.checks["fake_service"] is False


def test_status_healthy_when_ledger_reachable():
    report = run_health_check(engine=FakeEngine(10000.0), targets={})
    assert report.status == "healthy"
    assert report.ledger_ok is True


def test_status_degraded_when_ledger_unreachable():
    report = run_health_check(engine=BrokenEngine(), targets={})
    assert report.status == "degraded"
    assert report.ledger_ok is False


def test_status_healthy_with_no_engine_supplied():
    report = run_health_check(engine=None, targets={})
    assert report.status == "healthy"
    assert report.ledger_ok is None


def test_reports_through_the_control_plane():
    plane = build_default_control_plane()

    report = run_health_check(engine=FakeEngine(10000.0), targets={}, control_plane=plane)

    agent = plane.agents["monitoring"]
    assert agent.state == report.status
    assert agent.last_report["ledger_ok"] is True
    assert agent.live_adapter_state == "reporting"


def test_to_dict_round_trips_fields():
    report = run_health_check(engine=FakeEngine(1.0), targets={})
    d = report.to_dict()
    assert d["status"] == "healthy"
    assert d["ledger_ok"] is True
    assert "checked_at" in d
