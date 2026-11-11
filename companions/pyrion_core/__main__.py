"""Command-line interface for the non-executing Pyrion policy engine."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import PyrionEngine


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m companions.pyrion_core")
    parser.add_argument("--ledger", required=True)
    parser.add_argument(
        "--trusted-actors",
        required=True,
        help="JSON file mapping trusted actor IDs to actor types",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    register = sub.add_parser("register")
    register.add_argument("mission")
    register.add_argument("--actor-id", default="human:ark95x")

    record = sub.add_parser("record")
    record.add_argument("event")

    assess = sub.add_parser("assess")
    assess.add_argument("--mission-id", required=True)
    assess.add_argument("--expected-head", required=True)
    assess.add_argument("--as-of")

    verify = sub.add_parser("verify-ledger")
    verify.add_argument("--expected-head")

    args = parser.parse_args()
    trusted_actors = load_json(args.trusted_actors)
    engine = PyrionEngine(args.ledger, trusted_actors)
    if args.command == "register":
        actor_type = trusted_actors.get(args.actor_id)
        result = engine.register_mission(
            load_json(args.mission),
            {"actor_id": args.actor_id, "actor_type": actor_type},
        )
    elif args.command == "record":
        result = engine.record_event(load_json(args.event))
    elif args.command == "assess":
        result = engine.assess(args.mission_id, args.expected_head, args.as_of)
    else:
        result = engine.verify_ledger(args.expected_head)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
