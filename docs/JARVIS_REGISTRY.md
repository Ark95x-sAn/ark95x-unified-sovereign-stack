# Jarvis Registry

## 2026-09-06 — N95 native integration increment

- **Crew:** source reviewers (AI/data and operations), native bridge builder, legacy mesh fixer, independent security reviewer, Windows preflight builder; one root synthesis owner.
- **Repository/tool:** this existing stack; recovered Network-95 Core 1.4.0 used only for its real mission-schema validator. Candidate catalogue reviews 25 upstream projects; no upstream source trees or private user records copied into the bridge.
- **Layers:** tools/interfaces, security/policy, dashboard/observability, data, device coordination and service design.
- **Action:** implemented per-node signed telemetry, durable transport receipts, freshness-aware eligibility, bounded polling and digest-bound Core draft export. Fixed legacy false online/delivery/failover behavior. Prepared native Windows audit, 25-project review, 9×9 capability map and three installation offers.
- **Files:** `n95_native/`, `core/device_mesh.py`, three focused test modules, `tools/N95-Native-Preflight.ps1`, `.github/workflows/native-bridge.yml`, `.gitignore`, README and `docs/N95_*`.
- **Risk:** Yellow for original code, local fixture server and prepared files. No production deployment, model invocation, raw personal-data ingestion, message sending or upstream dependency installation. Windows script performs read-only checks when run locally.
- **Review:** fixed independent findings for HTTP redirect credential forwarding and mixed database snapshots; exported status now retains evaluation/expiry metadata and historical-only semantics. HMAC, audit-chain and physical-proof limitations remain explicit.
- **Validation:** 33 focused cases and 6 subtests passed on Linux. Actual loopback HTTP recorded three synthetic identities; two bounded polling cycles produced two further receipts; fresh Store reopened and checked all five. Exported draft was accepted by recovered Core's actual schema validator in a disposable database, with no submission or execution. See `N95_VERIFICATION.json`.
- **Test command:** `python -m pytest -q tests/test_native_bridge.py tests/test_core_handoff.py tests/test_device_mesh.py`.
- **Remaining gate:** Windows parsing/runtime, physical identity, native installation, PostgreSQL transaction acceptance, encrypted inter-device transport and actual local-model jobs are not proved by these checks. The selected Core C1–C6 dependency order remains active.
- **Next move:** run the role-specific native preflight on GM700/RTX/Surface through an authenticated native session; implement C1 transactions and identity before production mission operation. Complete one folder-to-brief workflow and recovery proof before selling the proposed packages.

This file is the durable project index for tools, repos, workflows, decisions, and next actions.

## Review Template

```text
Name:
URL:
Layer:
Purpose:
Install method:
Runs locally:
External dependency:
Required ports:
Risk notes:
First test:
Decision:
Reason:
```

## Layers

- Brain / orchestration
- Inference / local model
- Memory / vector store
- Automation / workflow
- Tools / interfaces
- Dashboard / observability
- Security / policy
- Data / database
- Domain module

## Decision Rules

Include now when the component is local-first, easy to test, documented, and directly useful.

Include later when the component is useful but not needed for the minimum stack.

Reject when the component is redundant, unclear, unsafe, unmaintained, or outside the architecture.
