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

if __package__:
    from .dispatcher import Dispatcher, DispatchRequest
else:
    from dispatcher import Dispatcher, DispatchRequest

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
    if mode not in {"full", "quick"}:
        raise ValueError(f"Unknown mission preset: {mode}")
    if verbose:
        print(BANNER)
        print(f"[ARK95X] Prototype run — mode={mode} fury={fury}")

    dispatcher = Dispatcher(fury=fury)

    mission = FULL_MISSION if mode == "full" else QUICK_MISSION
    if verbose:
        print(f"[ARK95X] Checking {len(mission)} task outcomes sequentially...\n")

    t0 = time.time()
    results = dispatcher.batch_route(mission)
    elapsed = time.time() - t0

    if verbose:
        print(f"\n[ARK95X] Prototype run finished in {elapsed:.2f}s")
        print("[ARK95X] === CREW OUTCOME REPORT ===")
    summary = dispatcher.summary()
    summary["elapsed_s"]    = round(elapsed, 2)
    summary["mode"]         = mode
    summary["crew_history"] = dispatcher.crew.memory.history(5)
    summary["execution_status"] = "unverified"
    print(json.dumps(summary, indent=2, default=str))
    if verbose:
        print("[ARK95X] No verified mission result; inspect each blocked or reported outcome.")
    return results

# ── CLI
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="ARK95X Command Center Runner")
    parser.add_argument("--fury",   action="store_true", default=True,
                        help="Enable fury mode (default: on)")
    parser.add_argument("--mode",   choices=["full", "quick"], default="full",
                        help="Mission preset (default: full)")
    parser.add_argument("--quiet",  action="store_true", help="Suppress banner")
    args = parser.parse_args(argv)

    run(fury=args.fury, mode=args.mode, verbose=not args.quiet)
    # No executor/verification adapter is bound to these mission presets.
    return 2


if __name__ == "__main__":
    sys.exit(main())
