# Revenue Radar — Levels, Layers, Protocols and Phase Gates

## Command principle

Revenue Radar is a controlled revenue operating system. Intelligence may
collect, normalize, rank, recommend and draft. Only the operator may authorize
external commitments.

The stack advances by evidence, not by the number of tools installed.

## Seven maturity levels

| Level | Name | Capability | Promotion proof |
|---:|---|---|---|
| 0 | Safe baseline | Electrical, device, account and data boundaries are known | Safety checklist complete; no exposed secrets or unsafe hardware |
| 1 | Local proof | One PC runs capture-to-outcome in dry-run mode | 25-case gold set meets calibration thresholds |
| 2 | Controlled automation | n8n performs intake and approved handoffs | Idempotent handoff; zero unauthorized actions |
| 3 | Multi-device command | AMARA, ARCX and operator devices share durable state | One source of truth; conflict and recovery tests pass |
| 4 | Bounded agent mesh | Research, verification and drafting agents use one queue | Every agent has an owner, tool scope and stop condition |
| 5 | Revenue operations | Multiple opportunity channels run through the same ledger | Positive collected revenue and measured operator hours saved |
| 6 | Resilient operations | Monitoring, backups, incident handling and failover are proven | Restore drill and degraded-mode test pass |
| 7 | Replicable platform | The system can be deployed for another business without hidden knowledge | Documented install, tenant isolation and repeatable acceptance test |

## Eight architecture layers

### Layer 1 — Safety and identity

- named operator and service identities
- least-privilege credentials
- MFA for external services
- no use of equipment involved in unresolved melting, smoke or fire
- secrets never stored in prompts, source files or audit messages

### Layer 2 — Data and evidence

- PostgreSQL becomes the durable source of truth after Level 2
- SQLite remains valid for the Level 1 local proof
- every material fact carries source, timestamp, owner and confidence
- raw evidence stays separate from interpretations and generated drafts
- private legal evidence remains isolated from general opportunity records

### Layer 3 — Decision and policy

- deterministic eligibility, deduplication and scoring run before AI
- score policy and templates are versioned
- AI output is a recommendation, never authorization
- contradictory or missing evidence routes to review
- stop conditions override opportunity score

### Layer 4 — Workflow and queue

- every job has a unique trace ID and idempotency key
- Redis stores queue state, not permanent business records
- retries have ceilings and exponential backoff
- poison jobs route to a dead-letter queue
- external side effects use an outbox or equivalent reconciliation record

### Layer 5 — Intelligence and agents

- research agent gathers permitted evidence
- verifier checks source quality and contradictions
- scorer applies the published deterministic policy
- drafting agent generates bounded communication
- no agent may approve its own output

### Layer 6 — Operator experience

- one decision packet at a time
- show known facts, uncertainty, recommendation and proposed action
- approve, reject, edit or hold are explicit controls
- high-risk actions require re-authentication
- silence and hold are valid outcomes

### Layer 7 — Observability and recovery

- health, queue, latency, failure and cost metrics
- append-only transition ledger
- encrypted backups with tested restores
- incident severity and response ownership
- handoff acceptance is not represented as confirmed delivery

### Layer 8 — Business outcomes

- qualified opportunities
- response time
- meetings booked
- conversion rate
- collected revenue
- operator hours saved
- cost per completed outcome

## Ten mandatory protocols

### RR-P01 — Intake protocol

Accept only declared channels. Assign a source ID, trace ID, timestamp and data
owner. Reject oversized or malformed payloads.

### RR-P02 — Evidence protocol

Separate observed facts, user-provided claims, external sources, inference and
generated content. Never promote inference to fact.

### RR-P03 — Identity and deduplication protocol

Match exact source keys first, then canonical contact and opportunity
fingerprints. Flag ambiguous similarity for review; never silently merge fuzzy
matches.

### RR-P04 — Scoring protocol

Use deterministic, versioned components. Return total score plus component
reasons. A model may explain a score but cannot change it.

### RR-P05 — Drafting protocol

Use verified context only. Forbid invented facts, promises and unresolved
placeholders. If local AI fails, fall back to the approved template.

### RR-P06 — Approval protocol

Bind approval to opportunity ID, destination, channel, subject, body, actor and
time. Any relevant edit invalidates approval. Agents cannot approve.

### RR-P07 — Handoff protocol

Require approval-hash equality and an idempotency key. Move through
`APPROVED → SENDING → HANDED_OFF | FAILED`. A webhook acceptance is not proof
of provider delivery.

### RR-P08 — Outcome protocol

Record reply, meeting, won, lost, no response or other against the original
opportunity and handoff ID. Preserve history instead of overwriting it.

### RR-P09 — Incident protocol

Freeze side effects for:

- unsafe hardware or electrical symptoms
- unauthorized action attempts
- approval mismatch
- suspected duplicate delivery
- credential exposure
- data corruption or restore failure
- sensitive data crossing its permitted boundary

### RR-P10 — Learning protocol

Use verified outcomes to propose scoring or template changes. Test changes
against the gold set. Promote only versioned policies that improve results
without weakening safety gates.

## State machine

```text
CAPTURED
  -> NORMALIZED
  -> DUPLICATE_REVIEW | SCORED
  -> DRAFTED
  -> PENDING_APPROVAL
  -> APPROVED | REJECTED | HELD
  -> SENDING
  -> HANDED_OFF | FAILED | RECONCILE
  -> OUTCOME_RECORDED
  -> CALIBRATION_REVIEW
```

Illegal skips fail closed. `SIMULATED` is a dry-run terminal state for the send
attempt and never equals `HANDED_OFF` or provider delivery.

## Phase sequence

### Phase A — Baseline

1. Resolve equipment safety.
2. Inventory devices, services, accounts and exposed ports.
3. Choose one source of truth.
4. Create encrypted backup and recovery ownership.

### Phase B — Local calibration

1. Run Revenue Radar on localhost in dry-run mode.
2. Load 25 historical, non-sensitive cases.
3. Compare expected and generated routing, scores and drafts.
4. Repair the policy before connecting any outbound provider.

**Exit:** 95% completeness, 90% routing accuracy, zero unauthorized actions,
less than 20% substantial rewrites.

### Phase C — Controlled n8n integration

1. Add authenticated intake webhook.
2. Add transactional outbox or reconciliation record.
3. Add idempotent outbound handoff.
4. Add provider delivery callback.
5. Test provider failure, timeout and duplicate-click cases.

**Exit:** complete traceability from intake to confirmed outcome.

### Phase D — Intelligence expansion

1. Connect intelligence gathering.
2. Add Sentinel verification.
3. Add bounded browser research.
4. Add local and cloud drafting routes.
5. Preserve the same approval gate.

**Exit:** agents improve throughput without increasing unauthorized actions or
substantial rewrites.

### Phase E — Multi-device operations

1. AMARA hosts the control plane after safety clearance.
2. ARCX performs heavy local inference.
3. Operator devices display the approval cockpit.
4. Tailscale provides private access.
5. PostgreSQL stores durable shared state.

**Exit:** restart, conflict and failover tests pass.

### Phase F — Revenue scale

Add one channel at a time:

1. grant service opportunities
2. real-estate leads and portfolio operations
3. investor and capital follow-up
4. AI automation service prospects
5. additional channels only after measured positive ROI

**Exit:** collected revenue exceeds operating cost and the system saves
measurable operator time.

### Phase G — Resilience and replication

1. monitoring and actionable alerts
2. encrypted backup and restore drills
3. incident response playbooks
4. tenant and business-data isolation
5. repeatable install and acceptance suite

**Exit:** a second controlled deployment can be completed without undocumented
operator knowledge.

## Promotion authority

| Change | Required authority |
|---|---|
| Data cleaning or internal classification | Policy-approved automation |
| Score-policy proposal | System may propose; operator reviews |
| Draft creation | Approved drafting route |
| External communication | Operator approval |
| Spending, contract, filing or credential change | Operator approval plus re-authentication |
| Sensitive disclosure or deletion | Operator approval plus explicit target confirmation |
| Phase promotion | Evidence gate satisfied and operator approval |

## Highest-ROI next move

Complete Level 1 before expanding the stack: run the 25-case calibration in
dry-run mode, lock the score-policy version, and record the baseline metrics.
Only then connect n8n.

