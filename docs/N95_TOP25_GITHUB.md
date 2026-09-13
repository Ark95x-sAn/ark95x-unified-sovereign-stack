# Network-95: 25 GitHub candidates across capability classes

> Current harvesting gate: [2026-09-13 preparation](#harvest-preparation--2026-09-13). Earlier adoption labels remain historical recommendations; reserve/reject and the existing Core dependency order govern current intake.

This is a curated suitability review observed on 2026-09-06, not a worldwide ranking or a production bill of materials. Selection priorities: local operation, observable correctness, license clarity, supported device fit, integration burden and demonstrated need. No upstream source code was copied into the new bridge. These projects are reviewed candidates; installation is a separate step.

**Canonical integration decision:** keep the existing Network-95 Core mission engine and C1–C6 queue. PostgreSQL remains the next production-state dependency in that queue; the later/now labels in the research below describe individual adoption costs, not permission to replace that queue with a new SQLite authority. The new bridge uses SQLite only as a transport receipt spool.

**Minimum first deployment target:** existing Core + PostgreSQL + private authenticated gateway on GM700; Ollama on RTX; browser review on Surface. Add a specific MCP/app adapter only when its first workflow is defined. Retain the existing Tailscale connection if target checks pass. Prove backup restoration before customer operation. Do not install all 25 projects.

# Network-95 AI and data candidate review

Checked 2026-09-06. This is a fit-based shortlist of 12 candidates contributing to the parent's broader 25-project review, not a global ranking. Actual LICENSE/COPYRIGHT files, current README files and GitHub release metadata were read through the GitHub connector. Device placements and adoption order below are design recommendations; no software installation, live hardware access, performance result or completed cross-device integration is claimed.

The three-device working premise comes from the user: GM700 control plane, RTX 2080 model worker, Surface Pro X console. Keep one system with defined interfaces and one evidence model. Merge capabilities through adapters; do not indiscriminately combine source trees or run every component at once.

| Project / class | Function | Verified license and reuse caveat | Device fit (proposed) | Adoption |
|---|---|---|---|---|
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) — Agent orchestration | Stateful mission graph, checkpoints, role handoffs, human interrupts. | [License](https://github.com/langchain-ai/langgraph/blob/main/LICENSE): MIT; keep copyright and permission notices. LangSmith services are separate. | GM700 coordinates; RTX worker provides inference; Surface is console. | Use now when explicit graph/checkpoint execution is needed; do not require LangSmith. |
| [temporalio/temporal](https://github.com/temporalio/temporal) — Durable workflow service | Persist workflows across interruption and retry failed activities. | [License](https://github.com/temporalio/temporal/blob/main/LICENSE): MIT; retain copyright and permission notices. | GM700 service with database; SDK workers on GM700/RTX; Surface views UI. | Later: use for long-lived customer jobs once retries, migrations and recovery justify a separate service. |
| [nats-io/nats-server](https://github.com/nats-io/nats-server) — Device/event messaging | Publish/subscribe and request/reply; JetStream persists messages for replay. | [License](https://github.com/nats-io/nats-server/blob/main/LICENSE): Apache-2.0; preserve license/notices and mark modified files; no trademark grant. | GM700 broker; clients on RTX and Surface. No need to run three brokers initially. | Later, first device-event bus candidate when asynchronous workers are connected. |
| [ollama/ollama](https://github.com/ollama/ollama) — Local model runtime | Local model management, chat and inference API. | [License](https://github.com/ollama/ollama/blob/main/LICENSE): MIT for runtime. Every model has separate model/license terms. | RTX 2080 primary worker; GM700 CPU fallback after benchmark; Surface calls remote worker. | Use now: first inference adapter, health check and model-inventory endpoint. |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) — Embedded inference engine | GGUF CPU/GPU inference and compatible HTTP serving; hardware backend tuning. | [License](https://github.com/ggml-org/llama.cpp/blob/master/LICENSE): MIT; preserve notices. Model weights and bundled third-party components have separate terms. | RTX CUDA worker; GM700 CPU; Windows ARM64 build path can be tested for small Surface models. | Reference/fallback: use when Ollama cannot meet packaging, backend or latency requirements. |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) — Model gateway/router | One API across local/cloud providers with routing, fallbacks and usage controls. | [License](https://github.com/BerriAI/litellm/blob/litellm_internal_staging/LICENSE): MIT outside enterprise/; enterprise content has separate terms. Referenced enterprise/LICENSE returned 404 on current default branch. | GM700 gateway; RTX hosts local model; Surface uses authenticated core endpoint. | Later: add after a second approved model provider, rather than duplicating a single Ollama endpoint. |
| [open-webui/open-webui](https://github.com/open-webui/open-webui) — Operator chat workspace | Self-hosted UI for Ollama/OpenAI-compatible models, files, voice and tools. | [License](https://github.com/open-webui/open-webui/blob/main/LICENSE): Custom Open WebUI License; preserve branding unless <=50 direct end users in rolling 30 days, written permission, or qualifying enterprise license. Earlier material follows LICENSE_HISTORY. | GM700 hosts UI; RTX serves models; Surface browser/PWA console. | Use now optionally for internal operator chat; retain branding in product packaging until exact chosen scope is checked. |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) — Tool/application bridge | Expose typed tools, resources and prompts; connect approved MCP clients/servers. | [License](https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE): MIT; retain copyright and permission notices. | GM700 adapter host; per-device tool servers only for explicitly registered capabilities. | Use now for the first approved app connector, with version-specific examples and authorization. |
| [fastapi/fastapi](https://github.com/fastapi/fastapi) — Core service/API | Typed mission, evidence, telemetry, device registry and dashboard API. | [License](https://github.com/fastapi/fastapi/blob/master/LICENSE): MIT; retain copyright and permission notices. | GM700 control plane; lightweight RTX worker API; Surface browser/PowerShell client. | Use now: core boundary with request validation, authenticated adapters and explicit health endpoints. |
| [qdrant/qdrant](https://github.com/qdrant/qdrant) — Semantic retrieval store | Vector similarity, payload filtering and dense/sparse retrieval. | [License](https://github.com/qdrant/qdrant/blob/master/LICENSE): Apache-2.0 for server; preserve license/notices and modified-file notices. Check separate SDK/Edge component terms if selected. | GM700 store; RTX produces embeddings; Surface queries via core. | Later: only after an authorized corpus and a retrieval benchmark show it beats simpler search. |
| [postgres/postgres](https://github.com/postgres/postgres) — Transactional operational database | Canonical mission state, permissions, events and evidence indexes with transactions. | [License](https://github.com/postgres/postgres/blob/master/COPYRIGHT): PostgreSQL license; keep the specified copyright, permission and disclaimer paragraphs. | GM700 database service; workers/API clients connect through the core. | Later/production store: use when concurrent durable operation outgrows single-process SQLite. |
| [duckdb/duckdb](https://github.com/duckdb/duckdb) — Embedded evidence analytics | SQL over CSV/Parquet and local data; audit percentage and trend aggregation. | [License](https://github.com/duckdb/duckdb/blob/v2.0-cyanoptera/LICENSE): MIT; retain copyright and permission notices; review chosen extensions separately. | GM700 reports; portable local report worker where exact package is verified; Surface consumes generated reports. | Later: analytics layer over exported evidence; no separate database server needed for initial reports. |

## Compatibility findings that change implementation

- **langchain-ai/langgraph** — release observation: 1.2.11. Python >=3.10; repository releases include several packages, so releases/latest points to SDK 0.4.4 rather than core LangGraph.
- **temporalio/temporal** — release observation: v1.31.2. Development server is for local development/testing. Official production guide uses temporalio/server plus managed schemas and persistence.
- **nats-io/nats-server** — release observation: v2.14.6. Core NATS is at-most-once. Use JetStream for durable delivery; redelivery means workers still need idempotency.
- **ollama/ollama** — release observation: v0.33.3. Official docs list RTX 2080 compute capability 7.5. Native Windows Home/Pro support; Windows docs require NVIDIA driver >=551.61. No local device or driver verified in this research.
- **ggml-org/llama.cpp** — release observation: v0.4.0. Windows ARM64 documented LLVM preset. CPU/GPU hybrid support does not pool three PCs into one memory device.
- **BerriAI/litellm** — release observation: v1.99.1. Latest v1.99.1 is Docker-only; release says pip users stay on 1.99.0. Default branch is litellm_internal_staging, so deploy a tested release artifact.
- **open-webui/open-webui** — release observation: v0.11.3. README recommends Python 3.11 for pip install. Browser-based Surface operation avoids assuming ARM64 server compatibility.
- **modelcontextprotocol/python-sdk** — release observation: v2.1.1. Current stable is v2, Python >=3.10. v2 uses from mcp.server import MCPServer. Old mcp.server.fastmcp examples need migration or v1 upper bound (<2).
- **fastapi/fastapi** — release observation: 0.141.1. Python >=3.10 in current pyproject; CPU service does not require CUDA or a GPU.
- **qdrant/qdrant** — release observation: v1.19.1. Official README warns its sample docker run exposes all interfaces without authentication. Configure authenticated private access; do not use sample directly in a customer deployment.
- **postgres/postgres** — release observation: Use supported release from postgresql.org; this GitHub mirror has no releases/latest.. Default master is development code. Use vendor-supported binaries/packages; backup/recovery must be tested.
- **duckdb/duckdb** — release observation: v1.5.5. Native in-process read/write uses a single writer process. Quack remote protocol is documented as beta; keep initial operational writes in core transactional store.

## What to implement first

A small original core with an evidence ledger, typed mission state, three registered device roles, an authenticated worker interface and an Ollama adapter is a credible first integration target. Add LangGraph if the mission requires branching/checkpointing, MCP for a specific approved application, and Open WebUI for operator chat. NATS, Temporal, PostgreSQL, Qdrant, DuckDB and LiteLLM earn adoption through measured requirements. Keep llama.cpp as the alternative inference/embedding route. This is engineering judgment based on the documented roles and operating burden.

Useful improvement loops measure actual outcomes: successful verified missions / attempted missions, evidence-linked results / asserted results, replay-safe retries / injected interruption cases, and latency/cost per accepted result. No generic 'percent audit proof' should be claimed without a defined denominator and passing evidence. Self-improvement should propose versioned changes, run checks and retain rollback; runtime observations are not proof of autonomous self-modification or model training.

Health data is a separate approved connector domain. These 12 projects provide integration/storage capabilities but do not themselves give access to wearable or medical data, establish clinical validation, or justify diagnosis. No health data was retrieved in this research.

## Evidence ledger

Each license SHA below identifies the exact retrieved Git blob. These are source-document hashes, not signed binaries or build proofs. Latest default branches can differ from stable releases; re-read licenses at the exact version selected for distribution.

### langchain-ai/langgraph

- License blob: `fc0602feecdd6748623c852ab534e1ca612673c7`
- README blob: `97c31e9cb4d8fe56be8d768ce3eb5e22400e897e`
- https://github.com/langchain-ai/langgraph/releases/tag/1.2.11
- https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/pyproject.toml
- https://github.com/langchain-ai/langgraph/blob/main/LICENSE
- https://github.com/langchain-ai/langgraph/blob/main/README.md

### temporalio/temporal

- License blob: `3349f76795f4409cba6ae18ea56adf9fbd8346f3`
- README blob: `d89e30ebb9863ea82c9203e1e696170ea9484af9`
- https://docs.temporal.io/self-hosted-guide/deployment
- https://github.com/temporalio/temporal/blob/main/LICENSE
- https://github.com/temporalio/temporal/blob/main/README.md

### nats-io/nats-server

- License blob: `261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64`
- README blob: `4487552a792652c3e95d504e7b2f55507fdce05b`
- https://docs.nats.io/concepts/jetstream
- https://github.com/nats-io/nats-server/blob/main/LICENSE
- https://github.com/nats-io/nats-server/blob/main/README.md

### ollama/ollama

- License blob: `8e3dc978a7ca8c53f56bbedc5b558116140fc02e`
- README blob: `e511fbe3fd3e73fc6d7cfb5393d827cf70f0a2f6`
- https://docs.ollama.com/gpu
- https://docs.ollama.com/windows
- https://github.com/ollama/ollama/blob/main/LICENSE
- https://github.com/ollama/ollama/blob/main/README.md

### ggml-org/llama.cpp

- License blob: `e7dca554bcb802f98408383a864404e3aa4eacca`
- README blob: `aae3bcd35ad9c2ba3e914750a36e125fec0b5355`
- https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md
- https://github.com/ggml-org/llama.cpp/blob/master/LICENSE
- https://github.com/ggml-org/llama.cpp/blob/master/README.md

### BerriAI/litellm

- License blob: `3bfef5bae9b48c334acf426d5b7f21bc1913aab9`
- README blob: `92757fcbbc13555373644428e448eb728a2569b6`
- https://github.com/BerriAI/litellm/releases/tag/v1.99.1
- https://github.com/BerriAI/litellm/blob/litellm_internal_staging/LICENSE
- https://github.com/BerriAI/litellm/blob/litellm_internal_staging/README.md

### open-webui/open-webui

- License blob: `99f39e7feff29c93342877adad2d5c15e707444c`
- README blob: `f3499e38f5cb02b3a46e136a88bfd5e62766226e`
- https://github.com/open-webui/open-webui/blob/main/LICENSE
- https://github.com/open-webui/open-webui/blob/main/README.md

### modelcontextprotocol/python-sdk

- License blob: `3d48435454b105021b4f777c11b6b07d8d2ffea3`
- README blob: `cc067aca2587ccbaee92d2a986fb7cd88e7b4c25`
- https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.1.1
- https://py.sdk.modelcontextprotocol.io/migration/
- https://github.com/modelcontextprotocol/python-sdk/blob/main/pyproject.toml
- https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE
- https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md

### fastapi/fastapi

- License blob: `3e92463e6bd522a2a21e5f0a80d8089d6c4be20d`
- README blob: `bd7e9e96b015b92f219c596710c96a89068488c8`
- https://github.com/fastapi/fastapi/blob/master/pyproject.toml
- https://github.com/fastapi/fastapi/blob/master/LICENSE
- https://github.com/fastapi/fastapi/blob/master/README.md

### qdrant/qdrant

- License blob: `456fb05e0e936f439cf42c517b19797dafd53ff9`
- README blob: `cf4c1c5213148ed9d6388654f9d3e75b06504bc9`
- https://qdrant.tech/documentation/security/
- https://github.com/qdrant/qdrant/blob/master/LICENSE
- https://github.com/qdrant/qdrant/blob/master/README.md

### postgres/postgres

- License blob: `0a397648dcd3c2177acc58bd7daecd11ad64be62`
- README blob: `f6104c038b3d5c69e7dc058aa4518c3cbcf56731`
- https://www.postgresql.org/download/
- https://www.postgresql.org/support/versioning/
- https://github.com/postgres/postgres/blob/master/COPYRIGHT
- https://github.com/postgres/postgres/blob/master/README.md

### duckdb/duckdb

- License blob: `2719c9a23d2a37c1dfb7402e79f03bd615701e53`
- README blob: `62a575f9e8e82d1bbbba89ce140b3803af28fdbe`
- https://duckdb.org/docs/current/connect/concurrency
- https://duckdb.org/install/
- https://github.com/duckdb/duckdb/blob/v2.0-cyanoptera/LICENSE
- https://github.com/duckdb/duckdb/blob/v2.0-cyanoptera/README.md

## Scope limits

No remote repository was mutated. No user conversation archive, private business file, app credential or sensor stream was fetched. All project capability claims come from official repositories or documentation. License observations summarize retrieved terms and are not a legal opinion. The parent owns persistence of this intermediate research with the final deliverable.



# Network-95 operations candidates — verified research

Checked 2026-09-06 against official repositories, project documentation, and release metadata. This is the operations half of the 25-project candidate set, not a claim that these are a universal popularity ranking. No candidate was installed or merged by this research task. Device placement and sequencing are engineering recommendations; actual device reachability, RAM, drivers, permissions, and installed versions remain deployment checks.

**Recommendation:** integrate a small number of independently versioned services through APIs and events. Keep Network-95's mission state, permissions, evidence records, and user interface in its own code. Do not source-merge all projects into one program. A connected interface does not establish correct sensor readings, completed work, or reliable autonomy.

| Project | Class and concrete function | Verified project license / reuse note | GM700 Windows x64 core | RTX 2080 Windows x64 worker | Surface Pro X Windows ARM64 console | Sequence |
|---|---|---|---|---|---|---|
| [OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector) | Receive, filter, batch, and export logs, metrics, and traces; one telemetry transport | Apache-2.0; preserve applicable license/NOTICE requirements and audit selected dependencies | Native Windows collector gateway is documented | Local collector agent for worker/application telemetry | Read observatory through browser; do not assume an ARM64 collector package | **Later:** instrument the core first; add collector when multiple telemetry producers need it |
| [Prometheus](https://github.com/prometheus/prometheus) | Time-series metrics, rule evaluation, operational alerts | Apache-2.0 | Official Windows amd64 binary; central metrics store | Publish or export worker metrics; no second database required | Browser query/view through private network | **Later:** add once there are real recurring metrics; initial core can expose a metrics endpoint |
| [Grafana](https://github.com/grafana/grafana) | Dashboards combining metrics, logs, and traces | AGPLv3 OSS; Enterprise binary has separate proprietary terms. Commercial use is not automatically prohibited; modification/distribution obligations still apply | Official Windows amd64 OSS build | Data producer rather than second dashboard server | Browser dashboards | **Later:** optional internal observatory; independently packaged if included in a customer deliverable |
| [Tailscale](https://github.com/tailscale/tailscale) | Private encrypted network connecting the three machines | Repository BSD-3-Clause; hosted coordination service, packaged apps, trademarks, and service plans are separate considerations | Native Windows amd64 client | Native Windows amd64 client | Official native Windows ARM64 MSI exists | **Use now:** verify the existing connection and restrict service access; do not replace a working network gratuitously |
| [Headscale](https://github.com/juanfont/headscale) | Self-hosted implementation of the Tailscale control server | BSD-3-Clause | Documented Debian/Ubuntu service in Linux VM/host; not the selected native Windows path | Tailscale client only | Tailscale client only | **Reference:** sovereignty option once maintaining coordination, TLS, identity, upgrades, and recovery has a justified owner |
| [Home Assistant Core](https://github.com/home-assistant/core) | Local device integrations, home sensors, events, and automation | Apache-2.0 for Core; integrations/dependencies may have their own terms | Official Windows instructions run Home Assistant OS in a VM; allocate real resources and device passthrough as needed | Usually no server role | Browser controls and sensor views | **Later:** when specific owned sensors and integrations are identified; not a general health-data collector |
| [Node-RED](https://github.com/node-red/node-red) | Event flows bridging HTTP, MQTT, devices, and applications | Apache-2.0; independently review third-party nodes | Native Windows Node.js deployment documented; good optional integration hub | Connect narrow task/result endpoints | Browser flow editor and dashboard; ARM64 server unnecessary | **Use now when needed:** first bridge candidate for a concrete external integration; avoid installing without a first flow |
| [Eclipse Mosquitto](https://github.com/eclipse-mosquitto/mosquitto) | MQTT broker for sensor events and small device messages | Current LICENSE declares EPL-2.0 **OR** BSD-3-Clause (EDL-1.0); choose applicable terms and preserve notices | Official Windows x64 installer | Publish/subscribe as a client | View sensor state through core UI; no broker needed | **Later:** first real MQTT sensor justifies installation; use authentication and per-topic authorization |
| [restic](https://github.com/restic/restic) | Encrypted incremental backups and restore | BSD-2-Clause | Official Windows amd64 binary; back up core state and configuration | Back up required local files/models selectively | Native Windows ARM64 binary was not present in checked v0.19.1 release; choose a verified backup path before promising native coverage | **Use now:** once real persistent state exists, prove a restore, not just a successful backup command |
| [SOPS](https://github.com/getsops/sops) | Encrypted YAML/JSON/ENV/INI configuration, using age/PGP or managed keys | MPL-2.0; covered source-file obligations apply if modifying/distributing SOPS itself | Native amd64 .exe in checked release | Native amd64 .exe; receive only secrets needed by that role | Native arm64 .exe in checked release; console usually does not need service secrets | **Later:** useful when encrypted configuration must be versioned; it is not a running vault or complete secrets rotation system |
| [Open Policy Agent](https://github.com/open-policy-agent/opa) | Explicit policy decisions before task execution | Apache-2.0 | Windows amd64 .exe in checked release; REST/server or CLI decision point | Ask core policy service; enforce result locally | Display proposed action/approval state; no local OPA required | **Reference now / later service:** begin with a small auditable policy gate, extract to OPA when policies grow |
| [Playwright](https://github.com/microsoft/playwright) | Browser verification and automation with traces/screenshots | Apache-2.0; browsers and website access retain their own terms | Native Windows 11 test runner supported | Good browser execution worker; GPU not required for ordinary tests | Console and reports; native Windows ARM64 browser runtime not verified by this audit | **Use now for UI verification:** exercise actual workflows; production browser actions need the same scoped permissions as API actions |
| [n8n](https://github.com/n8n-io/n8n) | App workflows, schedules, integration nodes, and AI workflow composition | Sustainable Use License + Enterprise terms; source available, not permissive OSS. Paid consulting on client-owned internal instances differs from hosting/embedding for clients | Self-hosted service if already present; use supported runtime/container and current dependencies | Call worker endpoints rather than duplicate orchestrator | Browser workflow interface | **Reference / optional internal use:** avoid making paid embedded n8n the unlicensed foundation of the three product tiers |

## Material commercial distinctions

n8n's official help center says consulting that helps customers set up their own internal n8n instances does not require a commercial license on the consultant's part, with each customer's use case still determining requirements. It separately says hosting clients' workflows and credentials in the provider's instance requires Enterprise licensing, and embedding workflows for clients in a product calls for an Embed license. Product tiers should therefore clearly sell implementation work on a customer-owned setup, or use a different appropriately licensed orchestration core, or price an agreed n8n license. This is a report of the vendor's stated categories, not a ruling on a particular contract. [Official n8n help center](https://support.n8n.io/article/can-i-use-your-license-for-my-use-case) and [repository license](https://github.com/n8n-io/n8n/blob/master/LICENSE.md).

Grafana's official licensing material identifies its core OSS projects as AGPLv3. Its FAQ says customers may ship Grafana when complying with the license and describes source-sharing obligations for modifications distributed or offered across a network. It also offers separate proprietary options. Do not describe all Grafana use as forbidden commercially, or assume that downloading an Enterprise binary grants resale rights. Keep exact build/edition, notices, modifications, and delivery method in the product bill of materials. [Licensing page](https://grafana.com/licensing/) and [vendor licensing Q&A](https://grafana.com/blog/qa-with-our-ceo-on-relicensing/).

Tailscale's repository license does not make its hosted coordination service self-hosted. A three-device private connection can use the existing Tailscale service; Headscale is a distinct operating choice with its own upkeep. Official Tailscale pages have an apparent documentation inconsistency: the MSI instruction page still says to use x86 on ARM64, while the current package index explicitly publishes architecture-specific ARM64 MSI packages. The package listing is direct evidence that a native ARM64 installer exists; validate the selected package and installed client on the Surface. [Packages](https://pkgs.tailscale.com/stable/) and [MSI instructions](https://tailscale.com/docs/install/windows/msi).

## Minimum operations pattern to build first

1. Core maintains one mission queue and evidence store; workers register capabilities and poll only for authorized tasks.
2. Each observation carries source, timestamp, unit, device, quality/freshness, and privacy category. Preserve missing and stale values instead of filling them with guesses.
3. One idempotency key links request, attempts, result, and artifact. Verify outputs before marking completion.
4. Measure completion success, evidence coverage, freshness, rollback/restore success, and unauthorized-action rejection separately. A single inflated “autonomy percent” is not an audit.
5. Keep deployment changes versioned, reversible, and testable. Adapt task routing from measured outcomes; queue software changes for tests before activation.

For health-related inputs, ingest only an explicitly connected source/export with a defined purpose. A device heartbeat is operational telemetry, not evidence of a person's physical presence, vital signs, or health. Home Assistant and MQTT provide transport/integration capabilities, not medical validation.

## Platform and evidence links

Project license and function were checked on each repository above. Additional direct platform sources:

- OpenTelemetry Windows installation: https://opentelemetry.io/docs/collector/install/binary/windows/
- Prometheus official download platform table: https://prometheus.io/download/
- Grafana official OSS Windows download: https://grafana.com/grafana/download?edition=oss&platform=windows
- Node-RED native Windows setup: https://nodered.org/docs/getting-started/windows
- Home Assistant Windows VM installation: https://www.home-assistant.io/installation/windows/
- Headscale official Debian/Ubuntu setup: https://headscale.net/stable/setup/install/official/
- Mosquitto Windows x64/x86 binaries: https://mosquitto.org/download/
- Mosquitto exact dual-license declaration: https://github.com/eclipse-mosquitto/mosquitto/blob/master/LICENSE.txt
- Playwright operating-system requirements: https://playwright.dev/docs/intro
- restic release assets checked: https://github.com/restic/restic/releases/tag/v0.19.1
- SOPS release assets checked: https://github.com/getsops/sops/releases/tag/v3.13.3
- OPA release assets checked: https://github.com/open-policy-agent/opa/releases/tag/v1.20.2
- Headscale release assets checked: https://github.com/juanfont/headscale/releases/tag/v0.29.3

GitHub connector returned exact license content for n8n (blob SHA `f85f59baa906530c26cee26e0c9ddd6bd5f86dbd`) and Mosquitto (blob SHA `aae2e8ccf529cef6b058f98ede72090f6ae92721`). Release assets for restic, SOPS, OPA, and Headscale were read from the GitHub REST release metadata. Versions listed here record observations, not a production version pin or a security clearance.

<!-- N95-HARVEST-2026-09-13:BEGIN -->
## Harvest preparation — 2026-09-13

```yaml
mission: N95-HARVEST-PREP
role: Black
mode: research_and_documentation
flow: [discover, verify, read, reserve_or_reject]
canonical_page: docs/N95_TOP25_GITHUB.md
protocol: docs/REPO_EXTRACTION_PROTOCOL.md
registry: docs/JARVIS_REGISTRY.md
architecture_baseline_commit: a409b793f90d927b5baa30b46108c0752173ffcd
architecture_review: STATIC_COMPARISON_COMPLETE_WITH_GAPS
live_verification: NOT_RUN
dependency_installation: NOT_PERFORMED
device_admission: UNKNOWN
execution_authority_added: false
terminal_decisions: [reserve, reject]
```

### Category map and extractive patterns

Category IDs preserve the nine existing Jarvis layers. Cross-cutting device constraints apply to every layer. Each pattern is a review target; reserve is a research disposition only.

| ID / existing layer | Extractive pattern | Existing destination / dependency | Required acceptance evidence | Disposition |
|---|---|---|---|---|
| C01 Brain | Intent → typed mission → bounded attempts → checked result; inspect routing, checkpoint and failure paths | Existing Core; GM700; preserve C1–C6 sequence [S0] | One authoritative mission ID across retry/restart; no parallel mission authority | reserve |
| C02 Inference | Model identity → API request schema → output shape → timeout/error receipt [S2] | RTX worker through Core; C3 after C1/C2 | Fresh authorized model response; dimensions and finite values observed; independent repeat | reserve |
| C03 Memory | Source bytes → hash → source locator → derived chunks → retrieval → cited answer | Core evidence index; optional pgvector/Qdrant only after corpus and retrieval baseline | Every answer claim resolves to retained source; stale/deleted source excluded; no retrieval result becomes authority | reserve |
| C04 Automation | Trigger → idempotency key → transactional claim → bounded retry → result | Existing Core scheduler; C1–C3; Node-RED/n8n/Temporal remain conditional candidates | Duplicate trigger and worker crash do not duplicate the external effect; attempt/result linked to same mission | reserve |
| C05 Tools | Repository → allowlisted files → path/symbol map → bounded source slice; typed read-only adapter [S3/S5] | Existing adapter boundary; C4; use plain file reads before adding dependencies | Full source retrievable at pinned revision; input/output contract checked; denied action remains denied | reserve |
| C06 Dashboard | Receipt → timestamp/freshness → status projection → source drilldown | Existing Core API; Surface review; C5 | Missing/stale receipt displays UNKNOWN/STALE; installed and verified have distinct states | reserve |
| C07 Security | Identity → scope → policy decision → authenticated request → replay/expiry check [S0] | Existing Core policy + native bridge; no self-promotion | Wrong identity, stale receipt, replay conflict and scope escalation rejected; an independent observer confirms | reserve |
| C08 Data | Document → structured export → source/page/table locator; mission key → database constraints [S1/S4] | PostgreSQL authoritative state; transport SQLite remains a spool; document worker follows C4 | Required fields, page/row provenance and units preserved; duplicate keys rejected; restore reconstructs state | reserve |
| C09 Domain | Approved business question → authorized input schema → evidence-linked fields → reviewable result | First approved business-folder-to-brief workflow; C5/C6 | Selected brief is checked against original documents; domain action authority remains separate | reserve |

### Domain and node fit

| Boundary | Result of static comparison | Still required |
|---|---|---|
| GM700 control/state | Matches `N95_INTEGRATION.md`: existing Core + PostgreSQL + authenticated gateway | Actual Core source locator, version/schema pin; transactions, restart and restore receipts |
| RTX compute | Matches bounded worker role; no new orchestrator | Authenticated endpoint, measured hardware/model fit, scoped execution receipt |
| Surface Pro X | Matches browser command/review role | ARM64 client fit; reads the same Core state; no inferred local server compatibility |
| Business/research | Extraction supports the selected source-linked operational brief | Approved sample corpus and an answer-quality fixture |
| Real estate/finance | Use the same evidence schema with domain-specific units, dates and review | Defined read-only use case; no research record authorizes signing, filing, payment or trading |
| Legacy shell/roles | Preserve current names and boundaries; this pass remains Black throughout | Exact Prime Fire / Ran / Sentinel / Body gate implementation bindings are absent from the inspected source set; do not invent aliases or replace authority |
| Learning | Derived procedures remain candidates until independently verified | Replay evidence, retained baseline, measurable improvement and rollback; no automatic policy/model promotion |

### Source receipts

Inspection date: 2026-09-13 UTC. Revision pins identify the bytes reviewed; they are not approved release versions. Recent commits are a maintenance signal only. No complete vulnerability audit or transitive-license clearance is claimed.

| ID | Repository and revision | Material read | Evidence scope |
|---|---|---|---|
| S0 | [Ark95x-sAn/ark95x-unified-sovereign-stack](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/tree/a409b793f90d927b5baa30b46108c0752173ffcd) · `a409b793f90d927b5baa30b46108c0752173ffcd` | [docs/N95_INTEGRATION.md](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/a409b793f90d927b5baa30b46108c0752173ffcd/docs/N95_INTEGRATION.md), [n95_native/core_handoff.py](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/a409b793f90d927b5baa30b46108c0752173ffcd/n95_native/core_handoff.py) | Existing boundaries + code read; no execution |
| S1 | [postgres/postgres](https://github.com/postgres/postgres/tree/8c7a74c3239ce29940582643533a190721b395c0) · `8c7a74c3239ce29940582643533a190721b395c0` | [doc/src/sgml/ddl.sgml](https://github.com/postgres/postgres/blob/8c7a74c3239ce29940582643533a190721b395c0/doc/src/sgml/ddl.sgml), [COPYRIGHT](https://github.com/postgres/postgres/blob/8c7a74c3239ce29940582643533a190721b395c0/COPYRIGHT) | Constraints documentation + license read; development revision, not production pin |
| S2 | [ollama/ollama](https://github.com/ollama/ollama/tree/53fed26112817f7c55f664efb9e3f65f06cab7db) · `53fed26112817f7c55f664efb9e3f65f06cab7db` | [api/types.go](https://github.com/ollama/ollama/blob/53fed26112817f7c55f664efb9e3f65f06cab7db/api/types.go), [LICENSE](https://github.com/ollama/ollama/blob/53fed26112817f7c55f664efb9e3f65f06cab7db/LICENSE) | Request/response code + runtime license read; model terms separate |
| S3 | [yamadashy/repomix](https://github.com/yamadashy/repomix/tree/4788909d62d6f6236627a9ba464ab8f8b9ad1c94) · `4788909d62d6f6236627a9ba464ab8f8b9ad1c94` | [README.md](https://github.com/yamadashy/repomix/blob/4788909d62d6f6236627a9ba464ab8f8b9ad1c94/README.md), [LICENSE](https://github.com/yamadashy/repomix/blob/4788909d62d6f6236627a9ba464ab8f8b9ad1c94/LICENSE) | README + package.json + license read; functionality described, not tested |
| S4 | [docling-project/docling](https://github.com/docling-project/docling/tree/5ea6490ffdc57b2fd7de5cc436f2d0a22f2214d4) · `5ea6490ffdc57b2fd7de5cc436f2d0a22f2214d4` | [README.md](https://github.com/docling-project/docling/blob/5ea6490ffdc57b2fd7de5cc436f2d0a22f2214d4/README.md), [LICENSE](https://github.com/docling-project/docling/blob/5ea6490ffdc57b2fd7de5cc436f2d0a22f2214d4/LICENSE) | README + pyproject.toml + license read; functionality described, not tested |
| S5 | [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk/tree/9972c21aa42054fb1450c5fc614761ed11847ec6) · `9972c21aa42054fb1450c5fc614761ed11847ec6` | [README.md](https://github.com/modelcontextprotocol/python-sdk/blob/9972c21aa42054fb1450c5fc614761ed11847ec6/README.md), [LICENSE](https://github.com/modelcontextprotocol/python-sdk/blob/9972c21aa42054fb1450c5fc614761ed11847ec6/LICENSE) | README + pyproject.toml + license read; v2 examples, not tested |

Additional architecture material read at the baseline: [AGENTS.md](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/a409b793f90d927b5baa30b46108c0752173ffcd/AGENTS.md), [deployment blueprint](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/a409b793f90d927b5baa30b46108c0752173ffcd/JARVIS_DEPLOYMENT_BLUEPRINT.md), [registry](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/a409b793f90d927b5baa30b46108c0752173ffcd/docs/JARVIS_REGISTRY.md), [extraction protocol](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/a409b793f90d927b5baa30b46108c0752173ffcd/docs/REPO_EXTRACTION_PROTOCOL.md), [Windows audit](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/a409b793f90d927b5baa30b46108c0752173ffcd/docs/N95_NATIVE_WINDOWS.md), [device mesh](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/a409b793f90d927b5baa30b46108c0752173ffcd/core/device_mesh.py), [stack ledger](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/a409b793f90d927b5baa30b46108c0752173ffcd/docs/STACK_LEDGER.md), and [CI workflow](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/blob/a409b793f90d927b5baa30b46108c0752173ffcd/.github/workflows/ci.yml).

### Five priority reserves

Ranks order preparation value; they do not change Core's execution dependency order. Tests below are proposed acceptance criteria and have not run.

| Rank / ID | Source-derived pattern | Dependencies / license | Bounded test and pass criterion | Reason reserved |
|---|---|---|---|---|
| 1 / R01 | PostgreSQL NOT NULL + UNIQUE mission/idempotency identity and FOREIGN KEY evidence links [S1] | Existing Core schema, supported PostgreSQL release, authenticated writer; PostgreSQL license notices | In a disposable database, submit one key concurrently and retry after restart: one mission; all evidence references valid; conflicting payload rejected; rollback leaves no partial record | C1 prerequisite. Constraints alone do not guarantee exactly-once external effects |
| 2 / R02 | Digest-bound draft evidence and explicit non-authority flags [S0] | Reuse `n95_native/core_handoff.py`; actual Core source needed | Changed observation bytes fail digest validation; unchanged packet remains draft; no dispatch, physical identity or node promotion inferred | Existing component can be reused; independent physical transport verification still missing |
| 3 / R03 | Embedding request/response contract [S2] | Exact RTX endpoint, model identity/digest, scoped application authentication; Ollama MIT runtime; model license separate | Approved fixed input → one vector with exactly 768 finite numeric values for the selected Nomic Embed Text acceptance. No padding/truncation or requested output dimension to manufacture success. Independent White makes a fresh request; invalid-port attempt records failure | C3 / Mission 011 acceptance target supplied by operator; upstream API supports embeddings but does not prove this model/endpoint works |
| 4 / R04 | Source packing with explicit inclusions, provenance and optional structural compression [S3] | Observed package 1.18.0 requires Node >=22; Tree-sitter/Secretlint dependencies; MIT notices; reuse ordinary file reads first | On a small public fixture, record bytes/tokens before/after and 5 fixed code questions; 5/5 answers must cite original pinned source. Measure reduction rather than assume it. Retain full code for behavior checks | New source candidate. Compression is documented as experimental and removes implementation details; do not execute remote repo configs or treat secret scanning as a guarantee |
| 5 / R05 | Structured document export with original-source linkage [S4] | Manifest at pin names `docling-slim` 2.126.0, Python >=3.10,<4; chosen format/model extras and hardware fit; code MIT, model terms separate | Three approved synthetic documents covering text, table and scan; 10 predefined fields with correct value/unit/date and source location, zero unsupported fields; measure errors/resources | New source candidate for C4/C5. Slim/core package and OCR/model choices must be resolved; README claims are not measured extraction accuracy |

MCP [S5] remains a C05 reserve supporting R04/R05 only when a real app boundary requires it. Pinned README describes stable v2 and `from mcp.server import MCPServer`; v1 examples require migration or an explicit compatible v1 dependency. Python >=3.10 is declared. A successful tool listing or structured response alone does not prove authentication, scoped authorization or business completion.

### Rejections and blocked assumptions

| ID | Candidate or inference | Decision | Evidence / condition to reopen |
|---|---|---|---|
| X01 | Install every project in the catalogue | reject | Conflicts with existing minimum stack and C1–C6 dependency sequence; reopen one candidate for a named unmet need |
| X02 | Use a second orchestrator/vector store/SQLite spool as mission authority | reject | `N95_INTEGRATION.md` and `core_handoff.py` preserve one Core authority |
| X03 | Verify behavior from a compressed source pack alone | reject | Repomix explicitly removes implementation details; re-open original pinned files and relevant tests |
| X04 | Installed/listed/reachable/signed means working | reject | Native audit measures limited prerequisites; key possession is not physical identity; receipt is not independent verification |
| X05 | Historical ledger growth/value/deployment assertions as current evidence | reject | Ledger claims lack matching fresh execution/measurement receipts in the inspected evidence; retain as historical claims until substantiated |
| X06 | Green generic CI proves tests and container health passed | reject | Existing `ci.yml` uses `pytest ... || true` and `curl ... || echo`; a green run can hide failure. Strict native workflow is separate and no run was verified here |
| X07 | Copy an upstream README install command into desktop execution | reject | Runtime/permission/resource/release prerequisites must be resolved first; research does not admit a physical node |
| X08 | Treat old “use now” / “later” adoption labels as execution permission | reject | Current harvesting terminal decisions are reserve/reject; Core PostgreSQL is a required next dependency, not an optional later substitute |

### Admission and missing evidence

| Gate | Rule | Observed status in this pass |
|---|---|---|
| Physical desktop admission | Fresh free-space reading on the designated target volume must be >=200 GB. Record raw bytes and unit. Below threshold or unknown → STOP / RETURN; no cleanup, cleanup planning, install or optimization on that target | UNKNOWN; no desktop inspected. Cloud source research/documentation is not desktop admission |
| Node trust | discovered → authenticated → healthy → capability-tested → independently verified | No new device state established |
| Source provenance | owner/repo + exact revision + file locator + observed date + license + claim/evidence distinction | Six source records populated above; transitive dependency review incomplete |
| Existing Core | Locate authoritative implementation and schema before proposing a replacement | Missing from inspected checkout; adapter references external `src/n95_ops/engine.py` |
| Role bindings | Preserve Black review / Orange execution / independent White / Green recording of accepted learning | No agent implementation or operational authority created by role labels |
| API acceptance | `/api/tags` proves only a listing; actual model call and fresh independent output check required | NOT_RUN |
| Writeback | Append under this page, retain prior review history, use guarded commit, log changed files | Verify exact persisted content before reporting saved |
| Weekly preparation | Monday morning, America/Chicago; source/read/fit/delta pass; max five worthwhile reserves; retain reject reasons | ENABLED per scheduler receipt 2026-09-13; first scheduled 2026-09-14, approximately 08:00 Central; no run recorded |

### Compact extraction record

```json
{
  "schema": "n95.harvest.v1",
  "mission_id": "N95-HARVEST-PREP",
  "record_id": "Rxx",
  "role": "Black",
  "category_id": "Cxx",
  "source": {
    "repository": "owner/repo",
    "revision": null,
    "path": null,
    "locator": null,
    "observed_at_utc": null,
    "license": null,
    "evidence_kind": "documentation_or_code_read"
  },
  "claim": null,
  "observed_evidence": null,
  "pattern": {"input": null, "transform": null, "output": null},
  "architecture": {"existing_module": null, "node_role": null, "core_dependency": null},
  "dependencies": [],
  "unknowns": [],
  "data_and_permission_scope": null,
  "first_test": {"fixture": null, "pass_criterion": null, "result": "NOT_RUN"},
  "decision": "reserve",
  "reason": null,
  "reopen_condition": null,
  "white_verification_receipt": null,
  "runtime_verified": false
}
```

Required nulls are unresolved evidence, never successful checks. A reserve may retain explicit blockers; a reject must state why and what new evidence could reopen it. Research provenance can be logged immediately; verified learning requires White acceptance.

<!-- N95-HARVEST-2026-09-13:END -->
