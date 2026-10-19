#!/usr/bin/env python3
"""n8n 7 Data Operations planner for Player 2.

Reads config/n8n_7_data_ops.json and generates workflow specs that can be
turned into n8n workflows later.

This intentionally does not export secrets or include credentials. It produces
plans, stage gates, and safe dispatch rules.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FACTORY = ROOT / "player2_skill_factory"
CONFIG = FACTORY / "config" / "n8n_7_data_ops.json"
OUTPUTS = FACTORY / "outputs"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_config() -> dict[str, Any]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def lane_to_workflow(lane: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": f"Player2 - {lane['id']}",
        "lane_id": lane["id"],
        "priority": lane["priority"],
        "safe_mode": lane["safe_mode"],
        "trigger": lane["trigger"],
        "source": lane["source"],
        "destination": lane["destination"],
        "player2_use": lane["player2_use"],
        "nodes": [
            {"id": "trigger", "type": "manual_or_schedule", "description": lane["trigger"]},
            {"id": "source", "type": "credentialed_source", "description": lane["source"]},
            {"id": "normalize", "type": "function", "description": "Normalize source payload into Player 2 signal schema"},
            {"id": "score", "type": "function", "description": "Score with impact/confidence/urgency/risk/complexity/cost"},
            {"id": "store", "type": "database", "description": lane["destination"]},
            {"id": "proof", "type": "file_or_database", "description": "Write proof manifest reference"},
            {"id": "review", "type": "human_gate", "description": "Require approval before external write or public action"},
        ],
        "data_fields": lane.get("data", []),
    }


def build_plan() -> dict[str, Any]:
    cfg = read_config()
    workflows = [lane_to_workflow(lane) for lane in cfg.get("data_lanes", [])]
    workflows.sort(key=lambda item: item["priority"], reverse=True)

    return {
        "generated_at": now(),
        "source_config": str(CONFIG.relative_to(ROOT)),
        "orchestrator": cfg["orchestrator"],
        "workflow_count": len(workflows),
        "workflows": workflows,
        "stage_gates": cfg["stage_gates"],
        "dispatch_policy": cfg["n8n_workflow_template"]["dispatch_policy"],
        "first_build_recommendation": workflows[0] if workflows else None,
    }


def write_markdown(plan: dict[str, Any]) -> None:
    md = "# n8n 7 Data Operations Plan\n\n"
    md += f"Generated: {plan['generated_at']}\n\n"
    md += f"Workflow count: {plan['workflow_count']}\n\n"
    md += f"Dispatch policy: {plan['dispatch_policy']}\n\n"
    md += "## First build recommendation\n\n"
    first = plan.get("first_build_recommendation")
    if first:
        md += f"**{first['name']}**\n\n"
        md += f"- Priority: {first['priority']}\n"
        md += f"- Safe mode: {first['safe_mode']}\n"
        md += f"- Source: {first['source']}\n"
        md += f"- Player 2 use: {first['player2_use']}\n\n"
    md += "## Workflows\n\n"
    for wf in plan["workflows"]:
        md += f"### {wf['name']}\n"
        md += f"- Priority: {wf['priority']}\n"
        md += f"- Safe mode: {wf['safe_mode']}\n"
        md += f"- Trigger: {wf['trigger']}\n"
        md += f"- Source: {wf['source']}\n"
        md += f"- Destination: {wf['destination']}\n"
        md += f"- Player 2 use: {wf['player2_use']}\n\n"
    (OUTPUTS / "n8n_7_data_ops_plan.md").write_text(md, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build n8n seven-data-ops workflow plan")
    parser.add_argument("command", choices=["plan", "first"])
    args = parser.parse_args()

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    plan = build_plan()
    write_json(OUTPUTS / "n8n_7_data_ops_plan.json", plan)
    write_markdown(plan)

    if args.command == "first":
        print(json.dumps(plan["first_build_recommendation"], indent=2, sort_keys=True))
    else:
        print(json.dumps({"ok": True, "workflow_count": plan["workflow_count"], "output": "player2_skill_factory/outputs/n8n_7_data_ops_plan.json"}, indent=2))


if __name__ == "__main__":
    main()
