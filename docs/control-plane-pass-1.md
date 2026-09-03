# Node 5 — Pass 1: Single Control Plane

## Decision

All existing ARK95X agents converge under one control plane. No new competing
brain or state store is introduced.

**`ARK-STATE.json` remains the only authoritative state of truth.**

The control plane is an authority and reporting contract around that file. ARC X
is the coordinator interface; it is not a second state owner. The Command Ledger
records outcomes. Specialist agents report observations, recommendations,
requests, evidence, and results through the shared plane.

## Converged roles

| Agent | Existing responsibility | Authority handed to control plane | Contract state | Live adapter state |
|---|---|---|---|---|
| ARC X | Intent decode, simulation, ranking, routing | Final dispatch and cross-agent priority | Registered | Pending runtime adapter |
| Codex Security | Threat modeling, review, veto, containment | Consequential security action release | Registered | Pending runtime adapter |
| Memory Cortex | Retrieval, pattern activation, memory patch proposals | Permanent memory acceptance and retirement | Registered | Pending runtime adapter |
| Monitoring | Health, anomaly, evidence, alerting | Incident priority and escalation route | Registered | Pending runtime adapter |
| GitHub | Source control, patches, PRs, proof | Repository writes, deployment, public changes | Registered | Connector available; continuous heartbeat not yet proven |
| n8n | Workflow transport, schedules, normalization | External dispatch and account-changing workflow activation | Registered | Workflow exists; live instance test pending |
| Devices | Inventory, heartbeat, scoped local execution | System mutation and destructive execution | Registered | Device coordinator work exists separately; adapter not yet converged |
| Business Ops | Wealth, real-estate, legal, and operating recommendations | Financial, legal, public, and account-changing action release | Registered | Data adapters pending |

“Registered” means the role and authority contract exist in code. It does **not**
mean a live heartbeat was observed. Runtime status becomes `reporting` only after
an adapter sends an accepted report.

## Reporting envelope

Every adapter reports the same minimum fields through the control plane:

```json
{
  "agent_id": "monitoring",
  "status": "healthy",
  "payload": {
    "evidence_ref": "health-check-1",
    "confidence": 1.0,
    "observed_at": "ISO-8601 timestamp"
  }
}
```

Recommended payload fields when applicable:

- evidence references and source identity;
- observed, calculated, inferred, simulated, or unknown classification;
- confidence and freshness;
- requested action and action class;
- dependency, cost, risk, and expected result;
- actual result and rollback state.

## Authority invariants

1. No specialist may override the control plane.
2. No specialist may self-approve a consequential action.
3. No component may interpret, authorize, execute, and permanently rewrite
   memory for the same consequential action.
4. Financial, legal, public, destructive, deployment, security-sensitive,
   system-mutation, and account-changing actions require human approval.
5. Monitoring may observe and alert, but may not silently erase or downgrade its
   own evidence.
6. Memory Cortex proposes changes; the control plane accepts or rejects them.
7. n8n moves approved data and work. It is transport, not the brain.
8. GitHub holds source and proof. It does not define live operational truth by
   itself.

## Current state

Pass 1 locks the control-plane contract and tests its boundaries.

What is proven in the repository:

- eight existing roles register under one plane;
- the plane points to `ARK-STATE.json` as the authoritative state path;
- agents cannot override the plane or self-approve;
- normal work is queued through the plane;
- consequential work is queued for human approval;
- out-of-scope requests are rejected.

What is not yet proven:

- continuous live heartbeats from every adapter;
- a live n8n execution against the current workflow definition;
- device-fleet connectivity and authenticated task execution;
- business-system data freshness and reconciliation.

## Next adjustment pass

Wire existing adapters into `ControlPlane.report()` and
`ControlPlane.request_action()`. Do not add another coordinator, registry, or
state file. Every adapter must write back status and evidence to the same plane,
and every completed action must return its result to the Command Ledger and
`ARK-STATE.json` workflow.
