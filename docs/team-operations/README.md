# Network-95 team operations

**Aim:** one authorized request reaches one real worker, produces a source-linked result, survives interruption, and returns proof to the same mission record.

Prepared October 6, 2026. This workspace is a reviewable operating specification and evidence snapshot. It does not start a controller, enroll a device, install software, create a schedule, or change the existing Core mission authority.

- [Current system map](current-state.svg)
- [Source audit and prioritized gaps](AUDIT.md)
- [Machine-readable evidence snapshot](system-state.json)
- [Task packet template](task-template.json)
- [Existing integration sequence](../N95_INTEGRATION.md)
- [Canonical project registry](../JARVIS_REGISTRY.md)

## Where the system actually stands

Network-95 has a substantial collection of code, operating instructions, and reported hardware. Its strongest inspected integration is a bounded telemetry bridge. The available evidence does **not** establish an operational, unattended Windows agent agency across the physical devices.

This audit listed 30 accessible GitHub repositories and inspected seven repository trees. Detailed implementation review focused on this stack, `oneness-system`, and `central-command-ops`; it was not a complete security or dependency audit of all 30 repositories. Two separately invoked reviewers inspected code. No physical Windows device was reached.

| Layer | Observed state | What the evidence supports |
|---|---|---|
| GitHub | Authenticated repository reads succeeded | Accessible source and version history, not installed services |
| Native bridge | 16 existing tests passed on the Linux audit host | Synthetic loopback transport, signatures, replay/expiry, SQLite recovery and boundary tests |
| Command agents | Implementations contain canned results and false completion paths | Prototype behavior; see P1 findings |
| Existing Core | Declared mission authority in the integration design | Current deployed source, database and API binding not inspected here |
| GM700 / SOLARISX | Operator-reported Windows 11, RTX 5070 Ti 16 GB, 32 GB RAM | Hardware planning input; no fresh device receipt |
| MSI / RTX 2080 | Operator-reported separate Windows 11 machine | Candidate worker; current RAM, driver, model fit and service health unknown |
| Surface Pro X | Reported review device | Candidate authenticated console; connection untested |
| Other phones, tablets and HQ network equipment | Reported inventory | No inferred live endpoints, VLANs, peer connectivity or unified control |
| OpenClaw, Copilot and other named allies | Intended integrations | Each needs its own authenticated adapter and tested capability |

`system-state.json` is a static audit snapshot, **not a new mission queue**. The map uses solid lines for relationships inspected in this audit and dashed lines for proposed or unverified runtime connections. “Unknown” does not mean absent or broken.

## One coordination model

Ben retains priority and authorization. Dot / OSK. Knox names the coordinating role; it is not a second commander beside the existing Core. The existing Core remains the intended durable mission authority. GitHub holds code, reviewed changes, issues and operating specifications; a GitHub issue is not permission to perform every action described in it.

| Responsibility | Accountable role | Required output | Current live status |
|---|---|---|---|
| Interpret and route | Dot / Knox | One task, owner, scope and acceptance | Available within active assistant sessions; no resident dispatcher proved |
| Build | Orange / authorized worker | Artifact, exact revision and execution receipt | Local Windows adapter unverified |
| Challenge | Black | Specific failure case tied to source | Two bounded source-review workers participated in this audit |
| Verify | White | Check the exact artifact and postcondition | Separate reviewer required for a release; not a renamed author |
| Record | Green | Update existing registry/mission record | Versioned documents available; Core write path unverified |

These names allocate responsibilities, not running agent counts. Start with one worker and one reviewer. Add concurrency only after a measured overlap test, resource measurements, independent output paths and a controlled merge. All children inherit the same mission limits and data boundary.

## Proposed work board

Role owners below are proposed responsibilities, not accepted human assignments. Due dates remain unset until an executing owner accepts. Preserve the existing C1→C6 integration order; read-only host evidence and source corrections can advance alongside it.

| ID | Priority | Proposed owner | Next action | Acceptance / proof | Dependency |
|---|---|---|---|---|---|
| OPS-01 | P1 | Builder + White | Replace placeholder success/delivery with explicit simulated or not-implemented results | Missing adapter, unknown agent and failed worker cannot return success; per-task receipts retained | Source patch and review |
| OPS-02 | P1 | Security owner | Define authenticated principal, target/action allowlist, limits and loopback default for command API | Unauthorized task rejected; no broad interface exposure before boundary test | Before any real adapter |
| OPS-03 | P1 | Build owner | Remove masked test failures and false-positive container health outcomes | A deliberately failing isolated check makes the workflow fail; passing path stays valid | Scoped CI patch |
| OPS-04 | P1 | Core owner | Locate canonical Core revision and actual storage/API binding | Mission idempotency, transaction conflict, lease expiry and restart recovery receipts | C1 |
| OPS-05 | P1 | Local operator | Run existing Windows preflight from a reviewed checkout; capture current GPU and host identity separately | Host-bound timestamp, script hash, OS/build, raw free bytes, GPU/driver and service evidence | Authenticated device session |
| OPS-06 | P1 | Local operator + White | Provision least-privilege per-device identity and private application route | Authorized test succeeds; unauthorized peer fails; expiry, cancellation and reconnect verified | OPS-02, OPS-04, OPS-05; C2–C3 |
| OPS-07 | P2 | Inference owner | Benchmark one existing local model on a synthetic task | Exact model/runtime, context, latency, peak VRAM/RAM, result quality and timeout receipt | OPS-05; C3 |
| OPS-08 | P2 | Workflow owner | Complete the existing folder-to-brief mission through Core | Source-linked result, review receipt, output digest and interruption recovery | C1–C5 |
| OPS-09 | P2 | Recovery owner | Restore into a disposable environment and reconcile pending tasks | No duplicate effects, verified restored state, known recovery time | C1–C2 |
| OPS-10 | P1 | Repository owner | Review public case/domain/log paths and define team data boundaries | Content classification and authorized remediation decision; no sensitive material copied into this workspace | Separate scoped exposure review |

No timers, notifications, issues or schedules are created by this table. Use the existing mission/task record when one exists; import a task only through its authorized interface with a native receipt.

## Windows 11 next move

Reuse [N95-Native-Preflight.ps1](../../tools/N95-Native-Preflight.ps1) and [the Windows runbook](../N95_NATIVE_WINDOWS.md). Do not create another installer. The script is an inventory tool: disk/RAM are informational; it does not enforce a free-space floor, report the NVIDIA driver, or authenticate the physical host. Its model-list probe currently runs only for the RTX2080 role, so it does not establish GM700 inference readiness.

The operator's current working free-space floor is **52 GB**, superseding the older 200 GB planning threshold for this session. Preserve raw bytes and the display unit; GB/GiB must be explicit before codifying a numeric runtime gate. Historic registry entries retain the threshold in force when written. Unknown space blocks device mutation, not read-only diagnosis. No current free-space value is asserted here.

After the reviewed script runs on the real target, obtain a private host/session binding and read-only `nvidia-smi` observation through the authenticated local operator. Keep raw host identifiers and diagnostics outside this public repository. A source hash and role label alone do not bind a receipt to the physical machine.

Retain GM700 as the existing Core/control host while measuring inference there first, given the reported 5070 Ti. Keep RTX2080 as a bounded secondary worker and Surface as the review console. Moving authority or always-on infrastructure to MSI requires uptime, RAM, storage and restore evidence; the hardware inventory alone does not justify that migration. The two GPUs do not automatically pool VRAM.

## NVIDIA recommendation

Use the equipment already reported before selecting more platforms. NVIDIA's [local AI guidance](https://developer.nvidia.com/topics/ai/local-ai) separates agent harnesses, inference backends, models and applications. Microsoft documents [CUDA in WSL on Windows 11](https://learn.microsoft.com/en-us/windows/ai/directml/gpu-cuda-in-wsl). Neither source verifies this machine's installation. Choose native Windows or WSL according to the selected runtime; WSL is not a blanket prerequisite for all local AI.

Start with one existing small, quantized model and one task. Increase size or concurrency only after measuring total runtime memory and context use; parameter count alone is not a fit guarantee. Defer a RAM purchase, more model downloads, distributed serving and new agent frameworks until measurements identify the constraint.

The live NVIDIA skills catalog and three cards were inspected. **Reserve `nemoclaw-user-guide`** if the existing OpenClaw lane is selected: it routes to current sandbox/setup documentation. First useful prompt: “Review current Windows 11 and local-inference prerequisites for my existing OpenClaw plan; list the smallest missing proof without installing anything.” Optional future installation command, not executed:

```sh
npx skills add nvidia/skills --skill nemoclaw-user-guide --agent codex --global --yes
```

`nemo-relay-plugin-observability` is conditional on actually adopting the matching Relay version. `rag-eval` requires the NVIDIA RAG Blueprint evaluator layout and judge/API setup; it is not a drop-in benchmark for this stack. Neither is needed to prove the first local workflow. No NVIDIA skill, driver, model or Windows component was installed in this audit.

## First operational acceptance

Use three synthetic business notes in an explicitly allowed folder. A named worker acknowledges the exact task, reads only those files, produces a short brief with source locators, and records an output digest. A separate verifier checks all claims and deliberately tests an out-of-scope path, a timeout, cancellation and replay. Interrupt and restart once; reconciliation must avoid duplicate output/effects. The same Core mission record retains the accepted result, errors and recovery receipt. Only that tested capability may then be called operational.

Success is a proven request-to-result loop. A dashboard, “online” badge, role roster, signature, model listing or passing synthetic test alone cannot substitute for it.
