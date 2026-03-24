# ARK95X — CREW OPS OPTIMIZATION
# Deep Setup, Research Protocols & Best Operational Deployment
**Updated: March 24, 2026 | ARK95X Sovereign Stack**

---

## PART 1: CREW ARCHITECTURE — WHO DOES WHAT

```
┌──────────────────────────────────────────────────┐
│     ARK95X CONDUCTOR (Orchestrator)                  │
│     - Routes tasks by type + priority                │
│     - Engages fury mode                              │
│     - Multiplexes 3 tasks simultaneously             │
└──────────────────────────────────────────────────┘
           ↓              ↓              ↓
   ┌─────────┐   ┌─────────┐   ┌───────────┐
   │  MANUS   │   │ ZENCODE  │   │ VIBECODER  │
   │Research │   │  Code &  │   │  UI/UX &   │
   │& Intel  │   │  Build   │   │ Creative  │
   └─────────┘   └─────────┘   └───────────┘
           ↓              ↓              ↓
        SharedMemory Bus (compound context)
```

---

## PART 2: OPTIMAL TASK ASSIGNMENT

| Task Type | Agent | Why |
|-----------|-------|-----|
| Financial research, pattern analysis | Manus | Deep research pipeline |
| Legal intel, court dockets, doc review | Manus | Case analyzer tool |
| Property data, utility analysis | Manus | Data extractor |
| API builds, routing, backend | ZenCode | Code gen + deploy engine |
| Database schemas, n8n workflows | ZenCode | Schema builder |
| GitHub commits, automation scripts | ZenCode | GitHub Actions integration |
| Dashboard design, command center UI | VibeCoder | Dashboard gen |
| Real-time status feeds | VibeCoder | Real-time feed tool |
| Visual reports, charts, summaries | VibeCoder | Data visualization |

---

## PART 3: RESEARCH PROTOCOLS — BEST PRACTICES

### Pre-Mission Checklist (before every session)
```
[ ] 1. Read MEMORY_ENHANCEMENT.md — know current state
[ ] 2. Read DATA_LOGS.md — confirm latest numbers
[ ] 3. Load new data files (bank statements, Square exports, utility bills)
[ ] 4. Set clear objective: "Today we are solving X"
[ ] 5. Assign to correct agent: research=Manus, build=ZenCode, visualize=VibeCoder
[ ] 6. Enable fury mode for multi-priority sessions
[ ] 7. Set multiplex to 3 for parallel task streams
```

### Research Quality Tiers

| Tier | Input Quality | Output Quality | Time |
|------|--------------|----------------|------|
| T1 (Best) | Raw source docs (PDFs, CSVs, statements) | Exact figures, cited | Fast |
| T2 (Good) | Structured prompts with known data | High accuracy | Medium |
| T3 (OK) | Open-ended prompts | Estimates only | Slow |
| T4 (Poor) | "Analyze everything" with no data | Generic output | Very slow |

**Always target T1 or T2. Never operate at T4.**

---

## PART 4: DEPLOYMENT PROTOCOLS

### Standard Deployment (Single Entity)
```python
from command.dispatcher import get_dispatcher, DispatchRequest

d = get_dispatcher(fury=True)
d.route(DispatchRequest(
    description="Analyze LBG Farmers Trust *9552 for Q4 2025",
    category="financial",
    priority=9
))
```

### Batch Deployment (Multi-Entity, Fury Mode)
```python
from command.run_crew import run
run(fury=True, mode="full")
```

### Specific Agent Direct Call
```python
from command.unified_crew import get_crew, AgentRole, CrewTask

crew = get_crew(fury=True)
task = CrewTask("LBG-001", "Build P&L from Square + bank data",
                AgentRole.ZENCODE, priority=9)
result = crew.conductor.dispatch(task)
```

---

## PART 5: WORKLOAD OPTIMIZATION

### The 3-Lane Highway (Multiplex Model)
```
Lane 1 (MANUS):     Research + Intel + Data Extraction
Lane 2 (ZENCODE):   Build + Structure + Automate
Lane 3 (VIBECODER): Visualize + Present + Dashboard

All 3 lanes run simultaneously.
Conductor feeds tasks. SharedMemory connects outputs.
Result: 3x throughput vs single-agent sequential.
```

### Priority Queue (Process in this order)
1. P1 — Active legal / bank threats (EQCV018537, Farmers Trust review)
2. P2 — Utility disconnection risks (BHE, Winnebago Coop)
3. P3 — Cash flow / NSF resolution
4. P4 — Revenue optimization
5. P5 — System improvements / documentation

---

## PART 6: COMPOUND LEARNING CONFIG

### How to Build Compounding Intelligence

```
Session 1: Establish baseline (Square data, bank statements)
Session 2: Add utility data. Cross-reference with bank.
Session 3: Add legal data. Cross-reference with cash flow.
Session 4: Add CPA compiled data. Compare to estimates.
Session N: Each session adds to previous. Never start over.
```

### SharedMemory Keys to Always Populate
```python
memory.write("manus",     "lbg_revenue_2025",   162216)
memory.write("manus",     "bhe_balance",          5667)
memory.write("manus",     "farmers_trust_nsf",   -4983.35)
memory.write("zencode",   "api_version",          "v2.1")
memory.write("vibecoder", "dashboard_status",     "live")
memory.write("conductor", "fury_mode",            True)
```

---

## PART 7: RECOMMENDED UPGRADES

### Immediate (Week 1)
- [ ] Wire n8n Gmail pipeline (OAuth already built — just needs authorization)
- [ ] Set up Google Drive "ARK95X Intake" folder for weekly data drops
- [ ] Configure winco@network.95 + betco@network.95 auto-forward to primary inbox

### Short-Term (Month 1)
- [ ] Deploy VibeCoder dashboard on Vercel/Netlify (real-time LBG financial view)
- [ ] Connect Square API to ZenCode live data pipeline
- [ ] Build Farmers Trust statement parser (auto-extract from PDF)

### Medium-Term (Month 2-3)
- [ ] Integrate Qdrant vector DB for persistent compound memory across sessions
- [ ] Deploy Ollama local model for offline analysis
- [ ] Add Claude as secondary research layer alongside Manus

### Advanced (Month 3+)
- [ ] n8n workflow: Square data → ZenCode → VibeCoder dashboard (fully automated)
- [ ] Weekly automated P&L report emailed to winco@network.95
- [ ] Legal case timeline auto-updated from Iowa Courts docket

---

## PART 8: QUANTUM BRILLIANCE PROTOCOL

> "See differently. Pattern first. Structure second. Present third."

The quantum lens looks at data from all angles simultaneously:

1. **Forward view:** What does current data predict for next 30/60/90 days?
2. **Backward view:** What patterns from 2023-2024 explain current 2025-2026 state?
3. **Cross-entity view:** How do LBG + Nordskog + Network-95 interact? Where are the leverage points?
4. **Stress view:** What is the worst-case scenario if BHE disconnects + Farmers Trust calls the loan?
5. **Opportunity view:** What single action has the highest ROI right now?

**Answer to #5:** Dispute the BHE Jul 2025 $4,702 fee. If successful, reduces $5,667 balance to ~$965 — a manageable one-time payment. This single action likely prevents disconnection and restores utility accounts to current. **Highest ROI action available today.**

---

## PART 9: OPERATING METRICS — KNOW YOUR NUMBERS

| Metric | Current Value | Target |
|--------|--------------|--------|
| LBG Annual Revenue | $162,216 (2025) | $180,000 (2026) |
| LBG Net Income | ~($2,196) loss | +$10,000 profit |
| Farmers Trust Account | -$4,983.35 NSF | +$5,000 buffer |
| BHE Balance | $5,667 | $0 (resolved) |
| Annual Debt Service | $14,660 | Restructure to $10,000 |
| Cash Sales Documented | ~0% | 100% daily log |
| Crew Deployment | Manual/reactive | Scheduled weekly |

---
*ARK95X Sovereign Stack — Network-95 LLC — Operational Excellence Mode*
*Quantum Brilliance. Unified Crew. Unstoppable.*
