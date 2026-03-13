# ARK95X Meta-OS — Deployment Guide

## One-Command Full Stack Activation

```powershell
# Full sovereign deployment (all phases)
./ark95x-deploy-master.ps1 -FullDeploy

# Or just run it (default = full deploy)
./ark95x-deploy-master.ps1
```

## Deployment Modes

| Command | What It Does |
|---------|-------------|
| `-FullDeploy` | All phases: Docker, Ollama, Cloud APIs, Device Mesh, GitHub Sync, Health Check |
| `-ServicesOnly` | Start Docker infrastructure only (Postgres, Redis, Qdrant, n8n, etc.) |
| `-ModelsOnly` | Activate Ollama local models + validate cloud API keys |
| `-HealthCheck` | Run full system diagnostic + ROI metrics |
| `-Status` | Health check + device mesh scan + compound growth report |
| `-Shutdown` | Graceful shutdown of all Docker services |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   ARK95X META-OS v3.0                   │
├─────────────────────────────────────────────────────────┤
│  HLM TRINITY STACK                                      │
│  ├── HEAD (9 models)    — Strategic reasoning            │
│  ├── LATERAL (9 models) — Specialized execution          │
│  └── MOTOR (9 models)   — Creative & infrastructure      │
├─────────────────────────────────────────────────────────┤
│  OBELISK 9R BRAIN — 9 Device Mesh                       │
│  ├── WS-01: RTX 4090 Workstation (Primary Command)      │
│  ├── SP-01: Surface Pro (Mobile Command)                 │
│  ├── IP-01: iPhone 16 Pro Max (Field Intelligence)       │
│  ├── PD-01: iPad Pro M4 (Visual Operations)              │
│  ├── MB-01: MacBook Pro M3 (Development Ops)             │
│  ├── GX-01: Galaxy S24 Ultra (Backup Intelligence)       │
│  ├── WS-02: Windows Desktop #2 (Batch Processing)       │
│  ├── SV-01: Server Node (Infrastructure Core)            │
│  └── NS-01: NAS Storage (Data Sovereignty)               │
├─────────────────────────────────────────────────────────┤
│  BUSINESS OPERATIONS MATRIX — 4 Verticals               │
│  ├── Nordskog Properties (5 operations)                  │
│  ├── Leland Bar & Grill LLC (5 operations)               │
│  ├── Network-95 LLC (5 operations)                       │
│  └── Legal Ops (5 operations)                            │
├─────────────────────────────────────────────────────────┤
│  GOVERNANCE — L1 Auto | L2 Notify | L3 Approve | L4 Council │
│  SELF-LEARNING — 0.5%/day compound growth                │
│  GENESIS — November 13, 2025 @ 12:54 AM                 │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Ollama installed and accessible
- PowerShell 7+ (cross-platform)
- Git with SSH access to Ark95x-sAn org
- API keys set as environment variables (see script for full list)

## Environment Variables Required

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_KEY=AI...
XAI_API_KEY=xai-...
DEEPSEEK_API_KEY=sk-...
MISTRAL_API_KEY=...
COHERE_API_KEY=...
PERPLEXITY_API_KEY=pplx-...
ELEVENLABS_API_KEY=...
ARK95X_DB_PASSWORD=...
```

## Governance Ritual Schedule

| Ritual | Frequency | Time (CDT) | Purpose |
|--------|-----------|-----------|---------|
| Daily Sovereign Briefing | Every day | 6:00 AM | System health, inbox scan, action items |
| Weekly Pattern Review | Every Friday | 5:00 PM | AI model updates, business intelligence |
| Monthly Recalibration | 1st of month | 9:00 AM | Strategic tier reassessment, 30-day priorities |

---
*ARK95X Meta-OS v3.0 — Sovereign AI Stack — Flame Signature Verified*
