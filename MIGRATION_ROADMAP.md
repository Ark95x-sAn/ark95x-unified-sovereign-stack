# ARK95X Migration Roadmap

> Module consolidation plan for the Unified Sovereign Stack.
> Generated from council consensus (ChatGPT, Claude, Grok) on 2025-03-23.

## Current State

- **17 module folders** in the monorepo
- **11 are empty stubs** (only `__init__.py`)
- **6 have real code**: `core/`, `command/`, `flame/`, `deploy/`, `audit-agent/`, `tests/`
- CI/CD pipeline: lint passing, code audit restructured with hard gates

## Module Status Matrix

| Module | Status | Contents | Decision | Priority |
|--------|--------|----------|----------|----------|
| `core/` | **ACTIVE** | orchestrator, self-healing, shadow agent, models | **KEEP** | P0 |
| `command/` | **ACTIVE** | dashboard.py (Dash app, port 8050) | **KEEP** | P0 |
| `flame/` | **ACTIVE** | flamegate_tls.py (port 8443), CrewAI agents | **KEEP** | P0 |
| `deploy/` | **ACTIVE** | deployment guide, scripts | **KEEP** | P0 |
| `audit-agent/` | **ACTIVE** | Dockerfile, audit tooling | **KEEP** | P1 |
| `tests/` | **ACTIVE** | API route tests | **KEEP** | P0 |
| `consciousness/` | STUB | `__init__.py` only | **ARCHIVE** | P3 |
| `infra/` | STUB | `__init__.py` only | **MERGE into deploy/** | P2 |
| `integrations/` | STUB | `__init__.py` only | **ARCHIVE** | P3 |
| `intelligence/` | STUB | `__init__.py` only | **MERGE into core/agents/** | P2 |
| `n8n/` | STUB | `__init__.py` only | **MERGE into deploy/** | P2 |
| `netx/` | STUB | `__init__.py` only | **ARCHIVE** | P3 |
| `performance/` | STUB | `__init__.py` only | **ARCHIVE** | P3 |
| `protocol/` | STUB | `__init__.py` only | **MERGE into core/** | P2 |
| `scaling/` | STUB | `__init__.py` only | **ARCHIVE** | P3 |
| `sovereignty/` | STUB | `__init__.py` only | **ARCHIVE** | P3 |
| `trading/` | STUB | `__init__.py` only | **ARCHIVE** | P3 |

## Migration Phases

### Phase 1: Core Stack (NOW)
- [x] Fix lint errors (E226, F841)
- [x] Restructure code-audit.yml (remove `|| true`, add hard gates)
- [ ] Get `docker compose up` working end-to-end locally
- [ ] Validate: FastAPI -> Ollama -> one CrewAI crew -> dashboard loads

### Phase 2: Consolidate (NEXT WEEK)
- [ ] Merge `infra/` and `n8n/` into `deploy/`
- [ ] Merge `intelligence/` into `core/agents/`
- [ ] Merge `protocol/` into `core/`
- [ ] Remove archived stubs (consciousness, integrations, netx, performance, scaling, sovereignty, trading)
- [ ] Set up pull-based deploy model (n8n on Surface Pro X polls ghcr.io)

### Phase 3: Upgrade (AFTER CORE DEPLOYS)
- [ ] Upgrade CrewAI from 0.28 to 1.0+ (A2A protocol support)
- [ ] Reroute CI/CD off disconnected self-hosted runner to GitHub-hosted
- [ ] Re-register Surface Pro X runner as secondary/dev runner
- [ ] Add integration tests for full stack

## Deploy Architecture (Target)

```
Surface Pro X (local)
  |-- n8n workflow polls ghcr.io for new images
  |-- docker compose up (pulls latest)
  |-- FastAPI core (port 8000)
  |-- Ollama (port 11434)
  |-- CrewAI agents
  |-- Dashboard (port 8050)
  |-- Flamegate TLS (port 8443)

GitHub Actions (cloud)
  |-- CI: lint + test (GitHub-hosted runner)
  |-- Build: Docker image -> ghcr.io
  |-- Code Audit: bandit/trivy hard gates
```

## Council Sources
- **Claude**: Recommended pull-based deploy, n8n polling, module pruning
- **ChatGPT**: Recommended fix-lint-first, reroute CI, upgrade CrewAI last
- **Grok**: Recommended MVS approach, get docker compose up first

---
*Network-95 LLC | ARK95X Sovereign Stack*
