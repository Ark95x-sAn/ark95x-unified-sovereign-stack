#!/usr/bin/env python3
"""Player 2 Skill Factory.

Turns repo maps + skill blueprints into generated skills, scored tasks,
SQLite state, and proof manifests.

Boundaries:
- local development only
- no live trading
- no credential harvesting
- no unauthorized access
- no network flooding
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FACTORY = ROOT / "player2_skill_factory"
STATE = ROOT / "state" / "player2_skill_factory"
GENERATED = FACTORY / "generated"
OUTPUTS = FACTORY / "outputs"
EVIDENCE = FACTORY / "evidence"
DB_PATH = STATE / "player2.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS repos (
    name TEXT PRIMARY KEY,
    full_name TEXT,
    clone_url TEXT,
    segment TEXT,
    lane TEXT,
    purpose TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS model_lanes (
    id TEXT PRIMARY KEY,
    role TEXT,
    safe_mode TEXT,
    use_for_json TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    target TEXT,
    safe_mode TEXT,
    triggers_json TEXT,
    source TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    intent TEXT,
    target TEXT,
    score REAL,
    command TEXT,
    status TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT,
    sha256 TEXT,
    kind TEXT,
    created_at TEXT
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def connect() -> sqlite3.Connection:
    STATE.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with connect() as con:
        con.executescript(SCHEMA)
    print(json.dumps({"ok": True, "db": str(DB_PATH)}))


def ingest_config() -> None:
    repo_cfg = read_json(FACTORY / "config" / "repositories.json")
    blueprint_cfg = read_json(FACTORY / "config" / "skill_blueprints.json")
    ts = now()

    with connect() as con:
        for repo in repo_cfg.get("repositories", []):
            con.execute(
                """INSERT INTO repos(name, full_name, clone_url, segment, lane, purpose, updated_at)
                   VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(name) DO UPDATE SET
                   full_name=excluded.full_name,
                   clone_url=excluded.clone_url,
                   segment=excluded.segment,
                   lane=excluded.lane,
                   purpose=excluded.purpose,
                   updated_at=excluded.updated_at""",
                (
                    repo["name"],
                    repo["full_name"],
                    repo["clone_url"],
                    repo["segment"],
                    repo["lane"],
                    repo.get("purpose", ""),
                    ts,
                ),
            )

        for lane in blueprint_cfg.get("model_lanes", []):
            con.execute(
                """INSERT INTO model_lanes(id, role, safe_mode, use_for_json, updated_at)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                   role=excluded.role,
                   safe_mode=excluded.safe_mode,
                   use_for_json=excluded.use_for_json,
                   updated_at=excluded.updated_at""",
                (lane["id"], lane["role"], lane["safe_mode"], json.dumps(lane.get("use_for", [])), ts),
            )

    print(json.dumps({"ok": True, "ingested": ["repositories", "model_lanes"]}))


def generate_skills() -> None:
    repo_cfg = read_json(FACTORY / "config" / "repositories.json")
    blueprint_cfg = read_json(FACTORY / "config" / "skill_blueprints.json")
    GENERATED.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    ts = now()
    generated: list[dict[str, Any]] = []

    for skill in blueprint_cfg.get("skills", []):
        generated.append({**skill, "type": "blueprint_skill", "source": "skill_blueprints.json", "generated_at": ts})

    for repo in repo_cfg.get("repositories", []):
        generated.append(
            {
                "id": f"repo_{repo['name'].replace('-', '_')}",
                "type": "repo_skill",
                "repo": repo["full_name"],
                "segment": repo["segment"],
                "lane": repo["lane"],
                "target": "codex" if repo["lane"] in {"operations", "unified", "orchestration"} else "python",
                "safe_mode": "workspace",
                "triggers": [repo["name"], repo["lane"], repo["segment"], "github", "repo"],
                "source": "repositories.json",
                "generated_at": ts,
            }
        )

    for skill in generated:
        write_json(GENERATED / f"{skill['id']}.skill.json", skill)

    with connect() as con:
        for skill in generated:
            con.execute(
                """INSERT INTO skills(id, target, safe_mode, triggers_json, source, updated_at)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                   target=excluded.target,
                   safe_mode=excluded.safe_mode,
                   triggers_json=excluded.triggers_json,
                   source=excluded.source,
                   updated_at=excluded.updated_at""",
                (
                    skill["id"],
                    skill.get("target", "plan"),
                    skill.get("safe_mode", "workspace"),
                    json.dumps(skill.get("triggers", [])),
                    skill.get("source", ""),
                    ts,
                ),
            )

    write_json(OUTPUTS / "generated_skills_report.json", {"count": len(generated), "generated_at": ts})
    print(json.dumps({"ok": True, "generated": len(generated), "dir": str(GENERATED)}))


def base_tasks() -> list[dict[str, Any]]:
    return [
        {"title": "Generate repo-derived skills", "target": "python", "impact": 9, "confidence": 9, "urgency": 9, "risk": 2, "complexity": 3, "cost": 1, "command": "python player2_skill_factory/player2_factory.py generate-skills"},
        {"title": "Build Player 2 router segment", "target": "codex", "impact": 10, "confidence": 7, "urgency": 8, "risk": 3, "complexity": 6, "cost": 2, "command": "codex --sandbox workspace-write"},
        {"title": "Audit generated skills", "target": "claude", "impact": 8, "confidence": 8, "urgency": 7, "risk": 2, "complexity": 4, "cost": 1, "command": "claude -p 'audit player2 skill factory'"},
        {"title": "Translate trading research into ops scoring", "target": "python", "impact": 8, "confidence": 7, "urgency": 6, "risk": 3, "complexity": 5, "cost": 1, "command": "python player2_skill_factory/player2_factory.py trading-map"},
        {"title": "Generate proof manifest", "target": "python", "impact": 7, "confidence": 10, "urgency": 7, "risk": 1, "complexity": 2, "cost": 1, "command": "python player2_skill_factory/player2_factory.py proof"},
    ]


def score_tasks(intent: str) -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    ranked: list[dict[str, Any]] = []
    words = [w.lower() for w in intent.split() if len(w) > 3]

    for task in base_tasks():
        score = (task["impact"] * task["confidence"] * task["urgency"]) - (task["risk"] + task["complexity"] + task["cost"])
        haystack = f"{task['title']} {task['target']} {task['command']}".lower()
        for word in words:
            if word in haystack:
                score += 20
        ranked.append({**task, "score": score})

    ranked.sort(key=lambda x: x["score"], reverse=True)
    top = ranked[0]

    with connect() as con:
        con.execute(
            """INSERT INTO tasks(title, intent, target, score, command, status, created_at, updated_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (top["title"], intent, top["target"], top["score"], top["command"], "open", now(), now()),
        )

    write_json(OUTPUTS / "ops_score_report.json", {"intent": intent, "ranked": ranked, "generated_at": now()})
    print(json.dumps({"top": top, "count": len(ranked)}, indent=2))


def trading_map() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    payload = {
        "boundary": "research/backtest-only; no live trading or financial advice",
        "translations": [
            {"trading": "signal", "operations": "action_trigger"},
            {"trading": "backtest", "operations": "historical_log_review"},
            {"trading": "drawdown", "operations": "time_money_energy_loss"},
            {"trading": "position_size", "operations": "effort_size"},
            {"trading": "portfolio_allocation", "operations": "project_allocation"},
            {"trading": "MAP-Elites", "operations": "skill_niche_exploration"},
        ],
        "formula": "(impact * confidence * urgency) - (risk + complexity + cost)",
        "generated_at": now(),
    }
    write_json(OUTPUTS / "trading_to_operations.json", payload)
    print(json.dumps(payload, indent=2))


def proof() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    for pattern in ("*.py", "*.json", "*.md", "*.yml", "*.yaml"):
        for path in FACTORY.rglob(pattern):
            if ".git" in path.parts:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            records.append({"path": str(path.relative_to(ROOT)), "sha256": digest, "bytes": path.stat().st_size})

    manifest = {"generated_at": now(), "db": str(DB_PATH), "file_count": len(records), "files": records}
    out = EVIDENCE / f"proof_manifest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    write_json(out, manifest)

    with connect() as con:
        for record in records:
            con.execute(
                "INSERT INTO evidence(path, sha256, kind, created_at) VALUES(?,?,?,?)",
                (record["path"], record["sha256"], "file_hash", now()),
            )

    print(json.dumps({"ok": True, "proof": str(out), "file_count": len(records)}))


def report() -> None:
    with connect() as con:
        counts = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ["repos", "model_lanes", "skills", "tasks", "evidence"]}
    print(json.dumps({"db": str(DB_PATH), "counts": counts}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Player 2 Skill Factory")
    parser.add_argument("command", choices=["init", "generate-skills", "score", "trading-map", "proof", "report"])
    parser.add_argument("--intent", default="build next highest-value automation")
    args = parser.parse_args()

    if args.command == "init":
        init_db(); ingest_config()
    elif args.command == "generate-skills":
        init_db(); ingest_config(); generate_skills()
    elif args.command == "score":
        init_db(); ingest_config(); generate_skills(); score_tasks(args.intent)
    elif args.command == "trading-map":
        trading_map()
    elif args.command == "proof":
        init_db(); proof()
    elif args.command == "report":
        init_db(); report()


if __name__ == "__main__":
    main()
