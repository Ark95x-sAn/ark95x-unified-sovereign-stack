# ARK95X Jarvis Deployment Blueprint

## Mission
Build a local-first Jarvis command stack that turns rough operator intent into classified, verified, logged, and repeatable execution.

## Seven-Breath Cycle

1. **Observe** — capture repo/tool/video/input.
2. **Decode** — translate the input into the Jarvis architecture.
3. **Route** — assign to the correct layer or specialist agent.
4. **Build** — extract install steps, config, ports, and first run command.
5. **Verify** — check maintenance, license, Docker support, local/offline capability, security risk, and integration fit.
6. **Remember** — store into the Jarvis Registry.
7. **Scale** — promote only if it improves the command center and remains auditable.

## Core Layers

| Layer | Purpose | Initial Components |
|---|---|---|
| Command Center | Operator UI and status | FastAPI, simple dashboard |
| Inference | Local model serving | Ollama |
| State | System record | PostgreSQL |
| Memory | Searchable recall | pgvector |
| Queue | Workflow/cache | Redis |
| Automation | Repeatable actions | n8n |
| Tools | Action interfaces | MCP servers |
| Orchestration | Agent routing | LangGraph |
| Verification | Safety and truth checks | approval gates, audit log |

## Master Commands

- OBSERVE
- ANALYZE
- PLAN
- BUILD
- RESEARCH
- VERIFY
- REMEMBER
- REPORT
- AUTOMATE
- EXECUTE

## Safety Gates

| Risk | Meaning | Rule |
|---|---|---|
| Green | read-only | may run automatically |
| Yellow | creates files/drafts/configs | log and review |
| Red | sends, deletes, pays, trades, publishes, signs, or changes legal/financial/security status | explicit human approval required |

## Minimum Deployment

```bash
cp .env.example .env
docker compose up -d
```

Services:

- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Ollama: `localhost:11434`
- n8n: `localhost:5678`
- Jarvis API: `localhost:8765`

## First Verification

```bash
curl http://localhost:8765/health
curl http://localhost:11434/api/tags
```

Expected result: API health returns online, Ollama responds, and the stack can log an operator command into PostgreSQL.

## Non-Negotiables

- No credential exposure.
- No destructive actions without approval.
- No live trading execution.
- No unsafe broad-permission browser automation.
- Every action must log actor, input, tool, output, timestamp, and risk score.
