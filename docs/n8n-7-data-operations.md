# n8n 7 Data Operations Layer

This layer makes n8n the workflow bus for Player 2.

The goal is not to let random automations run wild. The goal is to feed Player 2 with clean, staged, approved data so it can score the next best action.

## The seven data lanes

| Lane | Purpose | Safe mode |
|---|---|---|
| GitHub repo intake | Pull repos, issues, PRs, workflow signals | Official API / read-first |
| Local PC inventory | Map Windows 11 Pro resources and tools | Read-only inventory |
| Logs/proof ingest | Capture errors, hashes, outputs, skill results | Workspace read-only |
| Trading research signals | Translate research/backtest patterns into ops scoring | Research-only, no live trading |
| Real-estate ops data | Convert portfolio/task data into execution queues | Local/imported data only |
| Legal case ops data | Organize deadlines, filings, evidence, attorney tasks | Assistive organization, not legal advice |
| Content/social signal intake | Convert approved content data into campaign tasks | Official APIs/exports only |

## Workflow shape

```text
Trigger
  -> Credentialed Source Node
  -> Normalize JSON
  -> Player2 Score Function
  -> SQLite/Postgres Write
  -> Proof Manifest Write
  -> Human Review Gate
  -> Optional Dispatch
```

## Player 2 relationship

n8n should not be the brain. n8n is the workflow transport layer.

```text
n8n = data movement and scheduled operations
Player 2 = scoring, routing, and next-action selection
Codex = build and patch
Claude = review and audit
Ollama/Hermes = local planning and symbolic translation
GitHub = source control and proof
```

## Recommended first workflow

Start with GitHub repo intake because it gives Player 2 the cleanest source-of-truth signal.

1. Trigger: manual or scheduled.
2. Source: GitHub API / `gh` CLI.
3. Normalize: repo name, updated date, branch, open issues, open PRs, failed workflows.
4. Score: priority based on urgency, value, and broken state.
5. Store: SQLite `tasks` and `signals` tables.
6. Proof: write manifest.
7. Review: human gate before external write.

## Safe dispatch policy

Automatic dispatch is allowed only for:

- workspace-local file generation,
- proof manifest generation,
- read-only indexing,
- local task queue updates.

Human approval is required for:

- GitHub writes,
- deployments,
- credentialed API actions,
- public posting,
- financial/trading actions,
- legal filings,
- destructive or system-level commands.
