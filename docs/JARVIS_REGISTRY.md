# Jarvis Registry

## 2026-09-06 — N95 native integration increment

- **Crew:** source reviewers (AI/data and operations), native bridge builder, legacy mesh fixer, independent security reviewer, Windows preflight builder; one root synthesis owner.
- **Repository/tool:** this existing stack; recovered Network-95 Core 1.4.0 used only for its real mission-schema validator. Candidate catalogue reviews 25 upstream projects; no upstream source trees or private user records copied into the bridge.
- **Layers:** tools/interfaces, security/policy, dashboard/observability, data, device coordination and service design.
- **Action:** implemented per-node signed telemetry, durable transport receipts, freshness-aware eligibility, bounded polling and digest-bound Core draft export. Fixed legacy false online/delivery/failover behavior. Prepared native Windows audit, 25-project review, 9×9 capability map and three installation offers.
- **Files:** `n95_native/`, `core/device_mesh.py`, three focused test modules, `tools/N95-Native-Preflight.ps1`, `.github/workflows/native-bridge.yml`, `.gitignore`, README and `docs/N95_*`.
- **Risk:** Yellow for original code, local fixture server and prepared files. No production deployment, model invocation, raw personal-data ingestion, message sending or upstream dependency installation. Windows script performs read-only checks when run locally.
- **Review:** fixed independent findings for HTTP redirect credential forwarding and mixed database snapshots; exported status now retains evaluation/expiry metadata and historical-only semantics. HMAC, audit-chain and physical-proof limitations remain explicit.
- **Validation:** 34 focused cases and 6 subtests passed on Linux. Actual loopback HTTP recorded three synthetic identities; two bounded polling cycles produced two further receipts; fresh Store reopened and checked all five. Exported draft was accepted by recovered Core's actual schema validator in a disposable database, with no submission or execution. See `N95_VERIFICATION.json`.
- **Test command:** `python -m pytest -q tests/test_native_bridge.py tests/test_core_handoff.py tests/test_device_mesh.py`.
- **Windows CI correction:** the first hosted Windows run exposed three raw SQLite test-fixture handles left open. Those connections now close explicitly; production Store closure already worked. A new regression checks closure after successful commit and exceptional rollback. Hosted rerun pending.
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

## 2026-09-13 — GitHub harvest preparation

- **Crew / role:** Black; source discovery, verification, reading and static architecture review. Independent White did not run.
- **Repository/tool:** existing unified stack; GitHub read/write connector; pinned source inspection for PostgreSQL, Ollama, Repomix, Docling and MCP Python SDK.
- **Jarvis layers:** all nine existing categories mapped; five priority reserves; eight rejections with reopening conditions.
- **Action taken:** appended extraction patterns, source ledger, architecture crosswalk, bounded acceptance criteria, admission rules and record schema under the existing `docs/N95_TOP25_GITHUB.md`; added harvesting mode to the existing extraction protocol.
- **Files changed:** `docs/N95_TOP25_GITHUB.md`, `docs/REPO_EXTRACTION_PROTOCOL.md`, `docs/JARVIS_REGISTRY.md`.
- **Risk label:** Yellow documentation write authorized by operator's request to append/fold into the existing page. No upstream code imported; no physical-device action or installation performed.
- **Review result:** STATIC_COMPARISON_COMPLETE_WITH_GAPS. Core source/schema locator, target telemetry, authenticated RTX execution and fresh independent verification remain unresolved. Compression omits behavior; MCP v1/v2 examples differ; Docling extras/model terms need review. Historical ledger assertions and masked generic CI failures are not accepted as runtime evidence.
- **Test command:** none; documentation-only pass. Validate preserved original text, nine unique category IDs, five reserve IDs, eight rejection IDs, immutable source links and exact writeback contents. All proposed capability tests remain NOT_RUN.
- **Next move:** Monday harvesting preparation through this page; prioritize R01 Core transaction identity, then existing evidence handoff and RTX acceptance in C1–C6 order. A scheduler declaration alone is not evidence of an enabled task.

- **Scheduling receipt, 2026-09-13:** N95 GitHub Harvest created and enabled for Monday mornings around 08:00 America/Chicago, starting 2026-09-14. GitHub read access was checked successfully before creation. No scheduled execution has run yet.

## 2026-09-14 — GitHub harvest delta

- **Crew / role:** Black; discover, verify, read, reserve/reject; no independent White run.
- **Repository / tool:** GitHub source and documentation review; existing unified stack baseline `f9dae118f19babb54717ab8fb20e1cc36a4b7277`.
- **Layers / changes:** C08 Data with C07/C05/C09 cross-links; R06 backup-chain rejection/restore acceptance added, R05 DOCX content-control handling and missing page provenance refined, X09–X10 unsupported inferences rejected. Five existing upstream heads checked; no new catalogue.
- **Files changed:** `docs/N95_TOP25_GITHUB.md`, `docs/JARVIS_REGISTRY.md`; prior entries preserved.
- **Risk / scope:** Yellow documentation write only. Source examples and fixtures read, not run; no package install, model pull, device action, deployment, workflow dispatch or private-data publication.
- **Review result:** pinned PostgreSQL code/fixture and released Docling v2.127.0 code/fixture/manifests/license inspected; current Core source/binding and target telemetry remain UNKNOWN. All candidate tests NOT_RUN, White receipt absent.
- **Validation:** exact prior-content preservation, immutable source locators and read-back comparison of both documentation files. No runtime test command.
- **Write execution control:** documentation commit includes `[skip ci]` to avoid the repository's push-triggered installs/container runs under this research-only mandate. No workflow or protection configuration changed; skipped checks are not passes. [GitHub behavior reference](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs).
- **Next move:** identify the existing Core storage implementation and selected supported PostgreSQL backup strategy; retain C1→C2→C3→C4→C5→C6 order. R05's next later fixture checks wrapped DOCX cells and preserves unknown page provenance.

## 2026-09-21 — GitHub harvest delta

- **Crew / role:** Black; discover, verify, read, reserve/reject. Independent White did not run.
- **Repository / baseline:** existing unified stack `01cb2442757370a32b1a560bf298d6f466b9522b`; five governed files read first, then README, deployment blueprint and `n95_native/core_handoff.py`.
- **Named unmet need:** fail-closed source harvesting and C1 mission/evidence constraints under untrusted repository metadata, least-privilege role boundaries and exact-version assumptions.
- **Layers / decisions:** C08/C07 R01 refined for PostgreSQL RI permission/cache failure coverage; C05/C07 R04 refined for Repomix v1.18.1 Git-config non-execution and shell/YAML preservation. X11–X14 reject read-only-means-non-executing, post-tag Docling/MCP fix attribution, and Ollama-hardening-means-working inferences.
- **Files changed:** `docs/N95_TOP25_GITHUB.md`, `docs/JARVIS_REGISTRY.md`; sole catalogue and earlier provenance preserved.
- **Risk / scope:** Yellow documentation write only. No install, runtime execution, model pull, deployment, workflow dispatch, device action, cleanup, account/permission change, message or private-data publication.
- **Review result:** STATIC_COMPARISON_COMPLETE_WITH_GAPS. Exact pins, code, tests, manifests, licenses and releases read. Existing Core storage source/version, extractor and Ollama adapter bindings, target free space, device/model fit and White evidence remain UNKNOWN.
- **Validation:** guarded file-SHA write, unique delta heading, marker preservation and post-write read-back. All capability tests NOT_RUN.
- **Write execution control:** documentation commits use `[skip ci]`; no workflow or repository settings changed. A skipped workflow is not a pass.
- **Next move:** select the supported PostgreSQL release and role matrix for the R01 disposable test; keep R04 uninstalled until its malicious-config and semantic-preservation fixture can run after C1–C3. Do not admit any physical target without a fresh >=200 GB reading.

## 2026-09-28 — GitHub harvest delta

- **Crew / role:** Black; discover, verify, read, reserve/reject. Independent White did not run.
- **Repository / baseline:** existing unified stack 55670eb0c78345cd9b84835430673f92907649b8; five governed files read first, then README, deployment blueprint and n95_native/core_handoff.py.
- **Named unmet need:** fail-closed C4/C5 business-folder-to-source-linked-brief intake with format-scoped DOCX parsing and preserved list/table ordering.
- **Layers / decision:** C08/C05/C09 R05 refined against docling-project/docling v2.130.0 at 92fc74c36bbd20db9838d7665d38900e5c958319. The release contains the deferred optional docling_parse import guard and DOCX list-after-table fix, satisfying X12's source-level reopening condition without erasing its v2.129.0 rejection. PostgreSQL, Repomix, Ollama and MCP observations produced no new reserve.
- **Existing mapping:** no document worker exists; n95_native/core_handoff.py::prepare remains only a digest-bound draft envelope. GM700 retains the sole Core/PostgreSQL mission authority, RTX remains bounded and unnecessary for this DOCX-only path, and Surface remains the C6 review node.
- **Risk / scope:** Yellow documentation write only. No install, runtime execution, model pull, deployment, workflow dispatch, device action, cleanup, account/permission change, message or private-data publication. Free space remained UNKNOWN, so no physical target was admitted.
- **Dependency boundary:** docling-slim 2.130.0 requires Python >=3.10,<4; DOCX uses python-docx >=1.2,<2. PDF parser, standard, OCR, VLM and model extras remain separate and unadmitted; transitive/model license review remains open.
- **Review result:** STATIC_COMPARISON_COMPLETE_WITH_GAPS. Upstream code, tests, golden fixture, manifest, changelog and license were read at exact revisions. The R05 positive/negative fixture, Core binding, dependency closure and White evidence remain NOT_RUN/UNKNOWN.
- **Validation:** guarded file-SHA writes, unique delta headings, catalogue marker and prior provenance preservation, then read-back of both files. A skipped workflow is not a pass.
- **Write execution control:** documentation commits use [skip ci]; no workflow or repository settings changed.
- **Next move:** after C1–C3 and target/dependency authorization, run the bounded DOCX list–table–resumed-list plus missing-PDF-extra test; require digest/locator preservation and keep page provenance UNKNOWN when absent.

## 2026-10-05 — GitHub harvest delta

- **Crew / role:** Black; discover, verify, read, reserve/reject. Independent White did not run.
- **Repository / baseline:** existing unified stack 092918af13c9e0270b63e7482dd6490f30dce9cf; five governed files read first, then README, deployment blueprint and n95_native/core_handoff.py.
- **Named unmet need:** C4/C5 source-linked folder intake must preserve evidence identity and fail explicitly on ambient file access, oversized transport events and cancellation.
- **Layers / decisions:** C08/C07/C05/C09 R05 refined against docling-project/docling v2.133.0 at b0315ea356298e4659c9727e9f5191dd2001860a for default-deny local image references in re-ingested Docling JSON. C05/C04/C07 S5 refined against modelcontextprotocol/python-sdk v2.3.0 at 2118f14f8a19bc158d8a1cf90af58d85d187f849 for cancellable Windows command resolution and bounded SSE events. X13 remains historically correct for v2.2.0; its release condition is met only at source-reserve level. PostgreSQL, Repomix and Ollama produced no new reserve.
- **Existing mapping:** no document worker or MCP adapter exists. n95_native/core_handoff.py::prepare remains only a digest-bound draft envelope. GM700 retains the sole Core/PostgreSQL mission authority; RTX stays bounded; Surface remains C5 review; C1–C6 order is unchanged.
- **Risk / scope:** Yellow documentation write only. No install, runtime execution, model pull, deployment, workflow dispatch, device action, cleanup, account/permission change, message or private-data publication. Free space remained UNKNOWN, so no physical target was admitted.
- **Dependency boundary:** Docling slim JSON behavior is separate from DOCX/PDF/OCR/VLM/model extras; MCP examples are v2.3.0 only. Python/dependency ranges and MIT licenses were recorded; transitive and model terms remain open.
- **Review result:** STATIC_COMPARISON_COMPLETE_WITH_GAPS. Exact release commits, code, tests, manifests, changelogs/docs and licenses were read. R05-A and S5-A, Core bindings, worker/adapter implementations, dependency closure and White evidence remain NOT_RUN/UNKNOWN.
- **Validation:** guarded file-SHA writes, unique delta headings, catalogue marker and prior provenance preservation, exact source pins, then read-back of both files. A skipped workflow is not a pass.
- **Write execution control:** documentation commits use [skip ci]; no workflow or repository settings changed.
- **Next move:** after C1–C3, run R05-A in a disposable network-denied fixture and S5-A on a v2.3-only loopback transport. Require explicit failure receipts, later-request usability, no ambient file reads or orphan process/stream, and no submitted Core mission.

## 2026-10-07 — PostgreSQL startup review branch

- **Crew:** Codex root; no independent reviewer in this increment.
- **Repository/layer:** existing unified stack, Data/database and configuration.
- **Action:** corrected Core Compose ports/env_file structure; removed PostgreSQL password fallback at all three references; limited PostgreSQL host binding to loopback. Prepared isolated acceptance plan.
- **Files changed:** docker-compose.yml, docs/N95_POSTGRES_ACCEPTANCE.md, docs/JARVIS_REGISTRY.md.
- **Risk:** Yellow review-branch preparation. Applying configuration changes affects networking/credentials; no live host configuration or database was changed here.
- **Review result:** original YAML parses but Core ports was null and env_file contained port text. Corrected fields, three required-password references and loopback binding passed local Python/PyYAML assertions. Not an independent review or Docker validation.
- **Test command:** local Python/PyYAML structure assertions; docker compose config --quiet remains NOT_RUN because Docker is unavailable here. PostgreSQL runtime likewise unavailable.
- **Execution control:** review branch only; commits use [skip ci], no workflow settings changed. Skipped checks are not passes.
- **Next move:** quiet Compose validation, existing Core transaction/identity mapping and isolated PostgreSQL write/read, rollback/replay/role-denial, restart and separate-database restore evidence. Runtime and physical gates unchanged.
