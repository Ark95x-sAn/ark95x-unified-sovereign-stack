# Revenue Radar

A local-first opportunity workflow that enforces:

`Capture → clean → deduplicate → score → draft → approve → send → log outcome`

The application uses Python's standard library and SQLite. It binds only to
`127.0.0.1`, defaults to dry-run mode, and will not send anything externally
until live mode and an approved n8n webhook are both explicitly configured.

## Safety gate

Do not run this—or any always-on service—on the PC, monitor, cord, power strip,
or outlet involved in smoke/fire until the affected equipment has been
unplugged and inspected or replaced.

## Start on Windows

1. Install Python 3.10 or newer if `py --version` does not work.
2. Open PowerShell in this folder.
3. Run:

```powershell
py .\revenue_radar.py
```

4. Open <http://127.0.0.1:8765>.

The first run creates `revenue_radar.db` beside the script. Keep that database
backed up; it contains the opportunity records and audit ledger.

## What is already operational

- Cleans whitespace, validates email/phone, and normalizes contact keys.
- Merges exact duplicate fingerprints without deleting stronger data.
- Flags same-contact/different-opportunity records for human duplicate review.
- Produces a deterministic 0–100 score with visible component reasons.
- Creates a safe template draft; optional local Ollama drafting falls back to
  the template if the model is unavailable or returns invalid JSON.
- Binds approval to the exact recipient, subject, and body using SHA-256.
- Defaults every send to simulation, with no outbound network request.
- Uses an idempotency key and a `sending` state to prevent double-click sends.
- Records capture, merge, approval, send attempt, handoff, failure, and outcome
  events in an append-only audit table.

## Optional local Ollama drafting

Ollama affects drafting only. It never changes the score, approves, or sends.

```powershell
$env:REVENUE_RADAR_USE_OLLAMA="1"
$env:OLLAMA_URL="http://127.0.0.1:11434"
$env:OLLAMA_MODEL="qwen3:14b"
py .\revenue_radar.py
```

## Connect an n8n send workflow

Build an n8n webhook that accepts `POST` JSON, verifies the supplied approval
object and `Idempotency-Key`, sends through the credentialed provider, and
returns a provider message ID. Keep n8n private on localhost or Tailscale.

Test the n8n workflow independently, then enable live handoff:

```powershell
$env:REVENUE_RADAR_DRY_RUN="0"
$env:REVENUE_RADAR_SEND_WEBHOOK_URL="http://127.0.0.1:5678/webhook/revenue-radar-send"
py .\revenue_radar.py
```

Remote plain-HTTP webhooks are rejected. Use HTTPS or localhost HTTP. A 2xx
webhook response is logged as `handed_off`, not confirmed delivery; the final
provider result belongs in the outcome log.

## Run the tests

```powershell
py -m unittest -v test_revenue_radar.py
```

## Main environment controls

| Variable | Default | Purpose |
|---|---|---|
| `REVENUE_RADAR_DRY_RUN` | `1` | `0` enables webhook handoff |
| `REVENUE_RADAR_SEND_WEBHOOK_URL` | empty | Approved n8n webhook |
| `REVENUE_RADAR_USE_OLLAMA` | `0` | `1` enables local AI drafting |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `qwen3:14b` | Drafting model |
| `REVENUE_RADAR_DB` | local DB | Alternate SQLite path |
| `REVENUE_RADAR_PORT` | `8765` | Local dashboard port |

## Production boundary

This is a controlled MVP, not a mass-mailing engine. Keep human approval for
every external message. Before production volume, add authenticated operator
accounts, encrypted backups, provider delivery callbacks, rejection/revocation,
and a recovery screen for ambiguous `sending` records.

