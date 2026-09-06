# Network-95 service design: three products, one operating core

Prepared 2026-09-06. **Status: proposed service design and pricing hypotheses.** These packages have not been sold, benchmarked on customer hardware, or validated for demand. A synthetic demonstration proves only the behavior exercised in that demonstration. Physical device enrollment, startup recovery, networking, model execution, and customer outcomes require separate evidence.

## Aim

Give a customer one useful workflow that completes on their own equipment, shows its inputs and output, and reports where it stopped. Expand from one device to a coordinated three-device operation using the same queue, policies, evidence records, and operator console. Amara is the coordination role; completion is established by recorded checks, not agent narration.

The first proposed customer use case is **an approved document folder → a source-linked operational brief → a reviewed next-action queue**. Examples include a small business organizing its own procedures, job notes, inventory documents, or project records. Outbound messages, purchases, account changes, and publication remain separate actions with their own authority.

No market size, income, conversion, efficiency gain, or prediction accuracy is asserted here. Customer interviews and paid trials must establish demand.

## Proposed installation products

All three prices are **one-time installation fees**. Hardware, electricity, internet, cloud/API usage, third-party subscriptions, and license fees are paid separately by the customer. The installer accepts only configurations that pass a documented compatibility preflight. A connector means configuring one already-supported interface; building a new integration requires a separate quote.

| Offer | $100 — Single Workflow | $500 — Three-Device Core | $1,000 — Small-Team Operations |
|---|---|---|---|
| Customer result | One approved folder becomes a traceable brief on one compatible device | One workflow moves from console through core and worker and returns a verified result | Up to three useful workflows operate across the same three-device system with assigned user roles |
| Devices | One compatible endpoint with a working, supported local model runtime already available | Up to three compatible devices: one core, one worker, one console | Same three-device maximum; up to three named operator accounts |
| Workflows | One prebuilt folder-to-brief workflow | One prebuilt workflow spanning core and worker | Up to three prebuilt workflows selected from the tested catalog |
| Integrations | One approved local folder | Up to two supported connections; the source folder counts as one | Up to four supported connections; each source or destination counts |
| Automation | One manually triggered run; customer may choose one supported daily schedule instead | One customer-selected schedule plus startup/status reporting | Up to three schedules, failure notification inside the console, and a review queue |
| Operator interface | Local run command or simple local page and a report | Shared authenticated console, job status, cancel control, and evidence view | Same console plus the tested account/role controls and workflow ownership |
| Local AI | Use the compatible runtime/model already present | Configure one approved local runtime/model on the worker, subject to hardware and model-license preflight | Same runtime; configure up to two tested task routes using approved models already within equipment limits |
| Proof delivered | Input manifest, output, run log, and the defined acceptance results | Three-device enrollment record, end-to-end run, interruption recovery evidence, and acceptance results | Evidence for each workflow, account access checks, restart recovery, and backup/restore check |
| Handoff | One-page run/stop/recovery guide | Device map, runbook, installed-version list, and credential custody handoff | Same documents plus workflow owners, change procedure, and a short operator session |
| Included correction support | 15 minutes within 7 days | 30 minutes within 14 days | 60 minutes within 30 days |
| Installation labor cap | 1.25 hours total, including the support allowance | 5 hours total, including the support allowance | 10 hours total, including the support allowance |

The $100 offer is a narrow entry product for an already-compatible machine. It does not fund workstation repair, operating-system upgrades, model downloads on slow links, novel connector development, or a three-device deployment. The installation clock and scope are agreed after preflight; a configuration that cannot fit the package is declined or separately quoted before chargeable work begins.

For every tier, unrequested changes, a new workflow, unsupported hardware, OS recovery, public internet hosting, a production availability guarantee, and unbounded troubleshooting are excluded. Health/wearable data is excluded by default. Continuous observation of people, covert monitoring, medical interpretation, automated financial transactions, and legal filing are outside these offers.

### Illustrative delivery economics

These figures are **planning assumptions**, not market rates or profit forecasts. Use an internal loaded labor cost of **$50/hour**. Replace it with actual labor, acquisition, insurance, administrative, tax, and support costs before setting commercial prices.

| Item | $100 | $500 | $1,000 |
|---|---:|---:|---:|
| Preflight and scope, hours | 0.25 | 0.50 | 1.00 |
| Installation and configuration, hours | 0.50 | 2.75 | 5.50 |
| Validation and handoff, hours | 0.25 | 1.25 | 2.50 |
| Included support reserve, hours | 0.25 | 0.50 | 1.00 |
| Total labor, hours | 1.25 | 5.00 | 10.00 |
| Labor at $50/hour | $62.50 | $250.00 | $500.00 |
| Illustrative direct delivery expense | $5.00 | $20.00 | $40.00 |
| Extra contingency reserve | $10.00 | $50.00 | $100.00 |
| Remaining contribution before other business costs | **$22.50** | **$180.00** | **$360.00** |

The $100 package has little room for surprises. Proceed only if a repeatable installer and preflight keep delivery inside 1.25 hours. If support or installation exceeds the cap in two of the first three paid trials, narrow the scope or change the price before selling another identical package. Never recoup overruns through an undisclosed subscription.

**Separate ongoing support hypothesis:** $75/hour, in 30-minute blocks, for customer-approved work after the included allowance. No automatic enrollment, background monitoring obligation, or availability promise. A later monthly service can be priced only after actual support demand and operating costs are measured.

## Acceptance and customer proof

Each sale identifies its workflow, approved inputs, expected output fields, failure behavior, relevant devices, and data boundaries before installation. Test with synthetic or explicitly customer-approved non-sensitive fixtures. Preserve failures in the report.

**Single Workflow:** process a valid fixture with the expected source references; reject an unreadable or disallowed input with a visible reason; rerun without duplicating the queued action; and demonstrate run/stop. All required cases must pass on the customer's endpoint.

**Three-Device Core:** pass the preceding checks; prove the console, core, and worker identities on three actual machines; run five consecutive representative jobs; disconnect the worker and show a visible waiting/failed state; reconnect without duplicate execution; restart the core and show the expected queue recovery. No required check may remain blocked.

**Small-Team Operations:** pass the core checks and the declared scenario set for every purchased workflow; run ten consecutive representative jobs per workflow; verify user access against the purchased account roles; demonstrate cancellation, a failed connector, and restoration of the workflow configuration/evidence backup. The finite scenario set is agreed in advance. It is not a universal reliability guarantee.

The customer receives a compact proof packet containing timestamps, software/configuration versions, device identifiers, approved input manifest, relevant output artifacts, checks with expected and observed results, failures, and handoff instructions. Do not include secrets or raw sensitive material in the packet. Hashes can establish artifact identity; they do not establish that a statement is true or make a writable local log immutable.

### Percentage reporting without invented certainty

Report denominators and the observation window alongside every percentage:

- **Deployment check completion:** completed checks / predeclared applicable checks. Show passed, failed, blocked, and not run separately; completion is not success.
- **Acceptance pass rate:** passed required cases / all required cases. A blocked or unrun required case cannot count as passed. Readiness requires every required blocking case to pass, regardless of the average.
- **Observed workflow success:** attempts that produced all required outputs and proof / all eligible attempted runs in the stated period. Retain failed and retried attempts; disclose canceled runs separately and define eligibility before measurement.
- **Evidence coverage:** output claims with the required linked evidence / all output claims identified as requiring evidence. Coverage measures traceability, not truth; unresolved contradictions remain visible.

Example: “10 of 10 defined demo cases passed on this build; physical-device checks 0 of 3 completed.” Never present this as “100% autonomous,” “100% safe,” or “100% audit proof.”

## Desired three-device operation

This is the user's target topology, based on the stated equipment. It is **not a current device inventory or deployment verification**.

| Device | Proposed responsibility | Must be proved on the actual device |
|---|---|---|
| GM700 / SOLARISX | Core queue, local operational database, policy evaluation, workflow registry, evidence index, scheduler | Actual hostname/specifications, compatible OS/runtime, authenticated reachability, disk permission, startup behavior, restart recovery, and backup restoration |
| RTX 2080 PC | Local model execution and bounded workflow jobs | Actual GPU/VRAM and driver/runtime compatibility, approved model fit, measured latency, queue lease behavior, cancellation, and recovery after failure |
| Surface Pro X | Operator console and approvals; inspect results and send authorized tasks | Actual ARM64 browser/client compatibility, authenticated access, display behavior, and absence of assumed x64-only dependencies |

Use a tested private authenticated connection between nodes. The core keeps the mission state and task leases. The worker returns outputs with evidence references. The console renders the same state; it does not maintain a separate competing task queue. Do not assume the three machines are online because they were previously mentioned or because a loopback demo succeeds.

“Native local” acceptance means the necessary services run on the customer's own named machines, recover according to the runbook, and complete the purchased local workflow with cloud model calls disabled. A browser console on the Surface can satisfy its console role without pretending that an ARM64 machine runs an untested x64 worker.

### Logical operating roles

| Role | Responsibility | Authority boundary |
|---|---|---|
| **Amara — coordinator** | Turn the aim into bounded tasks; assign eligible workers; reconcile state; select the next authorized step | Cannot turn an unverified claim into a fact or override the policy decision |
| **Atlas — verifier** | Check required outputs, linked sources, failure conditions, and acceptance evidence | Records pass/fail/unknown; cannot certify checks it did not observe |
| **Axiom — policy** | Enforce scope, connector allowlists, account permissions, data boundaries, budgets, and required approval | Denies or pauses out-of-scope actions; never treats a model's request as authority |
| **ArcX — worker** | Perform the permitted local job and return artifacts/log references | Receives only the data and capabilities needed for the leased task |

These names describe responsibilities. They may be implemented by deterministic software, one model, or multiple isolated workers. They are not proof of independent running agents. A 9×9 capability map is likewise a design map, not 81 deployed agents.

## The 9×9 bridge: 81 capability cells

The nine lifecycle stages are **discover → authorize → collect → normalize → decide → execute → verify → record → adapt**. Each row below is a domain; every cell describes a concrete proposed operation. The first release implements only the cells needed for its acceptance cases.

| Domain | Discover | Authorize | Collect | Normalize | Decide | Execute | Verify | Record | Adapt |
|---|---|---|---|---|---|---|---|---|---|
| **1. Device operations** | Identify actual nodes | Enroll approved node | Read OS/architecture | Create device record | Choose eligible host | Run bounded job | Check output and exit | Save node/run IDs | Quarantine failing host |
| **2. Connectivity** | List reachable endpoints | Allow named peers | Capture connection result | Classify network errors | Choose available route | Send leased task | Confirm authenticated reply | Save latency/failure | Back off and retry |
| **3. Identity and privacy** | Identify data owners | Grant scoped permissions | Read consent settings | Map account roles | Evaluate access rule | Issue limited capability | Test forbidden access | Log policy decision | Revoke expired access |
| **4. Knowledge and files** | Enumerate approved folder | Confirm source scope | Read allowed documents | Extract text/provenance | Select relevant evidence | Produce cited brief | Check source support | Save hashes/references | Refresh changed sources |
| **5. Workflow operations** | Inventory useful tasks | Set action boundaries | Read submitted job | Validate job schema | Select tested workflow | Run leased steps | Check acceptance outputs | Save step state | Replay approved revision |
| **6. Model routing** | List installed models | Approve model/license | Read task requirements | Classify sensitivity/size | Select fitting runtime | Invoke bounded inference | Validate output contract | Save model/version/cost | Compare held-out results |
| **7. App connections** | List supported interfaces | Approve account scopes | Fetch allowed records | Map fields and IDs | Plan necessary change | Execute authorized call | Confirm returned state | Save connector receipt | Handle schema drift |
| **8. System-health telemetry** | Identify service metrics | Allow technical probes | Sample queue/disk/latency | Apply units/timestamps | Detect configured limit | Raise local alert | Recheck underlying metric | Save technical event | Tune reviewed threshold |
| **9. Optional personal data** | Identify requested export | Obtain explicit opt-in | Import selected file | Label units/time zone | Apply user display rule | Render chosen summary | Check source/units only | Store in separate vault | Change scope by consent |

“Adapt” means a measured proposal or a preauthorized operational response. Runtime retries and choosing a known available worker may be automatic within policy. Changing code, permissions, connector scopes, data categories, models, schedules, or budgets requires the relevant change authority, a versioned change, defined regression checks, and a rollback path. No self-editing production loop is included.

## System health and personal health are distinct

**System-health telemetry** concerns queue length, service uptime, task latency, disk capacity, process failure, and similar technical facts. It is not evidence of a person's pulse, presence, sleep, location, stress, or medical condition.

An optional personal/wearable import is a separately scoped extension. It starts disabled. The user chooses the source, fields, period, purpose, retention, and deletion method. Keep those records separate from business/system logs and deny other connectors and models access unless that exact use is authorized. No background wearable connection, physiological inference, treatment recommendation, or automatic sharing is implied. Use synthetic wearable-shaped data for demonstrations unless specific real-data consent is recorded.

## License-aware integration and reuse

Prefer integration through supported interfaces rather than merging unrelated repositories into one undifferentiated codebase. Repository popularity does not establish commercial redistribution rights, maintenance quality, or fitness for this service.

For each shipped component, retain its project URL, pinned version/commit, license text, copyright notices, required attribution, dependency record, security review status, and the way it is used: separate customer-installed process, API client, modified source, or bundled binary. Track model weights and dataset terms separately from application code.

Exclude any component whose commercial use, hosted-service use, modification, or redistribution terms are unresolved for the planned packaging. Some components may be usable as separate customer-owned installations while their inclusion in a resold bundle requires different treatment; verify the specific license and intended integration before committing. Do not describe source-available software as open source without checking its terms. A customer provides their own third-party accounts; credentials are never copied into an installer or another customer's environment.

## Forward thesis and backcast

**Strategic inference to test:** customers may place more value on private workflows that finish, recover, and show evidence than on adding more named agents. Network-95's proposed advantage is one operating state across a small device fleet, a constrained action boundary, understandable failure handling, and a concrete proof packet. This is a hypothesis, not a statement that the market has selected a winner or that AI can know the next major product category.

Work backward from a customer accepting a repeatable paid installation:

| Milestone | Deliverable | Proceed when | Stop, narrow, or revise when |
|---|---|---|---|
| **M0 — Bounded demonstrator** | Synthetic jobs, queue, four logical roles, evidence output, and a clearly labeled 9×9 map | Every declared demo case passes; outputs/logs distinguish simulated devices from real devices | Outputs imply an unconnected machine ran a task, or failed actions appear successful |
| **M1 — Actual three-device proof** | GM700 core, RTX worker, Surface console, signed-in device records, and restart/reconnect evidence | All three devices are individually observed; representative workflow and recovery cases pass with cloud inference disabled | Architecture/runtime compatibility is unknown, access is missing, jobs duplicate, or results cannot be traced |
| **M2 — Repeatable installer** | Versioned package, preflight, install/uninstall, backup/restore, and customer runbook | Clean installation and rollback work on each supported target configuration without undocumented manual repair | Repeat deployment depends on hidden credentials, unlicensed redistribution, or unrecorded local changes |
| **M3 — Problem validation** | Five interviews in one narrow customer segment and three concrete workflow examples | At least three interviewees confirm the same recurring problem and two agree to review a priced, scoped offer | Interest is only general AI curiosity or required scope does not fit the service |
| **M4 — Three paid trials** | Three independently accepted installations with labor, expense, support, and failure records | Customers accept their proof packets; every tier stays within its labor cap and positive contribution assumptions | Two trials exceed the labor cap, a required safety/data boundary fails, or customers do not use the result |
| **M5 — Repeatable service** | Published scope, tested compatibility list, delivery checklist, and support process | Ten consecutive installations meet acceptance, actual economics remain positive, and support fits the allowance | Reliability or delivery cost deteriorates as volume grows; suspend sales of the failing configuration |

These are proposed operating gates, not date or revenue forecasts. Count a sale only after an actual transaction, an installation only after physical deployment evidence, and an outcome only after its declared acceptance condition is observed.

## Immediate completion target

Build and verify the bounded local demonstrator first, attach its actual test results, and leave physical checks explicitly unverified until they run on the GM700, RTX 2080 PC, and Surface Pro X. The smallest initial deliverable is one approved document workflow with shared state, scoped execution, useful failure messages, and a proof packet. Sell that result only after it can be installed repeatedly inside its scope and labor allowance.
