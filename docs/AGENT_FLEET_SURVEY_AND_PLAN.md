# Agent Fleet Survey and Plan — 2026-11-21

Audit-first deliverable. Full audit: internal note `agent-fleet-audit-now.md` (Project store). Read-only survey; no account/billing/security settings changed, no keys entered, nothing posted/sent/published/paid/deleted. Job 001 stays NO-GO.

## Reasoning visible (seen → chosen → why)

| Decision | Seen | Chosen | Why |
|---|---|---|---|
| Source of truth | Manifest on PR #48 branch, absent on main | Build separate PR, cite PR #48 | Don't rewrite a PR under review |
| Grok overview | grok.com 200 public; /dashboard 403→login | Overview agent spec is a file; Grok seat state NOT VERIFIED | No signed-in Grok session from this seat |
| Security agent | Emerald audit-agent runs; BLACK 02 is config | New spec wraps Emerald, doesn't replace it | Reuse working code (Green/Yellow, local) |
| API council | brains.json + council service (8300), no spec | Spec adds quorum + credit-law routing | Council exists as plumbing, not governance |
| Cost plan | Credit law in preferences, no log exists | `docs/LIMITS_AND_USAGE_PLAN.md` + cost-log CSV template | Law without a log is unenforceable |
| Settings | cursor-cloud MCP returns env/run; dashboards 403 | Settings list from MCP evidence, UI = Ben-only | Evidence over screenshots we can't get |

## Five areas — status

1. **Agent types:** security PARTIAL, API council PARTIAL, terminal/environment/Cursor/overview MISSING → specs created in `agents/` (files, not live account agents).
2. **Integrations/plugins:** highest value = Grok connectors, GrokBot X Connector (Ben-only), X plugin (LIVE), cursor-cloud MCP (LIVE), local stack (compose). Notes in `docs/PLUGIN_AND_INTEGRATION_SETUP.md` (placeholders only).
3. **Limits/usage:** only X PremiumPlus seen; no balances/usage numbers verified anywhere. Plan in `docs/LIMITS_AND_USAGE_PLAN.md`.
4. **Origin/cloud settings:** cloud verified via MCP (Personal env, egress restricted:false, build bld-20261121-d91275f0); Origin NOT VERIFIED. List in `docs/SETTINGS_ADJUSTMENTS.md` split done/ready/Ben-only.
5. **Create agents:** 7 definitions in `agents/*.md` + health check `scripts/check_agent_fleet.py`. Live dashboard creations needing Ben are named plainly there.

## Browser log

grok.com 200 · grok.com/dashboard 403 login · cursor.com 200 · cursor.com/dashboard 403 auth · origin.com 200→EA (ambiguous) · github repo 200. Nothing unverified presented as live.

## Health check

```bash
python3 scripts/check_agent_fleet.py
```
