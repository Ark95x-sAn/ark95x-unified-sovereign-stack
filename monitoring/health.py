"""ARK95X Monitoring Adapter
Real health checks -- not decorative status flags -- reported through the
single control plane. Checks the command ledger's own reachability (does
`engine.balance` resolve without raising) and, best-effort, whether the
docker-compose data stack (postgres/redis/qdrant/mongodb) is accepting TCP
connections on its standard localhost ports.

Overall `status` is driven only by the ledger check: the data-stack ports
are informational evidence (`checks`) that will legitimately read False in
any environment that hasn't brought docker-compose up (e.g. CI), and that
is the honest result, not a bug to paper over. A caller that wants a strict
"every dependency must be up" verdict can inspect `checks` itself.
"""
from __future__ import annotations

import socket
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

DEFAULT_TARGETS: Dict[str, Tuple[str, int]] = {
    "postgres": ("localhost", 5432),
    "redis": ("localhost", 6379),
    "qdrant": ("localhost", 6333),
    "mongodb": ("localhost", 27017),
}


def _tcp_check(host: str, port: int, timeout: float = 1.5) -> bool:
    """Real TCP connect attempt -- true reachability, no mocking."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@dataclass
class HealthReport:
    status: str
    ledger_ok: Optional[bool]
    checks: Dict[str, bool] = field(default_factory=dict)
    checked_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _check_ledger(engine: Any) -> Optional[bool]:
    if engine is None:
        return None
    try:
        float(engine.balance)
        return True
    except Exception:
        return False


def run_health_check(
    engine: Any = None,
    targets: Optional[Dict[str, Tuple[str, int]]] = None,
    control_plane: Any = None,
) -> HealthReport:
    """Runs the real checks and, when a control_plane is given, reports the
    result back through it as `monitoring`'s heartbeat evidence."""
    targets = DEFAULT_TARGETS if targets is None else targets
    checks = {name: _tcp_check(host, port) for name, (host, port) in targets.items()}
    ledger_ok = _check_ledger(engine)
    status = "healthy" if ledger_ok is not False else "degraded"
    checked_at = datetime.now(timezone.utc).isoformat()

    report = HealthReport(status=status, ledger_ok=ledger_ok, checks=checks, checked_at=checked_at)

    if control_plane is not None:
        control_plane.report(
            agent_id="monitoring",
            status=status,
            payload={
                "evidence_ref": "health-check",
                "ledger_ok": ledger_ok,
                "data_stack_checks": checks,
                "observed_at": checked_at,
            },
        )

    return report
