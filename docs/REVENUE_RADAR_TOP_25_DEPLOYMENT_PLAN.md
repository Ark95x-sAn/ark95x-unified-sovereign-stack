# Revenue Radar — Top 25 Deployment Extraction

**Target:** ARK95X Unified Sovereign Stack  
**Operating rule:** one source of truth, one approval gate, no fabricated data,
no autonomous external commitments.

## Decision

Revenue Radar becomes the revenue intake and controlled follow-up module inside
the unified stack. Existing repositories contribute capabilities; they do not
run as 25 separate command centers.

## Ranked deployment map

| # | Deployment item | Best source asset | Operational value | Release gate |
|---:|---|---|---|---|
| 1 | Local Revenue Radar MVP | `revenue-radar/` in this repository | Working capture-to-outcome loop | Nine functional tests pass |
| 2 | Human approval gate | Revenue Radar + unified core | Prevents unauthorized sends | Approval hash matches recipient and draft |
| 3 | Append-only decision ledger | Revenue Radar SQLite, later PostgreSQL | Full traceability | Every state transition is logged |
| 4 | n8n workflow router | `n8n-sovereign` | Intake, scheduling and outbound handoff | Private endpoint; idempotency enforced |
| 5 | Opportunity normalization | Revenue Radar cleaning layer | Creates consistent records | Invalid contact data fails closed |
| 6 | Exact deduplication | Revenue Radar fingerprinting | Stops duplicate effort and messaging | Similar leads flagged, never silently merged |
| 7 | Transparent scoring policy | Revenue Radar score engine | Ranks cash-generating work | Versioned rules and visible reasons |
| 8 | Local AI drafting | Ollama through ARCX | Fast private first drafts | Template fallback always works |
| 9 | Outcome feedback loop | Revenue Radar outcome log | Calibrates scoring from results | Won/lost evidence required |
| 10 | Intelligence intake | `intelligence-gathering-system` | Finds grants, leads and market signals | Source URL and timestamp required |
| 11 | Sentinel verification | `Sentinel` | Checks claims before routing | Evidence and confidence attached |
| 12 | Browser execution worker | `browser-use` | Collects permitted web evidence | No submission or purchase without approval |
| 13 | Local research worker | `agenticSeek` | Reduces paid API usage | Sandboxed research-only role |
| 14 | Self-hosted AI foundation | `self-hosted-ai-starter-kit` | Ollama, n8n and supporting services | Health checks green |
| 15 | Amara multi-AI bridge | `amara-protocol-sovereign-os` | Routes specialized AI providers | Provider failures fall back safely |
| 16 | Omnikernel job router | `ark95x-omnikernel-orchestrator` | Prioritizes and schedules jobs | No circular or duplicate jobs |
| 17 | Central command cockpit | `central-command-ops` | Single operator view | One decision packet at a time |
| 18 | Flame agent registry | `flame-hq1` | Defines bounded agent roles | Named owner, tools and stop conditions |
| 19 | Comet infrastructure layer | `comet-layer1-infrastructure` | Browser and service infrastructure | Secrets isolated; recovery tested |
| 20 | Unified core API | `ark95x-unified-sovereign-stack` | Stable integration boundary | Auth, health and audit endpoints |
| 21 | Redis mission queue | Unified stack infrastructure | Reliable job state and backpressure | Retry ceiling and dead-letter queue |
| 22 | PostgreSQL source of truth | Unified stack infrastructure | Multi-device durable records | Migration and restore test pass |
| 23 | Private network access | Tailscale pattern | Secure PC-to-PC operation | No raw service port exposed publicly |
| 24 | Monitoring and alerts | Prometheus + Grafana in unified stack | Measures failures, queues and ROI | Actionable thresholds only |
| 25 | Backup and recovery | Infrastructure layer | Protects ledger and configuration | Encrypted restore drill succeeds |

## Phased release

### Phase 0 — Safety and truth

- Clear the affected monitor, cable, power strip and outlet before any 24/7 run.
- Confirm ARCX and AMARA hardware identity and service ownership.
- Keep legal evidence in its private repository; ingest only explicit,
  non-privileged references into Revenue Radar.

### Phase 1 — Prove the loop

Deploy items 1–9 locally in dry-run mode. Use 25 historical opportunities as a
gold set. Promotion requires:

- 95% required-field completeness
- 90% correct routing
- zero unauthorized external actions
- less than 20% substantial draft rewrites
- complete source-to-outcome traceability

### Phase 2 — Connect intelligence

Deploy items 10–18 behind the same queue and approval gate. Agents may research,
classify and draft. They may not submit, purchase, promise, delete, disclose
sensitive information or contact external parties without operator approval.

### Phase 3 — Harden operations

Deploy items 19–25. Move the source of truth to PostgreSQL only after a tested
backup and migration. Keep Redis for queue state, not permanent records.

## KPI contract

### Business

- qualified opportunities per week
- median first-response time
- approved follow-ups
- meetings booked
- pipeline value
- collected revenue
- operator hours saved

### System

- successful workflow rate
- duplicate rate
- human rewrite and rejection rate
- cost per completed outcome
- queue wait time
- unauthorized action count
- backup restore success

## Stop conditions

Stop deployment when any of the following occurs:

- equipment or electrical safety is unresolved
- the data source cannot be identified
- the system proposes invented facts
- an approval hash does not match the outbound payload
- duplicate delivery cannot be ruled out
- credentials or private legal material would be exposed
- a workflow cannot show measurable value or risk reduction

## Immediate operating order

1. Run Revenue Radar locally in dry-run mode.
2. Load five real, non-sensitive opportunities.
3. Review scores and drafts.
4. Approve and simulate each send.
5. Log outcomes.
6. Adjust the scoring policy only from observed results.
7. Connect n8n after the local loop passes.

**Do not deploy all 25 simultaneously. The ranked list is the sequence of
capabilities; the approval gate and ledger remain the control plane throughout.**
