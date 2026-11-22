-- Beekeeper hive ledger — single source of truth for agent task state.
-- Local SQLite only. No network listeners.

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY NOT NULL,
    source TEXT NOT NULL,
    raw_input TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('queued', 'assigned', 'running', 'done', 'failed', 'killed')
    ),
    assigned_agent TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    result TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent ON tasks(assigned_agent);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
