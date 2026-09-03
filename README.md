# ARK95X Unified Sovereign Stack

[![CI](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/) [![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

> **All repositories. One united front. Total sovereign integration.**

## What Is This?

ARK95X is a **complete self-hosted AI operations stack** — not a framework, not a library, but a full sovereign deployment combining agent orchestration, intelligence gathering, trading, and infrastructure into one unified system.

The flagship system currently built and live-tested on top of that stack is the **ARK95X Command Ledger**: a real-money pipeline (NetX signal → risk calculator → passive income ledger → cockpit) gated end-to-end by a single control-plane authority layer, backed by the live docker-compose data stack below. See [Command Ledger](#ark95x-command-ledger) for the full data flow, authority gate, and cockpit API.

### Why ARK95X vs Alternatives?

| Feature | ARK95X | LangChain | CrewAI | AutoGen |
|---|---|---|---|---|
| Self-hosted sovereign stack | **Yes** | No | No | No |
| Built-in n8n workflows | **Yes** | No | No | No |
| Trading + OSINT + Agents | **Yes** | No | No | No |
| Docker one-command deploy | **Yes** | No | Partial | No |
| Local-first (no cloud) | **Yes** | No | Yes | No |
| Monitoring (Prometheus+Grafana) | **Yes** | No | No | No |
| Multi-model support | **Yes** | Yes | Yes | Yes |

## Services (docker-compose up)

| Service | Port | Description |
|---|---|---|
| ARK95X Core API | `:8000` | FastAPI + `/docs` |
| n8n Workflows | `:5678` | Automation engine |
| Grafana | `:3000` | Monitoring dashboard |
| Prometheus | `:9090` | Metrics collection |
| SearXNG | `:8080` | Private search |
| Qdrant | `:6333` | Vector store |
| PostgreSQL | `:5432` | Primary database |
| MongoDB | `:27017` | Document store |
| Redis | `:6379` | Cache + queue |

## Quick Start

```bash
git clone https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack.git
cd ark95x-unified-sovereign-stack
cp .env.example .env
docker-compose up -d
```

## ARK95X Command Ledger

The Command Ledger is a real-money pipeline that turns a trading signal into a
recorded, human-approved ledger entry, broadcast live to a cockpit UI. It is
built fresh in this repo (`netx/`, `ledger/`, `passive_income_engine.py`,
`cockpit/`, `control_plane/`, `router/`) — it does not modify or depend on
any of the other 17-repo-vision directories below. Every module, test count,
and "done" claim here is tracked in `ARK-STATE.json`, the single source of
truth for this build; `HANDOFF.md` documents how a fresh model session
resumes it.

### Data flow

```
NetX signal  --->  risk calculator  --->  command ledger  --->  cockpit
(netx/signal_   (netx/risk_          (ledger/command_      (cockpit/app.py
 engine.py)      calculator.py)       ledger.py +           FastAPI +
                                       passive_income_       WebSocket, :8080)
                                       engine.py)
```

1. **`netx/signal_engine.py`** — `Signal` dataclass + `SignalBus` pub/sub;
   ingests a trade signal (symbol, side, entry/stop price) via
   `POST /netx/webhook`.
2. **`netx/risk_calculator.py`** — sizes the position:
   `capital * risk_pct/100 / stop_distance`.
3. **`ledger/command_ledger.py` + `passive_income_engine.py`** — records the
   risk-sized order as a real ledger entry, tracks running balance/ROI, and
   persists it (JSON file by default, or a real Postgres backend — see
   [Live data stack](#live-data-stack) below). `passive_income_engine.py`
   also implements a lossless `snapshot()`/`restore()` round trip.
4. **`cockpit/app.py`** — broadcasts the resulting `telemetry_event` (ROI
   ledger, leverage meter) to every connected `/ws/cockpit` WebSocket
   client, computed from the real ledger state, not decorative numbers.

Shared message shapes for all four steps live in
`contracts/ark-state.schema.json`.

### Authority gate (single control plane)

Financial and other consequential actions do not execute on their own —
this is real, tested behavior, not an aspiration. `control_plane/control_plane.py`
registers the 8 ARK95X roles (`arc_x`, `codex_security`, `memory_cortex`,
`monitoring`, `github`, `n8n`, `devices`, `business_ops`) under one
authority/reporting contract with `ARK-STATE.json` as the authoritative
state path. No agent can override the plane or self-approve its own
actions, and any action classified as `account_change`, `destructive`,
`deployment`, `financial`, `legal`, `public`, `security_sensitive`, or
`system_mutation` is routed to a human-approval queue instead of running
immediately.

Concretely for the ledger: **closing a position is a financial action.**
`POST /fills` queues the close request — the ledger's realized P&L stays
untouched — and money only moves once a human calls
`POST /approve/{request_id}`, at which point `CommandLedger` executes the
close and reports the real outcome back to the control plane. This was
proved live end-to-end (`scripts/prove_the_network.py`, 15/15 checks): a
real signal and fill were posted, `/roi` stayed at $0 P&L while the close
sat pending, approval released it, `/roi` then showed the real P&L, and
`/control-plane` showed `business_ops`'s report matching the actual ledger
entry. Setting `CONTROL_PLANE_ENABLED=false` restores immediate execution
for local testing.

The remaining 7 roles are wired to their own real integration points too
(not a generic shim each) — e.g. `codex_security` runs a real secret-pattern
scan over `git diff` before any release, `github_adapter` gates a real
`git push` behind human approval, and `router/failover.py` reports every
dispatch decision through the plane as `arc_x`'s own `routing` authority
scope. See `docs/control-plane-pass-1.md` and the
`control_plane_remaining_adapters` entry in `ARK-STATE.json` for the full
per-role breakdown.

### Cockpit API (`cockpit/app.py`, `:8080`)

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Basic liveness check |
| `/monitoring/health` | GET | Real ledger-reachability + TCP probes of the data stack, reported through the control plane |
| `/roi` | GET | Live ROI ledger + leverage meter snapshot, computed from real ledger state |
| `/netx/webhook` | POST | Ingests a trading signal; runs the full signal → risk → telemetry chain |
| `/fills` | POST | Reports a closed position — a financial action, queued for human approval by default |
| `/pending` | GET | Actions currently queued for human approval |
| `/approve/{request_id}` | POST | Approves a queued action; only now does money move and the ledger get written |
| `/control-plane` | GET | Read-only snapshot of the authority/reporting state — registered roles, scopes, pending queue |
| `/failover/dispatch` | POST | Runs `router/failover.py`'s `dispatch_next()` over HTTP, so n8n (or anything else) can trigger the failover cascade without needing Python or git in its own runtime |
| `/ws/cockpit` | WebSocket | Live telemetry stream; a connecting client is sent the current ROI snapshot immediately, then future updates as they happen |

### Live data stack

```bash
docker compose up -d postgres mongodb redis qdrant n8n
```

This brings up the infrastructure the Command Ledger actually runs against,
live-verified (not just "container running") on 2026-09-03:

- **`postgres`** — `passive_income_engine.py` can persist ledger state here
  instead of a JSON file (set `POSTGRES_URL`); proved durable across a
  simulated process restart and independently queryable with plain SQL.
- **`n8n`** — hosts `workflows/ark_failover_dispatch_v1.json`, the scheduled
  workflow that calls the cockpit's `/failover/dispatch` route on a
  heartbeat. Live-tested against a real n8n instance (see
  [Known limitations](#known-limitations) for what's still untested in it).
- **`mongodb`**, **`redis`**, **`qdrant`** — brought up as part of the same
  stack and probed by `/monitoring/health`, but the Command Ledger pipeline
  itself does not yet write to them; they back other parts of the wider
  ARK95X stack (see [Services](#services-docker-compose-up) below).

### Known limitations

These are the honest gaps as of this writing (see
`ARK-STATE.json.known_gaps` for the authoritative list):

- No real broker/exchange or production NetX signal source is wired behind
  `/netx/webhook` yet — signals are posted manually or by n8n for testing
  (`T5.3`, still pending).
- In `workflows/ark_failover_dispatch_v1.json`, only the dispatch path
  (`Failover_Heartbeat → Run_Failover_Router → Check_Dispatch_Status`) is
  live-tested. The `Commit_Genome_Update` node (git add/commit/push) needs a
  host with real git + repo access, and the Discord/Google Sheets
  notification nodes need real credentials — neither has been exercised
  live.
- `cockpit/app.py` is a new build in this repo, not a patch to the
  `omnikernel-orchestrator` repo, which has no FastAPI/`:8080`/WebSocket
  cockpit of its own.

## Architecture

```
ark95x-unified-sovereign-stack/
|
|-- core/                    # HLM-9 Omnikernel Orchestrator
|   |-- orchestrator.py      # Adaptive agent scheduling
|   |-- self_healing.py      # Circuit breakers + auto-recovery
|   |-- pipeline_manager.py  # DAG task pipelines
|   |-- telemetry.py         # Metrics + alerting
|   |-- config.py            # Centralized config
|   |-- models/              # AI model integration
|   |-- agents/              # Agent implementations
|
|-- flame/                   # Flame OS - 32 Agent Definitions
|   |-- flame_core.py        # CrewAI agent definitions
|   |-- orchestrator.py      # Meta-orchestrator
|   |-- nordskog_model_router.py
|
|-- intelligence/            # OSINT Intelligence Gathering
|   |-- browserbase/         # Browserbase + Stagehand
|   |-- scoring/             # AI-powered scoring
|   |-- sources/             # GitHub, HN, ArXiv, Reddit
|
|-- trading/                 # Autonomous Trading Engine
|   |-- openevolve/          # LLM strategy discovery
|   |-- flametrace/          # Capital allocation
|   |-- genetics/            # MAP-Elites algorithms
|
|-- command/                 # Central Command Ops
|-- consciousness/           # Distributed Cloud Infra
|-- sovereignty/             # Iowa AI Toolkit
|-- performance/             # Human Performance AI
|-- protocol/                # Multi-AI Bridge
|-- infra/                   # Terraform + K8s
|-- n8n/                     # n8n dispatch adapter (control plane)
|
|-- netx/                    # Command Ledger: signal engine + risk calculator
|-- ledger/                  # Command Ledger: command_ledger.py, telemetry events
|-- passive_income_engine.py # Command Ledger: real ledger entries, ROI, snapshot/restore
|-- cockpit/                 # Command Ledger: FastAPI + WebSocket cockpit (:8080)
|-- control_plane/           # Single-authority contract over 8 ARK95X roles
|-- router/                  # Credit-proof failover router (Claude/Ollama/Groq/Gemini)
|-- contracts/               # Shared message schemas for the ledger pipeline
|-- monitoring/, memory_cortex/, codex_security/, devices/, github_adapter/
|                             # Control-plane adapters for the remaining roles
|-- workflows/               # n8n workflow definitions (failover dispatch, etc.)
|-- scripts/prove_the_network.py  # Re-runnable end-to-end proof script
|
|-- main.py                  # Unified entry point
|-- docker-compose.yml       # Full stack deploy
|-- Dockerfile               # Production container
|-- requirements.txt         # Dependencies
```

See [ARK95X Command Ledger](#ark95x-command-ledger) above for what the
second block of directories does and how it fits together.

## System Stack

| Layer | Technology |
|---|---|
| **Orchestration** | CrewAI, AutoGen, LangGraph, n8n |
| **AI Models** | Ollama, OpenAI, DeepSeek, Llama3, Mistral |
| **Vector Store** | Qdrant, LanceDB |
| **Database** | PostgreSQL 16, MongoDB 7 |
| **Cache** | Redis 7 |
| **Search** | SearXNG, Browserbase |
| **Monitoring** | Prometheus, Grafana |
| **Infrastructure** | Docker, Kubernetes, Terraform |

## Core API Endpoints (`main.py`, `:8000`)

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Stack status |
| `/health` | GET | Service health check |
| `/api/query` | POST | Query AI models |
| `/api/models` | GET | List available models |
| `/api/services` | GET | Service status |
| `/docs` | GET | Interactive API docs |

For the Command Ledger's own API, see [Cockpit API](#cockpit-api-cockpitapppy-8080) above.

## License

MIT - Network-95 LLC | Nordskog Properties LLC

---

**ARK95X | Sovereign Architect | Winnebago County, Iowa**
