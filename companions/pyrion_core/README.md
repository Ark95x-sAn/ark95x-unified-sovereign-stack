# Pyrion Core

Pyrion Core is the proof-gated mission runtime behind the Pyrion-95 Work pet. It turns an append-only stream of mission facts into a deterministic assessment, one bounded next-action proposal, and a truthful pet animation state. It deliberately does **not** execute commands, call networks, handle credentials, or mutate external systems.

## What it guarantees

- Closed mission and event schemas with strict validation.
- Trusted actor registry with role-sensitive authority checks.
- SHA-256 hash-chained JSONL ledger and required trusted-head anchoring.
- Revision-isolated replay under a process lock.
- Evidence, artifact, risk, prerequisite, and exact-scope approval gates.
- Completion-time approval validation, including expiry and post-hoc resistance.
- Deterministic readiness scores, reason codes, and exactly one next proposal.
- Honest pet telemetry: invalid or untrusted facts cannot trigger success motion.

## Pet state contract

| State | Meaning |
|---|---|
| `idle` | Ready, cancelled, or no eligible move |
| `running` | Safe work is available |
| `running-right` | Trusted evidence, artifact, or action progress landed |
| `running-left` | Rejection or risk requires recovery |
| `review` | Evidence or risk needs verification |
| `waiting` | Blocked or waiting for exact human approval |
| `failed` | An action failed |
| `jumping` | Verified mission milestone reached |

## Verify

From the repository root:

```bash
python -m compileall -q companions tests
python -m unittest -q tests.test_pyrion_core
```

The CLI requires a trusted-actor registry and, for assessment, the caller's expected full ledger-head hash:

```bash
python -m companions.pyrion_core \
  --ledger ./pyrion.jsonl \
  --trusted-actors ./trusted-actors.json \
  assess --mission-id mis.example --expected-head <64-hex-sha256>
```

The returned proposal always has `execution_permitted: false`. A separate, approval-aware executor may consume it, but it is outside this package's trust boundary.
