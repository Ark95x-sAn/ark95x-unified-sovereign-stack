# Beekeeper ledger

Local-first SQLite state machine (`hive.db`). Single source of truth for agent tasks. No network listeners.

## Init and smoke test

```sh
python -m beekeeper
```

Creates `beekeeper/hive.db`, inserts one task, assigns it to `Cursor`, prints the row.

```sh
python -m beekeeper health
python -m beekeeper init
```

## Python API

```python
from beekeeper import HiveLedger

ledger = HiveLedger()          # uses beekeeper/hive.db
ledger.init_db()

task_id = ledger.log_command(
    raw_input="build the dashboard",
    source="Operator",
)
ledger.assign_task(task_id, "Cursor")
task = ledger.get_task(task_id)
ledger.update_task(task_id, status="done", result="ok")
```

Statuses: `queued` | `assigned` | `running` | `done` | `failed` | `killed`

Known agents: Muse, Grokbot, Cursor, Jarvis, Crew, Operator (see `routing.py`).
