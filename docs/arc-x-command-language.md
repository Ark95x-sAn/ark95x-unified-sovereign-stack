# ARC X Command Language

Status: Phase 1 command syntax
Owner: ARK95X
Purpose: Convert raw thought, voice, files, screenshots, links, repos, leads, and symbolic commands into exact execution routes.

---

## 1. Command Packet

```json
{
  "raw_signal": "string",
  "source": "chat | voice | file | screenshot | repo | browser | email | calendar | wearable | crm | manual",
  "mode": "decode | build | research | post | code | automate | audit | memory | simulate | realestate | wellness | hardware",
  "desired_output": "string",
  "approval_mode": "auto_draft | require_review | restricted",
  "context": {}
}
```

---

## 2. Core Commands

```text
/decode       Recover the true objective from raw language.
/cut          Challenge weak logic, missing facts, and low-leverage motion.
/scale9       Expand across objective, audience, data, platform, automation, money, risk, feedback, and next action.
/route        Choose the right agent, tool, model, device, or workflow.
/simulate     Run best/base/worst-case outcomes with probability ranges.
/prompt       Create the best prompt for a target model or platform.
/codex        Convert an idea into a Codex-ready engineering task.
/claude-code  Convert an idea into a Claude Code CLI or SDK task.
/github       Create an issue, repo structure, PR plan, or review checklist.
/automate     Build a workflow using n8n, Make, Zapier, scripts, APIs, or webhooks.
/research     Run a source-grounded research brief.
/post         Create LinkedIn, X, blog, email, or short-form content.
/comment      Generate response/comment options for a target post.
/income       Turn an idea into offers, products, retainers, or monetization paths.
/realestate   Convert a lead, property, market, listing, or investor question into action.
/hardware     Map machine/device capability and route workloads.
/wellness     Create wellness reflection, journaling, trend summary, or appointment-prep output.
/memory       Store, retrieve, upgrade, suppress, or retire a pattern.
/audit        Review logs, outputs, routes, risks, and drift.
/deploy       Stage execution into draft, issue, workflow, queue, dashboard, or notification.
```

---

## 3. Legend Interpreter

Symbolic commands map to production commands:

```text
Emerald Tablet Mode -> /decode + /cut + /scale9 + /deploy + /memory
Akashic Library -> memory retrieval + source confidence review
Twin Second Brain -> personalized memory + route history + decision rules
Fractal Self -> task-specific operating mode
Pulse Engine -> metrics, logs, sensors, engagement, system telemetry
Radar/Sonar -> research and monitoring
Flame/Grid/Map -> dashboard or routing visualization
2080 Automation -> high-speed repeatable workflow builder
```

Rule:

```text
Legend language is accepted as interface. Production must output function, file, schema, workflow, prompt, code task, or decision.
```

---

## 4. Review Modes

```text
auto_draft
Safe for drafts, plans, prompts, local notes, schemas, and non-public outputs.

require_review
Used when an output will affect public channels, repositories, external tools, client work, or durable records.

restricted
Used when the safest path is to redesign the request into a permitted alternative.
```

---

## 5. Output Contract

```text
Decoded:
Cut:
Best Move:
Execution:
Agent Route:
Offensive Score:
Defensive Structure:
Bottleneck:
Memory Patch:
Next Action:
```

---

## 6. Priority Rule

```text
1. Safety, privacy, and authorization
2. User mission alignment
3. Highest compound value
4. Fastest stable execution
5. Reusable asset creation
6. Style and legend layer
```

---

## 7. Deployment Rule

```text
Draft before publish.
Issue before implementation.
Plan before activation.
Research before current-fact claims.
Review before irreversible action.
Log after every meaningful action.
```
