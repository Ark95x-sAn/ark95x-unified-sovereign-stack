# ARK95X 300-Task Orchestration Development Plan

> Repository: `Ark95x-sAn/ark95x-unified-sovereign-stack` &nbsp;|&nbsp; Branch: `main`
> Focus: Forward development + scaling on top of the existing production stack.
> Companion artifact: `ARK95X_300_Task_Orchestration.xlsx` (full task table, summary pivots, lookups).

## Operating Loop (from AGENTS.md)
`Observe -> Decode -> Route -> Build -> Verify -> Remember -> Scale`

## How the 9-Brain Council consumes this plan
1. **Observe** - Filter tasks by Phase, Module/Path, Status, and Priority.
2. **Decode** - Router Brain converts each row into a canonical command + acceptance criteria.
3. **Route** - Handoff Router assigns the task to the Owning Agent / crew.
4. **Build** - Owning agent implements against the Module/Path.
5. **Verify** - Acceptance criteria + tests/CI gate the task to Done.
6. **Remember** - Result written to memory/victory log.
7. **Scale** - Completed primitives promoted into reusable workflows.

## Guardrails
- Trading work stays in **research / paper / simulation mode** (repo rule: no live trading execution).
- Security/sovereignty tasks preserve existing hardening (`shell=True` / `verify=False` removed).

## Phases (10 x ~30 tasks = 300)
| # | Phase | Primary Modules |
|---|-------|-----------------|
| 1 | Orchestration Core & 9-Brain Router | `core/`, `config/` |
| 2 | Agent Crews & Flame Agents | `crews/`, `flame/` |
| 3 | Intelligence / OSINT Pipeline | `intelligence/` |
| 4 | Trading Engine (sim only) | `trading/` |
| 5 | Infra / Deploy / Containers | `infra/`, `deploy/` |
| 6 | n8n & Workflow Automation | `n8n/`, `workflows/` |
| 7 | Scaling & Performance | `scaling/`, `performance/` |
| 8 | Security / Sovereignty / Audit | `sovereignty/`, `audit-agent/`, `protocol/` |
| 9 | Testing / CI-CD / Observability | `tests/`, `.github/workflows/` |
| 10 | Integration & Iowa AI GTM tie-in | `integrations/`, `command/`, `netx/` |

## Task ID convention
`P#-T##` (e.g. `P3-T14` = Phase 3, Task 14). Full descriptions, owning agents, dependencies, priority (P0/P1/P2), effort (S/M/L), status, and acceptance criteria live in the companion workbook and the linked GitHub Project board.
