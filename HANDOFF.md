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
| `passive_income_engine.py` | Real ledger entries, balance, ROI, lossless snapshot/restore. Optional `postgres_url` param persists to a real Postgres database instead of (or in addition to) the JSON file. |
| `ledger/command_ledger.py` | Wires signal -> risk -> ledger -> telemetry together. Also holds `request_close_order()`/`approve_pending_action()` -- the control-plane-gated close-position flow (see below). |
| `cockpit/app.py` | FastAPI + WebSocket cockpit on `:8080`. Routes: `/health`, `/monitoring/health`, `/roi`, `/netx/webhook`, `/fills`, `/pending`, `/approve/{request_id}`, `/control-plane`, `/failover/dispatch`, `/ws/cockpit`. |
| `control_plane/control_plane.py` | Single authority/reporting contract over the 8 ARK95X roles. `APPROVAL_REQUIRED_ACTION_CLASSES` gates financial/destructive/deployment/etc. actions to human approval; `ARK-STATE.json` is the declared `AUTHORITATIVE_STATE_PATH`. |
| `monitoring/health.py`, `memory_cortex/proposals.py`, `codex_security/scanner.py`, `devices/local_exec.py`, `github_adapter/repo_state.py`, `n8n/dispatch_adapter.py` | The other 7 control-plane role adapters, each wired to its own real integration point (see `ARK-STATE.json.modules.control_plane_remaining_adapters` for the full breakdown). |
| `router/failover.py` | Reads `todo_queue`, dispatches to Claude/Ollama/Groq/Gemini. Optionally reports dispatch decisions through a `control_plane` under `arc_x`'s `routing` scope. Also reachable over HTTP via cockpit's `POST /failover/dispatch`. |
| `workflows/ark_failover_dispatch_v1.json` | n8n workflow that runs the router (via an HTTP Request node against the cockpit, not a shell command) on a schedule. Live-tested against a real n8n instance -- see the caveats below. |
| `docker-compose.yml` (`postgres`, `mongodb`, `redis`, `qdrant`, `n8n` services) | The live data stack backing all of the above. Bring it up with `docker compose up -d postgres mongodb redis qdrant n8n`. |
| `scripts/prove_the_network.py` | Re-runnable end-to-end proof: drives the real cockpit in-process to prove the authority gate blocks then releases real money with a matching audit trail, then proves the failover cascade. `python3 scripts/prove_the_network.py`. |
| `tests/` | Full test coverage (100+ tests across the ledger, cockpit, control plane, and every adapter -- see `tests/test_*.py`), no `pytest-asyncio` required (async calls are wrapped in `asyncio.run()` inside plain `def test_...()` functions -- keep doing this so tests run under this repo's existing CI, which only installs `pytest`/`pytest-cov`, per `.github/workflows/ci.yml`) |

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
dispatch on an hourly heartbeat, then commits and pushes the updated
`ARK-STATE.json` back to GitHub so every future session -- regardless of
which backend runs it -- sees the same state. Its dispatch step
(`Run_Failover_Router`) is an **HTTP Request node** calling
`POST {COCKPIT_URL}/failover/dispatch` on the running cockpit -- not a
shell `python3 router/failover.py` call -- because n8n's official Docker
image ships no `python3` and has no repo checkout mounted. Only
`Commit_Genome_Update` (git add/commit/push) still uses an Execute Command
node.

This workflow **has been live-tested** against a real n8n instance
(`n8nio/n8n:latest` in the data stack, 2026-09-03): `Failover_Heartbeat ->
Run_Failover_Router -> Check_Dispatch_Status` all ran successfully end to
end. Two parts remain untested live: `Commit_Genome_Update` (needs a host
with real git + repo access, which n8n's container doesn't have) and the
Discord/Google Sheets notification nodes (need real credentials). See
[Control plane and data stack](#control-plane-and-data-stack) below for how
to bring up the n8n instance this was tested against.

## Verifying the pipeline still works after a change

```bash
pip install -r requirements.txt pytest flake8
pytest tests/ -v
flake8 . --max-line-length=120 --extend-ignore=E501,W503,E402,F401,E722,E127
```

For the cockpit specifically, a manual live check (not just `TestClient`).
`/netx/webhook`, `/fills`, `/approve/{id}`, `/pending`, `/control-plane`, and
`/failover/dispatch` require an `X-Cockpit-Token` header matching
`COCKPIT_ADMIN_TOKEN` (a random one is generated and logged once if you
don't set it) -- `/health`, `/monitoring/health`, `/roi`, and `/ws/cockpit`
stay open as the read-only dashboard surface:

```bash
COCKPIT_ADMIN_TOKEN=dev-token python3 -m uvicorn cockpit.app:app --host 0.0.0.0 --port 8080 &
curl -X POST http://localhost:8080/netx/webhook -H "Content-Type: application/json" \
  -H "X-Cockpit-Token: dev-token" \
  -d '{"symbol":"BTCUSD","side":"long","entry_price":100.0,"stop_price":95.0}'
curl http://localhost:8080/roi   # should reflect the order you just sized -- no token needed, read-only
```

## Control plane and data stack

Phase 5 added two things a fresh session needs to know about before picking
up where this build left off:

- **`control_plane/control_plane.py`** is a single authority/reporting
  contract sitting over the 8 ARK95X roles (`arc_x`, `codex_security`,
  `memory_cortex`, `monitoring`, `github`, `n8n`, `devices`,
  `business_ops`). No agent can override the plane or self-approve; any
  action classed as `account_change`, `destructive`, `deployment`,
  `financial`, `legal`, `public`, `security_sensitive`, or
  `system_mutation` (see `APPROVAL_REQUIRED_ACTION_CLASSES`) is queued for
  human approval instead of executing immediately. `ledger/command_ledger.py`
  wires this into the highest-value action -- closing a position -- via
  `request_close_order()`/`approve_pending_action()`, exposed through
  `cockpit/app.py`'s `/fills`, `/pending`, `/approve/{id}`, and
  `/control-plane` routes (`CONTROL_PLANE_ENABLED=true` by default). The
  other 7 roles are wired to their own real integration points -- see
  `ARK-STATE.json.modules.control_plane_remaining_adapters` and
  `docs/control-plane-pass-1.md` for the full contract and per-role detail.
  Proved live end to end by `scripts/prove_the_network.py` (15/15 checks).
- **The data stack** (`postgres`, `mongodb`, `redis`, `qdrant`, `n8n` in
  `docker-compose.yml`) is live and verified, not just defined:
  ```bash
  docker compose up -d postgres mongodb redis qdrant n8n
  ```
  `postgres` backs `passive_income_engine.py`'s optional `postgres_url`
  ledger persistence (proved durable across a simulated restart); `n8n`
  hosts `workflows/ark_failover_dispatch_v1.json`. `mongodb`/`redis`/`qdrant`
  are up and TCP-probed by `/monitoring/health` but have no Command-Ledger
  consumer wired to them yet.

If you're resuming from `ARK-STATE.json.todo_queue`, `T5.4`-`T5.7` (control
plane, the ledger's financial-action gate, the remaining 7 adapters, and
the live data stack) are all `done` -- only `T5.1` (human review of PR #31)
and `T5.3` (a real trading account behind `/netx/webhook`) are still
`pending`.

## Known gaps (see `ARK-STATE.json.known_gaps` for the authoritative list)

- `smart_home_bridge.py` and a multi-PC coordinator were mentioned in the
  original brief but are out of scope for this data flow and were not built.
- `cockpit/app.py` is a new build in this repo, not a patch to the
  `omnikernel-orchestrator` repo (which has no FastAPI/:8080/WebSocket
  cockpit, no Aura canvas, and no ROI ledger anywhere in it, verified by
  cloning and inspecting it directly).
- No real broker/exchange or production NetX signal source is wired behind
  `/netx/webhook` yet (`T5.3`, still pending) -- signals are posted
  manually or by n8n for testing.
- In `workflows/ark_failover_dispatch_v1.json`, the dispatch path itself
  (`Failover_Heartbeat -> Run_Failover_Router -> Check_Dispatch_Status`) IS
  live-tested (`T5.2`); `Commit_Genome_Update` and the Discord/Google Sheets
  notification nodes are not.
- `control_plane/` was added directly to this branch outside the
  `todo_queue` (commits `89e0428..5ce3c5b`, 2026-07-19) before this genome
  was updated to reflect it -- reconciled retroactively as `T5.4`/`T5.5`.
  Future sessions adding a module should update `ARK-STATE.json` in the
  same commit, not after the fact.
