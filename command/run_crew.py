#!/usr/bin/env python3
# run_crew.py — ARK95X Command Center Master Launcher
# Boots the full unified crew stack with fury + multiplexing
# Usage: python run_crew.py [--fury] [--mode full|quick|custom]

from __future__ import annotations
import argparse
import json
import sys
import time
from typing import List

from unified_crew import UnifiedCrew, CrewTask, AgentRole, get_crew
from dispatcher import Dispatcher, DispatchRequest, get_dispatcher

BANNER = """
██████╗ █████╗ ██╗  ██╗ █████╗ ██╗ ██╗  ███╗  ██╗ ██████╗ ██╗  ██╗
██╔════╝██╔══██╗██║ ██╔╝██╔══██╗██║ ██╔══██╗ ██║╚════██╗██║ ██╔╝
█████╗  ██║  ██║█████╔╝ ▉██████║██║ ██║  ██║ ██║ █████╔╝ █████╔╝
╚═══██╗██║  ██║██╔═██╗ ██╔══██║██║ ██║  ██║ ██║ ██╔══██╗██╔═██╗
██████╔╝╚█████╔╝██║  ██╗██║  ██║██║ ╚█████╔╝██║╔██████╔╝██║  ██╗
╚═════╝ ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚════╝ ╚═╝╚═════╝ ╚═╝  ╚═╝
         UNIFIED SOVEREIGN STACK — COMMAND CENTER
           Manus | ZenCode | VibeCoder | Conductor
"""

# ── Mission presets
FULL_MISSION: List[DispatchRequest] = [
    # Priority 9 — Critical
    DispatchRequest("Deep research: Reliance State Bank litigation intel",
                    "litigation", priority=9),
    DispatchRequest("Build command center API with full routing",
                    "api", priority=9),
    # Priority 8 — High
    DispatchRequest("Design sovereign command center dashboard",
                    "dashboard", priority=8),
    DispatchRequest("Deploy protocol router + agent multiplex engine",
                    "deploy", priority=8),
    DispatchRequest("Extract compound history data + pattern recognition",
                    "data", priority=8),
    # Priority 7 — Standard
    DispatchRequest("Build real-time agent status + workload UI",
                    "ui", priority=7),
    DispatchRequest("Analyze property portfolio financial data",
                    "financial", priority=7),
    DispatchRequest("Refactor and compress all command center modules",
                    "refactor", priority=7),
    # Priority 6 — Enhancement
    DispatchRequest("Design multi-agent visual flow + brand system",
                    "design", priority=6),
    DispatchRequest("Build database schema for case + property tracking",
                    "database", priority=6),
    DispatchRequest("Create test suite for all agent protocols",
                    "test", priority=6),
    DispatchRequest("Build UX flow for command center navigation",
                    "ux", priority=6),
]

QUICK_MISSION: List[DispatchRequest] = [
    DispatchRequest("Research latest litigation status",     "litigation", priority=9),
    DispatchRequest("Build core API endpoint",               "api",        priority=8),
    DispatchRequest("Render quick status dashboard",          "dashboard",  priority=7),
]

# ── Main runner
def run(fury: bool = True, mode: str = "full", verbose: bool = True):
    print(BANNER)
    print(f"[ARK95X] Booting — mode={mode} fury={fury}")
    print(f"[ARK95X] Initializing unified crew...")

    dispatcher = Dispatcher(fury=fury)

    if fury:
        print("[ARK95X] *** FURY MODE ENGAGED — ALL AGENTS UNLEASHED ***")
        print("[ARK95X] *** MULTIPLEX ACTIVE — 3x PARALLEL STREAMS ***")

    mission = FULL_MISSION if mode == "full" else QUICK_MISSION
    print(f"[ARK95X] Dispatching {len(mission)} tasks across crew...\n")

    t0 = time.time()
    results = dispatcher.batch_route(mission)
    elapsed = time.time() - t0

    print(f"\n[ARK95X] All tasks complete in {elapsed:.2f}s")
    print("[ARK95X] === CREW STATUS REPORT ===")
    summary = dispatcher.summary()
    summary["elapsed_s"]    = round(elapsed, 2)
    summary["mode"]         = mode
    summary["crew_history"] = dispatcher.crew.memory.history(5)
    print(json.dumps(summary, indent=2, default=str))
    print("[ARK95X] === MISSION COMPLETE — ARK95X SOVEREIGN STACK LIVE ===")
    return results

# ── CLI
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARK95X Command Center Runner")
    parser.add_argument("--fury",   action="store_true", default=True,
                        help="Enable fury mode (default: on)")
    parser.add_argument("--mode",   choices=["full", "quick"], default="full",
                        help="Mission preset (default: full)")
    parser.add_argument("--quiet",  action="store_true", help="Suppress banner")
    args = parser.parse_args()

    run(fury=args.fury, mode=args.mode, verbose=not args.quiet)
