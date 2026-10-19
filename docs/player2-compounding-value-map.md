# Player 2 Compounding Value Map

## Highest-value compounding asset

The highest compounding value is not one model, one repo, one trading engine, one gaming engine, or one automation.

The highest-value asset is the **closed learning loop**:

```text
GitHub source
  -> n8n data lanes
  -> SQLite memory/backend
  -> skill generator
  -> operations scoring
  -> Codex/Claude execution lanes
  -> proof manifest
  -> bug/task feedback
  -> stronger next skill
```

That is the flywheel. Every run should create more reusable system intelligence.

## Compounding value stack

| Rank | Asset | Why it compounds | Build priority |
|---:|---|---|---:|
| 1 | Skill Factory | Converts repos, prompts, bugs, workflows, and tasks into reusable capabilities | 100 |
| 2 | Data Backend | Stores memory, signals, skills, tasks, evidence, and run history | 98 |
| 3 | n8n 7 Data Ops | Feeds Player 2 with scheduled, normalized, approved data | 96 |
| 4 | Proof Manifests | Turns work into verifiable evidence and trust | 94 |
| 5 | Operations Scoring | Ranks what matters next instead of reacting randomly | 92 |
| 6 | Codex Build Lane | Converts plans into scripts, tests, patches, and deployable code | 90 |
| 7 | Claude Audit Lane | Prevents drift by reviewing architecture, safety, and weak points | 88 |
| 8 | Local Model Lane | Keeps local reasoning available when cloud/API access is down | 84 |
| 9 | Gaming/GPU Compute Lane | Adds horsepower for local models, simulation, rendering, and testing | 80 |
| 10 | Trading Research Transfer | Converts signal/backtest/fitness logic into operations scoring only | 76 |

## The core compounding formula

```text
compound_value = reusable_output * feedback_rate * proof_quality * deployment_speed
                 - risk_drag - context_switch_cost - broken_tool_penalty
```

The system wins when every task creates at least one reusable asset:

- a skill file,
- a script,
- a config,
- a test,
- a proof record,
- a workflow plan,
- a bug pattern,
- a next-action score.

## What to build first

### 1. Stabilize the Skill Factory

The Skill Factory is the multiplier. It turns every repo and workflow into more capability.

Command:

```bash
python player2_skill_factory/player2_factory.py init
python player2_skill_factory/player2_factory.py generate-skills
python player2_skill_factory/player2_factory.py score --intent "build next highest-value automation"
python player2_skill_factory/player2_factory.py proof
```

### 2. Build the n8n GitHub intake workflow

This is the first n8n lane because GitHub is the cleanest source of truth.

Command:

```bash
python player2_skill_factory/n8n_plan.py first
```

### 3. Add local PC inventory

This lets Player 2 route workloads based on the machine, not guessing.

Data to capture:

- CPU
- GPU
- RAM
- disk
- installed shells
- installed AI tools
- running local services
- available ports

### 4. Turn logs into bug-pattern memory

Every failure should become structured data.

```text
error -> bug pattern -> fix task -> Codex patch -> retest -> proof
```

### 5. Keep trading research as pattern transfer only

Trading logic is useful as an operations metaphor:

```text
signal         -> trigger
backtest       -> historical review
fitness score  -> task value score
drawdown       -> time/money/energy loss
position size  -> effort size
allocation     -> project allocation
MAP-Elites     -> many skill variants, keep best by niche
```

No live trading. No financial advice. No order execution.

## Highest-value next PR after this one

Create a new PR called:

```text
player2-runtime-loop
```

It should add:

1. `player2_skill_factory/runtime_loop.py`
2. `player2_skill_factory/pc_inventory.py`
3. `player2_skill_factory/log_ingest.py`
4. `player2_skill_factory/task_queue.py`
5. `player2_skill_factory/skill_fitness.py`
6. CI tests for all of the above

## North-star result

The end state is a self-improving local operations engine:

```text
I give intent once.
Player 2 finds the best lane.
Codex builds.
Claude audits.
n8n feeds data.
GitHub stores truth.
Proof records what happened.
The next run gets smarter.
```

That is the actual compounding engine.
