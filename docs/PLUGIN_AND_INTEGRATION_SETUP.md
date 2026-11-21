# Plugin & Integration Setup Notes (placeholders only)

| Integration | Value | State | Setup (no keys in chat) |
|---|---|---|---|
| X plugin (Cursor) | X read as @ark95x PremiumPlus | LIVE (PR #48 verified) | Already OAuth-connected; posting = Red per-post Ben yes |
| Grok connectors (Drive/Gmail/Calendar/MCP) | Grok research seat reaches files | PREPARED | Ben in Grok → Settings → Connectors; docs: docs.x.ai/grok/connectors |
| GrokBot X Connector | Mobile @bot X search | BEN-ONLY | Grok Bot app → Marketplace/Settings → Plugins → X for Grok Bot → sign in @ark95x |
| Cursor cloud MCP | Env/run evidence without dashboard login | LIVE (used in audit) | No setup; read-only |
| Customized: API council plugin | Routes jobs by credit law, logs cost | SPEC (`agents/api-council.md`) | Follow-up: wire `ark95x-council` (8300) to council spec; keys only in local `.env` as `COUNCIL_API_KEY=` placeholder |
| Customized: cost logger | Per-job cost receipt | SPEC | `docs/cost-log-template.csv`; fill locally, never commit real spend keys |
| Local stack (n8n/Qdrant/SearXNG/Ollama) | Local-first inference/memory/automation | Compose exists | `cp .env.example .env` locally, placeholders → local secrets only |

Rejected for now: any plugin needing paid signup, pasted bearer tokens, or publish rights — Red, Ben-only.
