# Repository Review Protocol

## Purpose
Every candidate software project must be reviewed before it is added to Jarvis.

## Required Fields

- Name
- URL
- Source observed
- Plain-English purpose
- Jarvis layer
- Install method
- Container support
- Local capability
- Hosted service requirement
- Network ports
- Configuration values
- Data stored
- Files changed
- Maintenance signal
- License
- Risk label
- First safe test
- Decision: include now, include later, or reject
- Notes

## Jarvis Layers

- Brain: agent orchestration, planning, routing
- Inference: local model serving
- Memory: vector store, recall, context, RAG
- Automation: workflows and triggers
- Tools: approved integrations and local actions
- Dashboard: command center and reports
- Security: configuration review and policy
- Data: databases, queues, streams, storage
- Domain: real estate, finance, or research modules

## Decision Rules

Use now only if the candidate supports the current build phase, can be tested safely, maps to a Jarvis layer, has clear setup instructions, does not require exposed secrets, and supports a local or container-based setup path.

Use later if it is useful but not needed yet.

Reject if it is redundant, unclear, not maintained, unsafe for the current environment, or unrelated to the Jarvis architecture.

## Final Review Format

Decision:
Reason:
Next move:
Registry update required: yes or no

## Harvesting mode — current gate, 2026-09-13

This mode governs preparation. Earlier “include now” wording is an adoption suggestion only. It does not grant install, execution or runtime-verified status.

| Step | Black review action | Record / stop condition |
|---|---|---|
| discover | Find a source against a named capability gap; check existing registry first | Candidate + category + owner/repo; missing identity stays unresolved |
| verify | Check origin, immutable revision, maintenance signal, license and declared environment | Source confidence + limitations; no runtime status inferred |
| read | Read primary documentation, relevant code, manifests and failure paths; compare with existing architecture | Source locator + extracted input/transform/output + dependencies + contradiction |
| reserve | Retain a useful pattern with module placement and one bounded acceptance test | Explicit unknowns; no installation, execution, permission or learning promotion |
| reject | Reject mismatch, duplication, unsupported inference or unacceptable scope | Reason + evidence + condition to reopen; retain provenance |

Workflow: `discover → verify → read → reserve OR reject`. Reject may occur at an earlier failing gate. The reviewer remains Black in every stage; independent White verification is a separate action and receipt.

Canonical category map, current source pins, five reserves, rejection ledger, admission gates and record schema: [existing 25-source page](N95_TOP25_GITHUB.md#harvest-preparation--2026-09-13). Keep future harvest entries under that same page, deduplicated by upstream/revision/pattern; do not create another master catalogue.

Architecture: preserve existing Core/PostgreSQL authority, GM700 control, RTX worker and Surface review. Work backward from acceptance through capability, dependency and missing implementation. Read `N95_INTEGRATION.md` before interpreting older broad deployment prose.

Physical-target admission: below 200 GB free or unverified free space means STOP / RETURN, without cleanup, cleanup planning, install or optimization on that target. Record the target volume, raw bytes and unit; never infer device health from cloud research.

No source README, badge, installed package, listed model, signed receipt or successful API call alone establishes a working end-to-end capability. Retain source claims separately from locally observed test results and independent verification. No model or policy may promote itself.
