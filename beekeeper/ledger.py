"""Beekeeper ledger — local SQLite state machine for agent tasks.

Any agent can log a command, receive a task_id, and route it to a named
agent via assign_task. No network listeners; filesystem SQLite only.
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from beekeeper.routing import route_to

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PACKAGE_DIR / "hive.db"
SCHEMA_PATH = PACKAGE_DIR / "schema.sql"

VALID_STATUSES = frozenset(
    {"queued", "assigned", "running", "done", "failed", "killed"}
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_task_id() -> str:
    return str(uuid.uuid4())


class HiveLedger:
    """Read/write API over hive.db (tasks table)."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Open a connection that always closes; inner with handles commit/rollback."""
        with closing(self.connect()) as conn:
            with conn:
                yield conn

    def init_db(self) -> Path:
        """Create hive.db and apply schema.sql. Returns db path."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        # executescript issues its own COMMIT; close without nested transaction.
        with closing(self.connect()) as conn:
            conn.executescript(schema)
        return self.db_path

    def log_command(
        self,
        raw_input: str,
        source: str,
        assigned_agent: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Insert a task. Returns task_id.

        If assigned_agent is set, status defaults to 'assigned' and the
        agent must be in the routing table. Otherwise status is 'queued'.
        """
        if not raw_input or not str(raw_input).strip():
            raise ValueError("raw_input must be non-empty")
        if not source or not str(source).strip():
            raise ValueError("source must be non-empty")

        agent: Optional[str] = None
        if assigned_agent is not None:
            agent = route_to(assigned_agent)
            resolved_status = status or "assigned"
        else:
            resolved_status = status or "queued"

        if resolved_status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status {resolved_status!r}. "
                f"Valid: {', '.join(sorted(VALID_STATUSES))}"
            )

        task_id = _new_task_id()
        now = _utc_now()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    task_id, source, raw_input, status,
                    assigned_agent, created_at, updated_at, result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    task_id,
                    source.strip(),
                    raw_input,
                    resolved_status,
                    agent,
                    now,
                    now,
                ),
            )
        return task_id

    def assign_task(self, task_id: str, agent: str) -> dict[str, Any]:
        """Route an existing task to a named agent; set status to assigned."""
        canonical = route_to(agent)
        return self.update_task(
            task_id,
            status="assigned",
            assigned_agent=canonical,
        )

    def update_task(
        self,
        task_id: str,
        *,
        status: Optional[str] = None,
        assigned_agent: Optional[str] = None,
        result: Optional[str] = None,
    ) -> dict[str, Any]:
        """Patch status, assigned_agent, and/or result. Raises KeyError if missing."""
        if status is not None and status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status {status!r}. "
                f"Valid: {', '.join(sorted(VALID_STATUSES))}"
            )
        agent_value: Optional[str] = None
        set_agent = False
        if assigned_agent is not None:
            agent_value = route_to(assigned_agent)
            set_agent = True

        fields: list[str] = []
        values: list[Any] = []
        if status is not None:
            fields.append("status = ?")
            values.append(status)
        if set_agent:
            fields.append("assigned_agent = ?")
            values.append(agent_value)
        if result is not None:
            fields.append("result = ?")
            values.append(result)

        if not fields:
            row = self.get_task(task_id)
            if row is None:
                raise KeyError(f"Unknown task_id: {task_id}")
            return row

        now = _utc_now()
        fields.append("updated_at = ?")
        values.append(now)
        values.append(task_id)

        with self._connection() as conn:
            cur = conn.execute(
                f"UPDATE tasks SET {', '.join(fields)} WHERE task_id = ?",
                values,
            )
            if cur.rowcount == 0:
                raise KeyError(f"Unknown task_id: {task_id}")

        row = self.get_task(task_id)
        if row is None:
            raise KeyError(f"Unknown task_id: {task_id}")
        return row

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        """Return one task as a dict, or None."""
        with self._connection() as conn:
            cur = conn.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (task_id,),
            )
            row = cur.fetchone()
        return dict(row) if row else None

    def list_tasks(
        self,
        *,
        status: Optional[str] = None,
        assigned_agent: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List tasks newest-first, optionally filtered."""
        clauses: list[str] = []
        values: list[Any] = []
        if status is not None:
            clauses.append("status = ?")
            values.append(status)
        if assigned_agent is not None:
            clauses.append("assigned_agent = ?")
            values.append(assigned_agent)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            f"SELECT * FROM tasks {where} "
            f"ORDER BY created_at DESC, rowid DESC LIMIT ?"
        )
        values.append(limit)

        with self._connection() as conn:
            cur = conn.execute(sql, values)
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def health(self) -> dict[str, Any]:
        """Lightweight health check: db exists and tasks table is readable."""
        ok = self.db_path.is_file()
        count = 0
        error: Optional[str] = None
        if ok:
            try:
                with self._connection() as conn:
                    cur = conn.execute("SELECT COUNT(*) FROM tasks")
                    count = int(cur.fetchone()[0])
            except sqlite3.Error as exc:
                ok = False
                error = str(exc)
        return {
            "ok": ok,
            "db_path": str(self.db_path),
            "task_count": count,
            "error": error,
        }
