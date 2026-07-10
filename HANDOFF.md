# ARK95X Command Ledger - Handoff Protocol

This document is how a fresh Claude, Ollama, Groq, or Gemini session picks
up this build with nothing but this repository. Claude running out of
credits (or any other backend going down) is a **routing event, not a
stop**.

## The one rule

**`ARK-STATE.json` at the repo root is the single source of truth.**
It holds the mission, the data flow, every module's status, the current
phase, and a `todo_queue` of tasks with dependencies. If something in this
document ever disagrees with `ARK-STATE.json`, trust the JSON file — it is
updated after every completed task; this file is not.

## How to resume, step by step

1. Read `ARK-STATE.json` in full.
2. Read `contracts/ark-state.schema.json` — every module in this build
   reads/writes one of its four message shapes (`signal`,
   `risk_sized_order`, `ledger_entry`, `telemetry_event`).
3. In `ARK-STATE.json.todo_queue`, find the **first entry** where:
   - `status == "pending"`, and
   - every id in `depends_on` has `status == "done"` on its own entry.
4. Execute that task.
5. Update that entry's `status` (`"done"`, or `"in_progress"` if you had to
   stop partway), plus the top-level `updated_at` (ISO-8601 UTC) and
   `updated_by` (your backend name: `claude`, `ollama`, `groq`, `gemini`).
6. Commit and push to the working branch. **Do not merge to `main`** —
   that is a manual human decision on this build, not something any
   backend should do autonomously.

`router/failover.py` automates steps 3-5 mechanically (it does not write
code -- it dispatches the task description to whichever backend is
reachable, so a human or the receiving model still has to do the actual
work described in step 4). See below.

## Repo layout

| Path | What it is |
|---|---|
| `ARK-STATE.json` | Build genome: source of truth, read this first |
| `contracts/ark-state.schema.json` | Shared message contracts for the whole pipeline |
| `netx/signal_engine.py` | `Signal` + `SignalBus`: NetX/n8n signal ingestion |
| `netx/risk_calculator.py` | Position sizing: `capital * risk_pct/100 / stop_distance` |
| `passive_income_engine.py` | Real ledger entries, balance, ROI, lossless snapshot/restore |
| `ledger/command_ledger.py` | Wires signal -> risk -> ledger -> telemetry together |
| `cockpit/app.py` | FastAPI + WebSocket cockpit on `:8080` (ROI ledger, leverage meter, Aura state) |
| `router/failover.py` | Reads `todo_queue`, dispatches to Claude/Ollama/Groq/Gemini |
| `workflows/ark_failover_dispatch_v1.json` | n8n workflow that runs the router on a schedule |
| `tests/test_command_ledger.py`, `tests/test_cockpit.py`, `tests/test_failover.py` | Full test coverage, no `pytest-asyncio` required (async calls are wrapped in `asyncio.run()` inside plain `def test_...()` functions -- keep doing this so tests run under this repo's existing CI, which only installs `pytest`/`pytest-cov`) |

## Running the failover router manually

```bash
# Reads ARK-STATE.json, finds the next pending task, dispatches it to
# whichever backend below is reachable, and updates the task's status.
python3 router/failover.py
```

Backend availability is environment-driven, checked in this priority order:

| Priority | Backend | How availability is checked | Env vars |
|---|---|---|---|
| 1 | Claude | `ANTHROPIC_API_KEY` is set | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (default `claude-sonnet-4-5`) |
| 2 | Ollama | `GET {OLLAMA_HOST}/api/tags` responds 200 | `OLLAMA_HOST` (default `http://localhost:11434`), `OLLAMA_MODEL` (default `llama3`) |
| 3 | Groq | `GROQ_API_KEY` is set | `GROQ_API_KEY`, `GROQ_MODEL` (default `llama-3.3-70b-versatile`) |
| 4 | Gemini | `GEMINI_API_KEY` or `GOOGLE_API_KEY` is set | `GEMINI_API_KEY` / `GOOGLE_API_KEY`, `GEMINI_MODEL` (default `gemini-2.0-flash`) |

The n8n workflow (`workflows/ark_failover_dispatch_v1.json`) runs this same
script on an hourly heartbeat via an Execute Command node, then commits and
pushes the updated `ARK-STATE.json` back to GitHub so every future session
-- regardless of which backend runs it -- sees the same state. It has not
been live-tested against a running n8n instance; verify the
`ARK_REPO_PATH` env var and Discord/Google Sheets credentials before
enabling it.

## Verifying the pipeline still works after a change

```bash
pip install -r requirements.txt pytest flake8
pytest tests/ -v
flake8 . --max-line-length=120 --extend-ignore=E501,W503,E402,F401,E722,E127
```

For the cockpit specifically, a manual live check (not just `TestClient`):

```bash
python3 -m uvicorn cockpit.app:app --host 0.0.0.0 --port 8080 &
curl -X POST http://localhost:8080/netx/webhook -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSD","side":"long","entry_price":100.0,"stop_price":95.0}'
curl http://localhost:8080/roi   # should reflect the order you just sized
```

## Known gaps (see `ARK-STATE.json.known_gaps` for the authoritative list)

- `smart_home_bridge.py` and a multi-PC coordinator were mentioned in the
  original brief but are out of scope for this data flow and were not built.
- `cockpit/app.py` is a new build in this repo, not a patch to the
  `omnikernel-orchestrator` repo (which has no FastAPI/:8080/WebSocket
  cockpit, no Aura canvas, and no ROI ledger anywhere in it, verified by
  cloning and inspecting it directly).
- The n8n workflow has not been executed against a live n8n instance.
