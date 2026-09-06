"""Prepare a digest-bound draft for the existing Core; never release a mission."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

from .bridge import Store, canonical, private_write


def prepare(state):
    """The spool supplies evidence. Core retains mission state and authority."""
    snapshot = Store(state).status()
    evidence = {
        "schema": "network95.transport-observation.v1",
        "observed_at": snapshot["observed_at"],
        "validity": "historical observation only; recheck current receipts before routing",
        "audit": snapshot["audit"],
        "nodes": snapshot["nodes"],
        "evidence_coverage": snapshot["evidence_coverage"],
        "physical_identity_verified": False,
        "physical_deployment_verified": False,
        "execution_authority_granted": False,
    }
    digest = hashlib.sha256(canonical(evidence).encode()).hexdigest()
    mission = {
        "mission_id": "N95-BRIDGE-" + digest[:24],
        "idempotency_key": "transport-observation-" + digest,
        "title": "Review signed transport observations",
        "objective": "Compare local transport evidence with the actual device acceptance requirements.",
        "success_criteria": [
            "Match observation bytes to the source digest",
            "Preserve synthetic and physical-verification labels",
            "Identify missing target checks without granting execution authority",
        ],
        "mode": "draft",
        "data_class": "D1",
        "risk_level": "LOW",
        "priority": "normal",
        "requested_actions": ["read_authorized_internal", "draft", "validate_artifact"],
        "tags": ["command", "infrastructure"],
        "constraints": ["observation_sha256=" + digest, "draft_only", "no_device_promotion", "historical_snapshot_not_live_authority"],
        "unknowns": ["Physical node identity", "Cross-device execution", "PostgreSQL authority"],
        "budget": {"cost_cap_usd": 0, "time_cap_seconds": 60, "max_attempts": 1},
    }
    return {"status": "PREPARED_NOT_SUBMITTED", "source_sha256": digest,
            "observation": evidence, "mission": mission}


def validate_with_core(packet, core_root):
    """Exercise the recovered Core's real validation code in a disposable database."""
    root = Path(core_root).resolve()
    module_path = root / "src/n95_ops/engine.py"
    if not module_path.is_file() or not (root / "config/policy.json").is_file():
        raise ValueError("Core source and policy are required")
    source_digest = hashlib.sha256(canonical(packet["observation"]).encode()).hexdigest()
    if source_digest != packet["source_sha256"]:
        raise ValueError("observation digest mismatch")
    if "observation_sha256=" + source_digest not in packet["mission"]["constraints"]:
        raise ValueError("mission does not bind observation")
    if packet["mission"]["mode"] != "draft":
        raise ValueError("handoff must remain a draft")
    sys.path.insert(0, str(root / "src"))
    try:
        from n95_ops.engine import OperationsEngine
        loaded = Path(sys.modules["n95_ops.engine"].__file__).resolve()
        if loaded != module_path:
            raise ValueError("different Core module already loaded")
        with tempfile.TemporaryDirectory(prefix="n95-core-contract-") as temp:
            with OperationsEngine(Path(temp) / "contract.sqlite3", root / "config") as engine:
                normalized = engine.validate_mission(packet["mission"])
        return {"schema_accepted": True, "mission_submitted": False,
                "engine_sha256": hashlib.sha256(module_path.read_bytes()).hexdigest(),
                "normalized_mode": normalized["mode"]}
    finally:
        sys.path.pop(0)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--core-root", type=Path, help="Optional trusted existing Core source for schema validation")
    args = parser.parse_args(argv)
    output = args.output_dir.expanduser().resolve()
    if any((parent / ".git").exists() for parent in (output, *output.parents)):
        parser.error("private observations must be written outside a git checkout")
    packet = prepare(args.state)
    if args.core_root:
        packet["core_contract_check"] = validate_with_core(packet, args.core_root)
    encoded = canonical(packet) + "\n"
    # Full packet identity distinguishes exports with/without a Core contract check.
    packet_digest = hashlib.sha256(encoded.encode()).hexdigest()
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination = output / (packet_digest + ".json")
    if destination.exists():
        if destination.read_text(encoding="utf-8") != encoded:
            raise ValueError("existing export conflicts")
    else:
        private_write(destination, encoded)
    print(json.dumps({"status": packet["status"], "file": str(destination),
                      "sha256": packet_digest, "mission_submitted": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
