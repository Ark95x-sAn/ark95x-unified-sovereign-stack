# Web Intelligence 9-Angle Skill Pack

This document converts current public source intelligence into operational skills for Player 2, n8n, GitHub, local development, proof, and deployment.

## Source-backed extraction loop

```text
discover source
  -> verify authority
  -> extract pattern
  -> normalize into a skill spec
  -> score operational value
  -> generate skill
  -> test in workspace
  -> write proof
  -> feed result back into Skill Factory
```

## The nine angles

### 1. MCP tool/data layer

Pattern: MCP provides a standard way for AI applications to connect to external systems such as files, databases, tools, and workflows.

Skill to add:

```text
mcp_connector_skill_generator
```

Operations value:

- Create typed connector contracts.
- Separate read-only data from write-capable tools.
- Maintain a tool allowlist.
- Store connector proof in `mcp_tool_registry.json`.

### 2. A2A agent syndication

Pattern: A2A is the agent-to-agent communication layer. MCP is the agent-to-tool layer. Together they support larger multi-agent systems.

Skill to add:

```text
a2a_agent_card_generator
```

Operations value:

- Generate Agent Cards for Player 2, Codex Builder, Claude Auditor, n8n Courier, Proof Sentinel, and Research Scout.
- Allow capability discovery without exposing internal memory or credentials.
- Store proof in `agent_cards/*.json`.

### 3. Managed agent runtime

Pattern: a production agent runtime needs tools, handoffs, guardrails, sessions, tracing, sandbox workspaces, and human review.

Skill to add:

```text
managed_agent_loop_skill
```

Operations value:

- Run multi-step work with traceable handoffs.
- Store session state.
- Add review gates for external writes.
- Store proof in `agent_trace_manifest.json`.

### 4. n8n workflow transport

Pattern: n8n is the workflow movement layer: triggers, nodes, credentials, workflow history, data transformation, and error handling.

Skill to add:

```text
n8n_workflow_blueprint_generator
```

Operations value:

- Turn approved data lanes into reusable workflow plans.
- Keep credentials outside the repo.
- Use normalize -> score -> store -> proof -> review -> dispatch.
- Store proof in `n8n_workflow_plan.json`.

### 5. Stateful long-running agents

Pattern: long-running operations need persistence, checkpoints, human review, and state graphs.

Skill to add:

```text
stateful_runtime_graph_skill
```

Operations value:

- Define durable task graphs.
- Resume from failure.
- Use checkpoints before risky actions.
- Store proof in `runtime_graph_state.json`.

### 6. Observability proof signals

Pattern: traces show request paths, metrics measure runtime activity, logs record events, and contextual data links related signals.

Skill to add:

```text
otel_signal_mapper_skill
```

Operations value:

- Give every task a trace id.
- Record duration, success, errors, and proof count.
- Keep sensitive content out of logs.
- Store proof in `otel_signal_map.json`.

### 7. Supply-chain attestation

Pattern: artifact attestations and SLSA-style provenance help connect source, build process, and generated artifacts.

Skill to add:

```text
attestation_gate_skill
```

Operations value:

- Hash generated scripts and packages.
- Track source commit, workflow run, and artifact digest.
- Prefer least-privilege CI permissions.
- Store proof in `artifact_attestation_manifest.json`.

### 8. Agentic safety gate

Pattern: agent systems need guardrails for prompt injection, sensitive data handling, supply-chain risk, output validation, excessive agency, and cost control.

Skill to add:

```text
agentic_safety_gate_skill
```

Operations value:

- Review untrusted issue, PR, and user-provided text before automation uses it.
- Require explicit review for external writes and deployments.
- Store decisions in `safety_gate_decisions.json`.

### 9. Data banking + skill fitness

Pattern: compounding happens when every task deposits reusable knowledge into memory and proof ledgers.

Skill to add:

```text
skill_fitness_bank_skill
```

Operations value:

- Score skills by reuse count, pass rate, time saved, risk avoided, revenue potential, and proof quality.
- Promote high-fitness skills into default routing.
- Retire low-fitness skills.
- Store proof in `skill_fitness_ledger.json`.

## Deployment order

```text
1. agentic_safety_gate_skill
2. mcp_connector_skill_generator
3. n8n_workflow_blueprint_generator
4. otel_signal_mapper_skill
5. attestation_gate_skill
6. skill_fitness_bank_skill
7. a2a_agent_card_generator
8. managed_agent_loop_skill
9. stateful_runtime_graph_skill
```

Reason: protect the bus first, expose tools second, move data third, observe/prove fourth, then scale agent syndication.

## AI agency syndication angle

Agency syndication means:

```text
one core skill factory
  -> many specialized agents
  -> many service packages
  -> one proof ledger
  -> reusable client operations
```

The productized packages become:

1. GitHub repo audit package.
2. n8n workflow intake package.
3. Local PC automation package.
4. Real estate operations package.
5. Legal evidence organization package.
6. Content signal extraction package.
7. Trading-research-to-operations scoring package.
8. Agentic safety gate package.
9. Proof and attestation package.

## Data banking angle

Create four ledgers:

```text
source_ledger = where intelligence came from
skill_ledger  = generated skills and tests
task_ledger   = runs, outcomes, failures, fixes
proof_ledger  = hashes, attestations, manifests, reviews
```

Without the data bank, every run is a one-off. With it, every run makes Player 2 more useful.

## Breakthrough summary

The breakthrough is not simply adding more agents. The breakthrough is making every agent action produce structured proof and reusable skill memory.

```text
source intelligence
  -> skill extraction
  -> operations skill
  -> deployment lane
  -> proof artifact
  -> learning feedback
  -> stronger next run
```
