# Network-95 Control Plane v1 — Canonical Build Contract

Status: IMPLEMENTATION BASELINE / LIVE EXECUTION HOLD

## Product
One doorway in. One accountable operating system out.

Operator supplies an objective once. Network-95 preserves the raw signal, compiles it into typed missions, checks authority, routes each task to the best registered capability, collects evidence, independently verifies consequential results, persists state, and returns a compressed executive brief.

This extends the existing Network-95 spine. It does not replace n95_native, existing receipt/authentication work, SCARIO concepts, or existing device roles.

## Canonical loop
SIGNAL -> COMPILE -> AUTHORIZE -> ROUTE -> EXECUTE -> OBSERVE -> VERIFY -> RECORD -> BRIEF

SCARIO maps to the same lifecycle:
Sense -> Classify -> Authorize -> Record -> Intervene -> Observe.

## Roles
- Operator: intent and consequential authorization.
- Amara: orchestration/navigation persona; no independent authority.
- Mission compiler: raw signal -> typed mission DAG.
- Axiom/policy gate: deterministic authority and risk gate; cannot self-approve.
- Capability registry/router: provider-neutral selection by authority, privacy, health, cost, latency, and capability.
- Executors: replaceable adapters such as Codex, OpenAI/ChatGPT, Perplexity/search, Ollama/local models, n8n, and registered machine workers.
- Black: adversarial challenge.
- White: independent acceptance authority.
- Green: append-only evidence/receipt and learned-state candidate after verification.
- Executive brief: only decisions, material risks, blockers, proof, and next action.

## Device baseline
Existing logical roles remain:
- D4-GM700: continuity/control.
- D4-RTX2080: compute.
- D4-SURFACE: human edge.

No device is considered live, authenticated, or execution-capable without native evidence.

## Hard invariants
1. Raw operator signal is immutable and preserved.
2. Availability, authentication, authority, execution, and verification are separate states.
3. No executor may expand its own authority.
4. A planner/verifier cannot approve its own consequential action.
5. Every external mutation requires an explicit authority receipt and idempotency key.
6. "Done" requires evidence satisfying the mission acceptance contract.
7. Provider failure triggers bounded rerouting, never silent scope expansion.
8. Duplicate mission/event IDs cannot produce duplicate side effects.
9. Restart/recovery resumes from durable state without replaying completed side effects.
10. Unknown identity, authority, or evidence => HOLD.
11. Local/private routes are preferred when capability is sufficient.
12. Model/provider names are configuration, not architecture.
13. Human attention is reserved for money, legal exposure, security, architecture, irreversible action, or irreducible intent/authorization.

## Mission contract
Required fields:
- mission_id
- raw_signal
- objective
- acceptance[]
- constraints[]
- risk_class
- authority_required[]
- dependencies[]
- work_units[]
- evidence_required[]
- created_at
- state

Each work unit declares:
- capability_required
- data_class
- mutation_class
- budget
- timeout
- retry_policy
- idempotency_key
- candidate_executors[]
- verifier_requirement

## Routing
Filter in this order:
discover -> reach -> authenticate -> identify -> capability -> authority -> privacy -> health -> cost/latency.

Only eligible executors enter scoring. Selection favors the lowest total cost that can satisfy acceptance, privacy, authority, and verification requirements. Routing decisions are receipted.

## Result contract
Every work unit returns:
- state: proposed | running | blocked | failed | observed | verified
- claim
- evidence[]
- artifacts[]
- executor_identity
- execution_receipt
- confidence
- verifier_verdict
- next

A claim without evidence is not a trusted result.

## Executive brief contract
Default output is compressed to:
- MISSION
- STATE
- DECISION / WHAT MATTERS
- MATERIAL RISK OR BLOCKER
- PROOF
- NEXT

## First product acceptance test: HQ Daily Operating Brief
Input:
"Network-95, prepare today's operating brief."

The system must:
1. Preserve the exact input.
2. Resolve authorized sources and current mission state.
3. Compile parallel work for cash/revenue, deadlines/risk, operations/build, and unresolved blockers.
4. Route each work unit without operator selecting agents.
5. Stop any unapproved external mutation.
6. Reconcile contradictory findings.
7. Independently verify material claims.
8. Persist mission, routing, evidence, receipts, and verifier verdicts.
9. Return one brief containing only outcome-changing information.
10. Recover after restart without duplicate execution.

Pass requires all ten assertions plus native evidence for any claimed live executor. Fixture success may be labeled FIXTURE_VERIFIED only.

## Promotion gates
G0 schema/fixture
G1 durable persistence/reopen
G2 authenticated executor binding
G3 real bounded execution + hash-verifiable receipt
G4 independent White observation
G5 controlled failure/recovery/idempotency
G6 HQ Daily Operating Brief end-to-end
G7 measured pilot with cost, latency, error, intervention, and completion metrics

Current baseline remains LIVE HOLD until G2-G4 are established with native evidence.

## Non-goals for v1
- agent-count theater
- consciousness claims
- unrestricted autonomy
- autonomous money movement
- autonomous legal filing
- silent external communications
- replacing proven components because a binding is missing

## North-star metric
Verified outcomes completed per unit of operator attention, subject to zero unauthorized consequential actions.
