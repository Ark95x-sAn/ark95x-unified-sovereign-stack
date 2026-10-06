# Network-95 source audit — 2026-10-06

Baseline: [`c153e0a66329673bb44c5203c0b54911c9905fe3`](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/commit/c153e0a66329673bb44c5203c0b54911c9905fe3). Scope: source and bounded local fixture verification. Windows deployment, account settings, secrets, branch protection, production networking and all-repository vulnerability scanning were not verified.

## Decisive findings

| Priority | Finding and implication | Evidence at inspected baseline | Required correction |
|---|---|---|---|
| P1 | Canned executor output becomes `done`; canned review returns a score and empty findings. This can mislead the operator about work performed. | [unified_crew.py 61–84](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/c153e0a66329673bb44c5203c0b54911c9905fe3/command/unified_crew.py#L61-L84); [zencode_agent.py 129–141](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/c153e0a66329673bb44c5203c0b54911c9905fe3/command/agents/zencode_agent.py#L129-L141) | Separate simulated output from execution; no invented scores; success needs a checked receipt. |
| P1 | MCP without a handler and A2A/ACP paths return `delivered` without a corresponding transport action. | [protocol_router.py 119–132](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/c153e0a66329673bb44c5203c0b54911c9905fe3/command/protocol_router.py#L119-L132) | Return not implemented or blocked until actual transport and receipt validation exist. |
| P1 | The command API has wildcard CORS, caller-provided action/identity fields and a direct-launch all-interface bind, with no authentication dependency in the file. Actual network exposure is unknown. | [command_center_api.py](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/c153e0a66329673bb44c5203c0b54911c9905fe3/command/command_center_api.py) | Keep it unexposed; implement authenticated principals, allowed targets/actions and per-task limits before connecting real adapters. |
| P1 | `fury_deploy` gathers exceptions as values, ignores per-task outcomes and always reports complete; unknown agents are filtered out. | [agents/__init__.py 105–115](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/c153e0a66329673bb44c5203c0b54911c9905fe3/command/agents/__init__.py#L105-L115) | Reject unknown workers, retain errors, and distinguish success, partial and failure. |
| P1 | General CI masks pytest errors with `|| true` and masks failed container health checks. A green job is not reliable proof for those checks. | [ci.yml](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/c153e0a66329673bb44c5203c0b54911c9905fe3/.github/workflows/ci.yml) | Remove failure masking in a focused patch and verify deliberate failure propagation. |
| P2 | The inspected crew uses in-memory history; batch routing skips the single-task record/hook path. Restart and batch audit coverage are incomplete in this component. | [unified_crew.py 19–36](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/c153e0a66329673bb44c5203c0b54911c9905fe3/command/unified_crew.py#L19-L36); [dispatcher.py 82–106](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/c153e0a66329673bb44c5203c0b54911c9905fe3/command/dispatcher.py#L82-L106) | Bind to existing Core transactions, leases, idempotency and restart reconciliation. Do not introduce another mission database. |
| P2 | One “multiplex” path runs synchronous nested loops. The separate command API uses gather, so concurrency behavior differs by entry point. | [unified_crew.py 151–159](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/c153e0a66329673bb44c5203c0b54911c9905fe3/command/unified_crew.py#L151-L159) | Pick one bounded scheduler and demonstrate actual overlap, cancellation and result merge. |
| P1 prerequisite | Native bridge routing is telemetry-only and returns `executed: false`; Core export is a draft. Host identities, ACL provisioning, tunnels and real jobs remain separate. | [native README](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/c153e0a66329673bb44c5203c0b54911c9905fe3/n95_native/README.md); [Core handoff](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/c153e0a66329673bb44c5203c0b54911c9905fe3/n95_native/core_handoff.py) | Collect real host evidence, validate Core binding and complete one scoped job before promoting runtime status. |

These are findings and acceptance criteria. This documentation change does not claim to fix their implementations.

## What deserves preservation

The native bridge rejects stale/conflicting receipts, distinguishes synthetic identities from physical machines, restricts accepted metadata, disables redirects/proxy inheritance for its loopback client, and persists accepted receipts transactionally. Its README describes HMAC and hash-chain limitations candidly. Preserve these properties while adding task execution separately.

The existing registry and C1–C6 integration order already name the hard work. Continue them. Adding another coordinator repository, memory database or agent roster would increase reconciliation work before closing the known gaps.

## Repository boundaries

| Repository | Evidence and role recommendation |
|---|---|
| `ark95x-unified-sovereign-stack` | Existing integration registry, focused native bridge and explicit C1–C6 path. Chosen home for this cross-repository audit and team workspace. This does not declare every module production-ready. |
| `oneness-system` | Contains real monitoring/report/preview code and a scaffolded nine-agent scheduler. Reuse selected Windows components after review; no second top-level mission authority. Its scheduler tick stubs and default healthy state do not prove agent work. |
| `central-command-ops` | Prototype: the four named agencies use nginx images; SALAS references an absent `api/main.py` in the inspected complete tree. Published availability/throughput claims lack supporting measurements in that tree. |
| `ark95x-omnikernel-orchestrator`, `NetX`, `flame-hq1`, `net95x` | Trees inspected for overlap and placement only. No comprehensive implementation or runtime certification. |

Oneness sources: [monitor cycle](https://github.com/Ark95x-sAn/oneness-system/blob/201593a438150c4d3235c1b7e559d35f9c39e524/src/ops_mind/mind.py), [scheduler](https://github.com/Ark95x-sAn/oneness-system/blob/201593a438150c4d3235c1b7e559d35f9c39e524/src/oneness_orchestrator.py). Central sources: [Compose](https://github.com/Ark95x-sAn/central-command-ops/blob/430b370911b9fa8389009e2379ea1ad1ac4226b8/docker-compose.yml), [architecture](https://github.com/Ark95x-sAn/central-command-ops/blob/430b370911b9fa8389009e2379ea1ad1ac4226b8/docs/architecture.md), [SALAS Dockerfile](https://github.com/Ark95x-sAn/central-command-ops/blob/430b370911b9fa8389009e2379ea1ad1ac4226b8/salas/Dockerfile).

Some inspected public trees include case/domain/log paths. Their contents were not read for this audit, so exposure is not established. Review classification and visibility before widening team access. Do not copy raw diagnostics, case facts, financial records or credentials into public operations documents. No collaborators, permissions or repository visibility were changed.

## Verification record

- Two distinct source-review workers completed bounded read-only tasks; no additional local agents were installed.
- Authenticated GitHub reads and the seven-tree inventory succeeded. This proves access to those resources, not every connected product or host.
- `python -m pytest -q tests/test_native_bridge.py tests/test_core_handoff.py tests/test_device_mesh.py` could not start because pytest is absent. No packages were installed to conceal the limitation.
- The existing standard-library alternative, `python -m unittest discover -s tests -p test_native_bridge.py -v`, ran **16 tests in 1.574 seconds, all passed** on the Linux audit host. It exercised synthetic loopback and temporary local state. It did not run the other two suites or Windows PowerShell.
- No model inference, device control, cross-device transport, current scheduled job, deployment or end-to-end business workflow was verified.
- Draft documentation commits use `[skip ci]` to avoid triggering the repository's unrelated installer/scanner workflows. Skipped checks are not passing checks. No workflow file or repository setting is changed by this increment.

## Official references checked

- [NVIDIA local AI stack](https://developer.nvidia.com/topics/ai/local-ai)
- [Microsoft CUDA in WSL](https://learn.microsoft.com/en-us/windows/ai/directml/gpu-cuda-in-wsl)
- [NVIDIA live skills catalog](https://github.com/NVIDIA/skills/blob/main/skills.sh.json)
- [NemoClaw documentation skill](https://github.com/NVIDIA/skills/blob/main/skills/nemoclaw-user-guide/SKILL.md)
- [Relay observability skill](https://github.com/NVIDIA/skills/blob/main/skills/nemo-relay-plugin-observability/SKILL.md)
- [RAG evaluation skill](https://github.com/NVIDIA/skills/blob/main/skills/rag-eval/SKILL.md)

These moving upstream pages were inspected October 6, 2026. No upstream code, model, driver or skill was adopted. Catalog presence is not capability readiness.
