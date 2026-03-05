# ARK95X Unified Sovereign Stack

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
