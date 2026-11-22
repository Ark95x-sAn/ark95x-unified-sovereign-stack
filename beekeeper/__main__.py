"""CLI health / smoke test for the Beekeeper ledger.

Usage:
  python -m beekeeper          # create DB, insert one task, read back
  python -m beekeeper health   # health check only
  python -m beekeeper init     # create schema only
"""

from __future__ import annotations

import json
import sys

from beekeeper.ledger import HiveLedger
from beekeeper.routing import list_agents


def cmd_init(ledger: HiveLedger) -> int:
    path = ledger.init_db()
    print(f"initialized {path}")
    return 0


def cmd_health(ledger: HiveLedger) -> int:
    if not ledger.db_path.is_file():
        ledger.init_db()
    report = ledger.health()
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


def cmd_smoke(ledger: HiveLedger) -> int:
    """Create DB, insert one task, assign, read back — exit 0 on success."""
    path = ledger.init_db()
    task_id = ledger.log_command(
        raw_input="beekeeper smoke test",
        source="beekeeper-cli",
    )
    ledger.assign_task(task_id, "Cursor")
    row = ledger.get_task(task_id)
    if row is None:
        print("FAIL: task not found after insert", file=sys.stderr)
        return 1

    expected = {
        "task_id": task_id,
        "source": "beekeeper-cli",
        "raw_input": "beekeeper smoke test",
        "status": "assigned",
        "assigned_agent": "Cursor",
    }
    for key, value in expected.items():
        if row.get(key) != value:
            print(
                f"FAIL: {key}={row.get(key)!r} expected {value!r}",
                file=sys.stderr,
            )
            return 1

    print(
        json.dumps(
            {
                "ok": True,
                "db_path": str(path),
                "agents": list_agents(),
                "task": row,
            },
            indent=2,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    command = args[0] if args else "smoke"
    ledger = HiveLedger()

    if command in {"smoke", "test"}:
        return cmd_smoke(ledger)
    if command == "health":
        return cmd_health(ledger)
    if command == "init":
        return cmd_init(ledger)
    if command in {"-h", "--help", "help"}:
        print(__doc__)
        return 0

    print(f"unknown command: {command}", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
