# Network-95: 25 GitHub candidates across capability classes

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
