# ARC X Omnicodex Model Fleet Hierarchy

Status: architecture layer
Owner: ARK95X
Purpose: Define the highest-level GPT-style brain engine as a modular, model-fleet command system where every model, old or new, can be routed when it is the best fit.

---

## 1. Core Answer

The highest brain is not one model.

The highest brain is the codex that knows how to use every model.

```text
Apex model alone = powerful but blind to operational context.
Apex codex + model fleet + memory + tools + evals + governance = operating intelligence.
```

The codex is the operating grammar: hierarchy, logic, roles, routing, memory, risk gates, tool use, feedback, and deployment rules.

---

## 2. Title of the Apex GPT

Recommended title:

```text
ARC X OMNICODEX
```

Role:

```text
Tier-0 Apex Intelligence Coordinator
```

Purpose:

```text
Select the right model, right lens, right tool, right workflow, right guardrail, and right next action for every command.
```

It is not the worker. It is the command law above the workers.

---

## 3. Hierarchy Under ARC X OMNICODEX

```text
Tier 0: ARC X OMNICODEX
- Apex coordinator
- Strategic intent interpreter
- Model fleet router
- Governance commander
- Memory decision authority
- Output quality judge

Tier 1: Core Intelligence Council
- Reasoning Brain
- Code Brain
- Vision Brain
- Research Brain
- Automation Brain
- Business Brain
- Security/Risk Brain
- Memory Brain

Tier 2: Specialist GPTs / Agents
- Real Estate Agent
- Lead Leak Agent
- Visual Due Diligence Agent
- Prompt Judge Agent
- Income Filter Agent
- Client Delivery Agent
- Content Authority Agent
- Data Analyst Agent
- Legal/Compliance Guardrail Agent

Tier 3: Tool Layer
- ChatGPT / frontier reasoning models
- Codex / coding agents
- Claude Code / alternative coding agents
- Perplexity / research browser
- GitHub
- Notion / Sheets / databases
- Google Drive
- n8n / Make / Zapier
- CRM / email / calendar
- local devices / edge compute

Tier 4: Data Layer
- client records
- lead trackers
- content metrics
- repo history
- conversation logs
- file store
- vector memory
- structured memory
- audit log

Tier 5: Deployment Layer
- drafts
- dashboards
- reports
- issues
- pull requests
- workflows
- client deliverables
- approval queue
- final archive
```

---

## 4. Model Fleet Logic

Every model is treated as a tool with a capability profile.

```json
{
  "model_id": "string",
  "model_type": "reasoning | code | vision | research | small_fast | local | legacy | experimental",
  "strengths": ["string"],
  "weaknesses": ["string"],
  "cost": "low | medium | high",
  "speed": "fast | medium | slow",
  "privacy_level": "local | private_cloud | public_api",
  "context_capacity": "small | medium | large | huge",
  "best_tasks": ["string"],
  "do_not_use_for": ["string"],
  "last_eval_score": 0
}
```

Routing rule:

```text
Do not ask: what is the newest model?
Ask: what model is best for this exact job, risk level, budget, context, speed, and proof requirement?
```

---

## 5. Highest Hidden Lenses

These are the lenses most systems do not activate unless forced.

### 1. Consequence Lens

What happens if this works, fails, scales, or gets copied?

### 2. Second-Order Systems Lens

What downstream behaviors does this create?

### 3. Incentive Lens

Who benefits, who resists, who changes behavior, and why?

### 4. Trust Lens

Where can confidence collapse?

### 5. Evidence Lens

What is observed, what is inferred, what is unsupported?

### 6. Latent Constraint Lens

What invisible constraint is controlling the whole situation?

### 7. Temporal Lens

What looks good today but breaks in 30, 90, or 365 days?

### 8. Adversarial Lens

How would this be misunderstood, misused, attacked, copied, or degraded?

### 9. Mobility Lens

What still works from a phone, weak signal, field situation, or low-resource device?

### 10. Memory Lens

What must be stored so the next run is smarter?

---

## 6. Mobile Sense

Mobile does not mean smaller. Mobile means operational anywhere.

```text
Phone = capture, command, review, approval, lightweight drafts.
Laptop = build, edit, inspect, deliver.
Desktop/GPU = heavy compute, batch analysis, local models, media, simulation.
Cloud = durable workflows, APIs, queues, dashboards, backups.
```

Mobile architecture:

```text
voice note -> command packet -> cloud or local router -> model selection -> draft output -> approval queue -> deployment or archive
```

Mobile must support:

- voice capture
- photo upload
- document scan
- quick approval
- lead update
- dashboard check
- call notes
- memory patch
- emergency freeze command

---

## 7. Self-Correcting Feedback Loop

The codex improves through outcomes, not fantasy.

```text
Command -> output -> eval -> action -> result -> memory -> route score -> next command
```

Each route gets scored:

```text
clarity
accuracy
speed
risk control
client usefulness
conversion value
reuse potential
```

If a route fails:

```text
1. identify failure mode
2. update prompt or schema
3. adjust model routing
4. add edge case
5. rerun eval
6. write memory patch
```

---

## 8. Edge-Case Simulator

Before output ships, ARC X should simulate:

```text
Client misunderstands it.
Client asks for legal advice.
Lead rejects offer.
Message sounds spammy.
Dashboard field is missing.
Automation fails.
Model hallucinates.
Private data appears in content.
Payment received but intake missing.
Diagnostic is late.
Build scope expands.
```

Every edge case becomes:

```text
risk -> response -> template -> automation candidate -> memory patch
```

---

## 9. Governance Mechanism

The codex aligns output with strategic intent through gates.

```text
Gate 1: Intent
Does this match ARK95X mission?

Gate 2: Evidence
Is this observed, inferred, or unsupported?

Gate 3: Risk
Does this create legal, privacy, platform, reputation, financial, or safety exposure?

Gate 4: Value
Does this create revenue, clarity, speed, automation, authority, or reusable knowledge?

Gate 5: Approval
Can this stage automatically, or does Commander approve?

Gate 6: Memory
What should be saved, upgraded, paused, or archived?
```

---

## 10. What The Apex GPT Is Capable Of In This System

In its own system, the top GPT can:

```text
hold the full operating map
route all sub-models
translate messy input into task packets
maintain project continuity
generate deliverables
critique deliverables
simulate edge cases
stage client-facing outputs
build code tasks
extract patterns from images and documents
turn lessons into SOPs
track conversion signals
create memory patches
force approval gates
coordinate mobile and desktop workflows
```

But the apex must not pretend to know what it cannot observe.

Its real strength is disciplined uncertainty and fast route correction.

---

## 11. The Codex Definition

The codex is not just code.

The codex is:

```text
1. identity
2. hierarchy
3. command language
4. model fleet registry
5. tool registry
6. memory schema
7. eval rules
8. approval gates
9. deployment rules
10. learning loop
```

Final compression:

```text
Model = brain.
Tools = hands.
Memory = history.
Evals = mirror.
Governance = spine.
Deployment = legs.
Codex = the nervous system that makes them one.
```

---

## 12. Build Files To Implement Next

```text
schemas/model-fleet-registry.schema.json
schemas/route-decision.schema.json
src/router/model_fleet_router.py
src/evals/route_quality_eval.py
src/memory/route_score_memory.py
src/governance/strategic_intent_gate.py
src/mobile/command_packet.py
```
