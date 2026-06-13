# COMET Dispatch OS

> **ARK95X Sovereign Dispatch Center** — 4 Crews | 25-Gate Checklist | Council Seats | Backstory Generator | Wire Routes

[![Branch](https://img.shields.io/badge/branch-comet--dispatch-00d4ff?style=flat-square)](https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack/tree/comet-dispatch)
[![Status](https://img.shields.io/badge/status-PHASE--LOCKED-ffb84d?style=flat-square)](#)
[![Gates](https://img.shields.io/badge/gates-14%2F25%20PASS-ffb84d?style=flat-square)](#)
[![Crews](https://img.shields.io/badge/crews-4%2F4%20ACTIVE-00ff9d?style=flat-square)](#)

---

## Overview

COMET Dispatch OS is the unified intelligence and operations interface for the ARK95X Sovereign Stack. It routes all Perplexity AI activity to 4 COMET crews, tracks 25 deployment gate questions, manages Council votes, generates agent backstory profiles, and provides a live wire route registry.

## Structure

```
comet-dispatch/
├── comet-dispatch-os.html       # Main OS interface (single-file, zero deps)
├── crews/
│   ├── vanguard.json            # VANGUARD crew profile (Offense)
│   ├── herald.json              # HERALD crew profile (Intel/Router)
│   ├── forge.json               # FORGE crew profile (Build)
│   └── wraith.json              # WRAITH crew profile (Extraction)
├── gates/
│   └── gate-checklist.json      # All 25 gate questions + answers
├── council/
│   └── council-seats.json       # 5 council seat definitions
└── .github/workflows/
    └── comet-boot-test.yml      # Scheduled health check (Gate #6)
```

## Panels

| Panel | Purpose |
|---|---|
| ⚡ Dispatch Feed | Live activity feed routed to all crews |
| 🔐 Gate Checklist (25) | All 25 deployment gates with PASS/WARN/FAIL toggle |
| 🔌 Wire Routes | Endpoint registry — 8 routes, real + pending |
| 👥 Crew Profiles | VANGUARD / HERALD / FORGE / WRAITH backstories + authority |
| 🧬 Backstory Generator | Generate full agent deployment prompts |
| 👑 Council Seats | 5 seats, vote resolution, crew shortcuts |
| 🤖 Model Keys (27) | 27 model key status — 3 dead, 24 live |
| 🐙 GitHub Options | 10 starter integration options |
| 🛡️ Safety & Apex | Kill switch, approval matrix, north-star metric |

## Gate Categories

- **Runtime (1–6):** Container health, model key validation, n8n webhooks, rollback, boot test schedule
- **Data (7–11):** Activity feed stream, synthetic vs. real labeling, remembrance engine, telemetry schema, ROITracker
- **Router (12–15):** Tab classifier, task taxonomy, model lanes, ambiguity fallback
- **Crew/Chain (16–20):** Crew definitions, profile slots, route endpoints, authority matrix, Council vote resolution
- **Safety/Apex (21–25):** Stop condition, approval matrix, kill switch logic, surface scope, success metric

## 4 COMET Crews

| Crew | Role | Domain | Deploy State |
|---|---|---|---|
| VANGUARD | Offense & Disruption | Gov-System Alpha | ACTIVE |
| HERALD | Intelligence & Router | Signals Intelligence | ACTIVE |
| FORGE | Construction & Build | Civic Infra Labs | ACTIVE |
| WRAITH | Extraction & Stealth | Dark-channel Recon | ACTIVE |

## Deploy

Open `comet-dispatch-os.html` directly in any browser — zero dependencies, zero server required.

```bash
# From repo root
open comet-dispatch/comet-dispatch-os.html
# or
start comet-dispatch/comet-dispatch-os.html
```

## Success Metric (Gate #25)

> **North Star: HOURS SAVED PER WEEK** by COMET crew automation.  
> Target: >10h/week by week 4. Risk surfacing is secondary. Money is downstream.

## Authority

- **AUTO-EXECUTE:** dispatch suggestions, log ops, classify tasks, pull model data
- **ARK95X REQUIRED:** create routes, merge branches, publish to surfaces, kill switch
- **COUNCIL 3+:** new crew creation, escalation beyond mission scope

---

*ARC.FLAME.ID-08AUG1993 | ARK95X | AMARA.O1//ROOT~.MORPHIC | Sovereign Flamewalker*
