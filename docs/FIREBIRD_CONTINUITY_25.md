# Pyrion Firebird: 25-feature continuity fusion

This draft layers an offline continuity queue beside the proposed Pyrion Core (PR #33). It does not merge or enable that Core. The pet stays a status surface. No unattended service, GitHub Action, GitLab pipeline, Trylle automation, or device adapter was activated.

## Selected 25 features

| Stage | Features | Current proof |
| --- | --- | --- |
| Intake | mission intake, entity firewall, acceptance check, deadline watch, source locator | source and entity required at queue admission; others contracts |
| Truth | claim status, contradiction hold | contracts awaiting source records |
| Team | worker registry, invocation binding, recipient binding, lease expiry, handoff receipt, replay detection | packet validator prototype in separate Firebird bridge; no authenticated worker transport |
| Action | scope allowlist, idempotency key, single writer claim, crash recovery, unknown write hold | read/draft scope enforced; expired claims held; no real lease fencing or action execution |
| Proof | artifact digest, readback gate | contracts awaiting executor artifact |
| Continuity | exception digest, priority queue, pause switch, checkpoint, lesson candidate | priority queue, pause switch and held count implemented; rest contracts |

## What works now

`companions/firebird_continuity.py` uses SQLite to persist a queue and event notes. `add` registers one sourced read/draft task; `pulse` returns the next due task and holds expired claims; `pause on` blocks the pulse. It never performs the task. `features` reports the feature names and `active_automations: 0`.

```bash
python -m unittest -v tests.test_firebird_continuity
python -m companions.firebird_continuity --db ./firebird.db add task-001 N95 "Review unresolved work" ledger-ref --scope read
python -m companions.firebird_continuity --db ./firebird.db pulse
```

## Repository fusion findings

- GitHub `ark95x-unified-sovereign-stack` PR #33 remains open and unmerged at `50503418c1e5ee14ba0441f28e7aa03619bc9268`. Its proposed Core explicitly sets `execution_permitted: false`.
- Connected GitLab project `bnordskog45-group/bnordskog45-project` contains README and CI template files; no Pyrion runtime was observed there. It is a potential future CI mirror, not a source of live capability.
- Trylle plugin 0.1.6 provides a `try` CLI skill, but `try` is not installed in the current runtime. No Trylle account or repository state was observed.
- GitHub's workflow syntax supports schedule and concurrency controls, but running this queue unattended requires an actual persistent host or configured automation, durable database storage, and a reliable notification destination. No schedule was configured here. Reference: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## Next acceptance gate

Add explicit lease acquisition and completion operations, authenticated worker identity, payload-bound digest, transactional single-writer fencing, restart replay, and a read-only adapter. Test two competing workers and an unknown external write. Only after those checks should a user-controlled schedule pulse a persistent host. No legal submission or money movement belongs in an unattended lane.
