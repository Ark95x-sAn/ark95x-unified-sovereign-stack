# ARK95X Unified Sovereign Stack — Command Center

> **FURY MODE ACTIVE | MULTIPLEX ENABLED | UNIFIED CREW DEPLOYED**

---

## Overview

The ARK95X Command Center is a multi-agent orchestration system built on a CrewAI-inspired architecture. Three sovereign AI agents operate as a unified crew, sharing memory, routing tasks by category, and running in fury-mode multiplexed streams.

---

## Agents

| Agent | Role | Key Tools | Key Skills |
|-------|------|-----------|------------|
| **Manus** | Research & Intel | web_search, doc_reader, data_extractor, case_analyzer | litigation_intel, financial_analysis, pattern_recognition |
| **ZenCode** | Architecture & Code | code_gen, refactor, deploy_engine, api_designer | python, typescript, systems_design, docker, github_actions |
| **VibeCoder** | UI/UX & Creative | ui_builder, dashboard_gen, creative_engine | react, tailwind, dashboard_architecture, real_time_feed |
| **Conductor** | Orchestrator | — | fury_mode, multiplex, task_dispatch |

---

## File Structure

```
command/
  agents/
    manus_agent.py        # Research & Intel agent
    zencode_agent.py      # Architecture & Code agent
    vibecoder_agent.py    # UI/UX & Creative agent
  unified_crew.py         # CrewAI-style orchestrator + shared memory
  dispatcher.py           # Task router by category + priority
  run_crew.py             # Master launcher CLI
  protocol_router.py      # A2A/M2M protocol routing
  command_center_api.py   # FastAPI command center API
  workload_config.py      # Agent workload assignments
  __init__.py             # Package exports
  README_CREW.md          # This file
```

---

## Quick Start

```bash
# Full fury mission (all 12 tasks, 3x multiplex)
python run_crew.py --fury --mode full

# Quick mission (3 priority tasks)
python run_crew.py --fury --mode quick

# Programmatic usage
from dispatcher import get_dispatcher, DispatchRequest

d = get_dispatcher(fury=True)
result = d.route(DispatchRequest(
    description="Analyze Reliance Bank case docs",
    category="litigation",
    priority=9
))
```

---

## Task Routing

The dispatcher automatically routes tasks to the right agent:

| Category | Agent |
|----------|-------|
| research, litigation, property, financial, data, extract, analyze | Manus |
| code, build, api, deploy, schema, database, backend, refactor, test | ZenCode |
| ui, ux, dashboard, design, frontend, visual, creative | VibeCoder |

---

## Fury Mode

When `fury=True`:
- All tasks get the `[FURY]` prefix tag
- Conductor multiplexes 3 tasks per batch simultaneously
- Shared memory accumulates compound context across all agents
- Priority queue sorts tasks 9→6 before dispatch

---

## Shared Memory

All agents read and write to a single `SharedMemory` bus:
- Manus writes research findings → ZenCode reads for API design context
- ZenCode writes schemas → VibeCoder reads for dashboard structure
- Conductor tracks fury state + handoff counts

---

## Workload Assignment

| Domain | Owner | Priority |
|--------|-------|----------|
| Litigation & case intel | Manus | P1 |
| Property & financial data | Manus | P1 |
| Command center API | ZenCode | P1 |
| Protocol routing | ZenCode | P1 |
| Command center UI | VibeCoder | P1 |
| Agent status dashboard | VibeCoder | P2 |

---

## ARK95X Sovereign Stack

Built by **Network-95 LLC** — Unified. Sovereign. Unstoppable.
