# AGENTS.md — Jarvis Crew Operating Instructions

## Mission
Build Jarvis as a local-first command system that turns operator requests into structured tasks, reviewed outputs, logs, and repeatable workflows.

## Rule of Work
Use only instructions that are visible in this repository. Do not assume private chat context. If something is missing, document the gap in a TODO or registry note.

## Crew Assignments

### Crew One — Repository Reader
Read these files before building:

1. `AGENTS.md`
2. `JARVIS_DEPLOYMENT_BLUEPRINT.md`
3. `README.md`
4. `docs/JARVIS_REGISTRY.md`
5. `docs/REPO_EXTRACTION_PROTOCOL.md`

Output:

- current objective
- available instructions
- missing instructions
- next safe build step

### Crew Two — Tool Classifier
For every new repository, package, framework, or service, classify it into one Jarvis layer:

- Brain / agent orchestration
- Inference / local model serving
- Memory / vector database
- Automation / workflow engine
- Tools / approved integrations
- Dashboard / observability
- Security / configuration review
- Data / database or event stream
- Domain module / real estate, finance, or research

Reject tools that do not clearly support the architecture.

### Crew Three — Review and Safety
Before use, check:

- required permissions
- secret handling
- local or hosted dependency
- license
- recent maintenance
- Docker or local install support
- whether the action is read-only, file-creating, or external-facing

Risk labels:

- Green: read-only or local inspection
- Yellow: creates files, drafts, configs, or local services
- Red: sends, deletes, pays, trades, publishes, signs, or changes financial, legal, or security status

Red actions require explicit human approval.

### Crew Four — Builder
Create installable files only after review.

Approved first-build outputs:

- `docker-compose.yml`
- `.env.example`
- database schema
- API routes
- n8n workflow JSON
- local test scripts
- README run instructions

Rules:

- Prefer local-first setup.
- Prefer Docker-first setup.
- Use placeholders for secrets.
- Do not hardcode credentials.
- Include a health check or test command for every service.

### Crew Five — Registry Logger
Every material action must be logged in the Jarvis Registry.

Required fields:

- date
- crew
- repository or tool
- Jarvis layer
- action taken
- files changed
- risk label
- review result
- test command
- next move

No undocumented work.

## Command Loop

```text
Observe -> Decode -> Route -> Build -> Verify -> Remember -> Scale
```

## Master Commands

- OBSERVE: collect current state
- ANALYZE: find meaning and risk
- PLAN: choose sequence
- BUILD: create asset or system
- RESEARCH: gather facts
- VERIFY: check truth, safety, and fit
- REMEMBER: store reusable knowledge
- REPORT: summarize for decision
- AUTOMATE: make repeatable workflow
- EXECUTE: perform approved action

## Non-Negotiables

- No secrets in code.
- No unreviewed external actions.
- No undocumented changes.
- No live trading execution.
- No destructive actions without explicit approval.
- Every material action must be auditable.
