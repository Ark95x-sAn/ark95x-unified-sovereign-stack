# ARK95X Unified Sovereign Stack

## Work-brief evaluation candidate — 2026-09-06

The first runnable $100 service candidate is a [local work brief](n95_workflow/README.md)
from explicit text-note tasks. It includes source references, conflict reporting,
repeat-output verification and a [Windows handoff](docs/N95_WORK_BRIEF_RUNBOOK.md).
It performs deterministic extraction with no model inference.

The [offer](docs/N95_WORK_BRIEF_OFFER.md) remains on hold for measured customer value.
Use the [nine-evaluator protocol](docs/N95_NINE_EVALUATOR_PROTOCOL.md) and
[value observation template](docs/N95_VALUE_OBSERVATIONS_TEMPLATE.json) to challenge
it. Passing software tests is not proof that a customer gets more than $100 of value.

## Verified integration increment — 2026-09-06

The new [native receipt bridge](n95_native/README.md) adds signed technical
observations, expiration/replay checks, a bounded polling loop and a draft handoff
for the existing Network-95 Core schema. It does not establish physical device
deployment. The legacy device mesh now preserves context until real delivery and
does not seed devices as online. Treat the broader service claims below as the
historical project description; live services still need target-specific proof.

- [25 GitHub candidates and license review](docs/N95_TOP25_GITHUB.md)
- [Three installation offers and the 9×9 capability map](docs/N95_SERVICE_PRODUCTS.md)
- [Integration boundaries and next acceptance gates](docs/N95_INTEGRATION.md)
- [Windows preflight commands](docs/N95_NATIVE_WINDOWS.md)

Run the isolated demonstration with Python 3.11+ and a fresh private state folder
outside this checkout:

```sh
python -m n95_native demo --state /tmp/n95-native-demo
```

This sends three synthetic identities through actual loopback HTTP and records
their signed receipts. It is a one-host test, not proof of a three-device network.

[![CI](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/) [![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

> **All repositories. One united front. Total sovereign integration.**

## What Is This?

ARK95X is a **complete self-hosted AI operations stack** — not a framework, not a library, but a full sovereign deployment combining agent orchestration, intelligence gathering, trading, and infrastructure into one unified system.

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
|-- n8n/                     # Sovereign n8n Fork
|
|-- main.py                  # Unified entry point
|-- docker-compose.yml       # Full stack deploy
|-- Dockerfile               # Production container
|-- requirements.txt         # Dependencies
```

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

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Stack status |
| `/health` | GET | Service health check |
| `/api/query` | POST | Query AI models |
| `/api/models` | GET | List available models |
| `/api/services` | GET | Service status |
| `/docs` | GET | Interactive API docs |

## License

MIT - Network-95 LLC | Nordskog Properties LLC

---

**ARK95X | Sovereign Architect | Winnebago County, Iowa**
