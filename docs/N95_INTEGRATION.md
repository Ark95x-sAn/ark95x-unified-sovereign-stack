# Network-95 native bridge integration

This increment adds a signed transport-evidence component to the existing stack. It does not replace the Network-95 Core mission engine, approve a production deployment, or merge 25 upstream source trees. The existing Core 1.4.0 C1–C6 build queue remains the integration order.

## What is implemented

- `n95_native`: original Python code with per-node HMAC envelopes, bounded technical metadata, replay conflict rejection, receipt expiration, a SQLite transport spool, hash-chain inspection and a loopback HTTP fixture.
- `n95_native.core_handoff`: exports a digest-bound **draft** observation for the existing Core mission schema. Optional `--core-root` exercises the supplied Core's real validator against a disposable database. It neither submits nor executes the draft, changes a node's verified state, nor modifies Core's mission ledger.
- `core/device_mesh.py`: legacy in-memory behavior now distinguishes preparing a handoff from actually transferring context. Routing requires a fresh locally observed heartbeat; this old API still supplies no authenticated physical identity.
- `tools/N95-Native-Preflight.ps1`: read-only Windows inventory and role checks. See the Windows runbook for its target limits.
- A focused GitHub verification workflow runs the bridge/mesh contracts on hosted Linux and Windows runners. Hosted runner tests are separate from GM700, RTX and Surface acceptance.

## One mission authority

| Component | Owns | Does not establish |
|---|---|---|
| Existing Network-95 Core | Mission schema, mission state and release policy | Production readiness from a fixture |
| New transport spool | Signed telemetry envelopes and transport receipts | A second mission queue, human authority or medical evidence |
| Core handoff adapter | Reviewable observation + source digest + draft mission | Approval, submission, dispatch or device promotion |
| Legacy device mesh | Prepared device/context descriptions | Delivery, authenticated reachability or completed failover |

The bridge can authenticate possession of a node key. All keys on one demonstration host still represent one host. A signed claimed producer hash is a report by that key holder; matching it to a local file is not remote code attestation. A hash chain can expose edits relative to its retained state; a privileged writer can rewrite or truncate an unanchored local log. There is no blanket “audit-proof percentage.”

## Three-device target

| Node | Intended role | Next required proof |
|---|---|---|
| GM700 | Existing Core, PostgreSQL authority, private authenticated gateway, scheduler and backups | C1 transaction/identity contracts, then target restart and restore tests |
| RTX 2080 | Local Ollama inference and bounded worker jobs | Native driver/model fit, scoped key enrollment, timeout handling and verified output |
| Surface Pro X | Browser command/review console | ARM64 client fit and authenticated access to the same Core state |

There is no hardware-memory pooling in this design. Nodes cooperate through typed requests and replies. The native bridge has a loopback-only listener and client; a separately verified private transport is required before sending between real devices. Do not expose the prototype on a public interface. Tailscale installation alone does not supply an authenticated application route or prove a working tunnel.

## First useful end-to-end mission

The selected product workflow is an approved business-document folder to a source-linked operational brief and a review queue. Current transport tests exercise technical metadata only. Folder ingestion, local inference, claim-to-source verification and the review interface remain worker integrations to complete through Core. No human health data is needed for the first workflow.

System health and human health are separate domains. A technical heartbeat is not presence, a vital sign or a health assessment. A future optional personal-data connector needs an identified source, explicit purpose and opt-in, separate storage/retention, unit/time validation and no automatic medical decision. The current bridge rejects extra data fields rather than silently collecting them.

## Adaptation and scaling

Implemented routing chooses among configured eligible telemetry nodes using fresh receipts. It does not invoke a worker. Missing or stale receipts remove eligibility; software does not invent a replacement capability. Future automatic retries must be bounded and idempotent. Software/model/policy improvements enter a versioned candidate, comparison against the same baseline, held-out checks, limited release and a retained rollback path. A model cannot promote its own permission or rewrite the release gate.

The 9×9 matrix in `N95_SERVICE_PRODUCTS.md` maps 81 capability cells, not 81 installed agents. Amara coordinates; Atlas checks outputs; Axiom enforces policy; ArcX executes bounded work. These are software responsibilities until an actual registered implementation and execution receipt exist.

## Selection and commercial boundary

`N95_TOP25_GITHUB.md` contains the 25-source review and exact upstream links. Candidate selection uses local fit, observable execution, license clarity and operating burden. Only the original bridge code is implemented in this increment. Candidate dependencies are not silently installed.

The $100/$500/$1,000 offers in `N95_SERVICE_PRODUCTS.md` are proposed one-time installation scopes. Prices, time caps, support economics and demand need paid-pilot validation. They are not currently advertised as delivered products. Upstream licenses and model terms remain separate from the installation service.

## Backcast from a saleable result

1. Prove Core's authoritative transactions and authenticated identities (C1).
2. Deploy on GM700 with restore/restart receipts (C2).
3. Complete one scoped RTX model call with failure/replay behavior (C3).
4. Admit one supported read-only connector (C4).
5. Deliver the actual folder-to-brief result through Surface, including checked sources and an outage recovery test (C5).
6. Run paid pilots against the defined labor/support caps; add a capability only when measured customer outcomes justify it (C6).

This backcast is a proposed sequence, not a prediction that a product will sell. The business thesis is that customers may pay for private workflows that finish with checkable results and recover when interrupted. Demand is unverified.
