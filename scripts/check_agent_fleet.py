#!/usr/bin/env python3
import pathlib, sys
root = pathlib.Path(__file__).resolve().parents[1]
need = ["agents/security-agent.md","agents/terminal-agent.md","agents/environment-agent.md","agents/cursor-agents-roster.md","agents/api-council.md","agents/overview-agent.md","docs/AGENT_FLEET_SURVEY_AND_PLAN.md","docs/PLUGIN_AND_INTEGRATION_SETUP.md","docs/LIMITS_AND_USAGE_PLAN.md","docs/SETTINGS_ADJUSTMENTS.md"]
missing=[p for p in need if not (root/p).exists()]
bad=[]
for p in root.rglob("*.md"):
    if "sk-" in p.read_text(errors="ignore") and "placeholder" not in p.read_text(errors="ignore").lower():
        pass
print("MISSING:",missing) if missing else print("OK agent fleet files present:",len(need))
sys.exit(1 if missing else 0)
