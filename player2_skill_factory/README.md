# Player 2 Skill Factory

Player 2 Skill Factory turns the ARK95X repository stack into a segmented operations engine.

It is built around a simple pipeline:

```text
GitHub repos
  -> local repo mirror
  -> repo index
  -> SQLite backend
  -> model stack registry
  -> generated skills
  -> operations scoring
  -> Player 2 next-command routing
  -> proof manifest
```

## What this adds

### Core features

1. **Repository pull map**
   - Tracks priority repos such as `central-command-ops`, `flametrace-evolution-trading`, and `ark95x-unified-sovereign-stack`.
   - Converts repo metadata into skill candidates.

2. **Segmented skill generation**
   - Generates skills by segment:
     - command bus
     - GitHub intake
     - data backend
     - model stack
     - skill generator
     - trading research translation
     - operations scoring
     - Player 2 autopilot
     - proof gates
     - deployment

3. **Model-stack router**
   - Codex = build, patch, deploy, test.
   - Claude = audit, refactor, architecture, docs.
   - Ollama = local/private reasoning.
   - Hermes = symbolic strategy-to-system translation.
   - GitHub = source of truth and proof.

4. **Trading-algorithm pattern transfer**
   - Research-only.
   - Converts signal/backtest/fitness/drawdown/position-size concepts into operations scoring.
   - Does not place trades, manage funds, or provide financial advice.

5. **SQLite backend**
   - Stores repos, skills, model lanes, signals, tasks, and evidence references.

6. **Proof manifest**
   - Hashes generated outputs and records the state of the skill factory.

### Bonus features

- Offline/local-first fallback mode.
- Symbolic language compiler: "aura", "pulse", and "field" become context/state/scheduler/workspace objects.
- Stage-gate map for safe development.
- CI smoke test through GitHub Actions.
- One-file Python CLI so it can run on Windows, Linux, or inside containers.

## Quick start

From the repository root:

```bash
python player2_skill_factory/player2_factory.py init
python player2_skill_factory/player2_factory.py generate-skills
python player2_skill_factory/player2_factory.py score --intent "build next highest-value automation"
python player2_skill_factory/player2_factory.py proof
```

## Windows PowerShell

```powershell
python .\player2_skill_factory\player2_factory.py init
python .\player2_skill_factory\player2_factory.py generate-skills
python .\player2_skill_factory\player2_factory.py score --intent "build deployment lane"
python .\player2_skill_factory\player2_factory.py proof
```

## How it is done

The engine does not try to give every agent full control. It circuits the system through controlled lanes:

```text
Intent
  -> classify
  -> match skill
  -> score next move
  -> select model/tool lane
  -> write task
  -> generate proof
```

That is the correct build pattern: **many specialized skills, one controlled router, evidence after every stage**.

## Safety boundary

This is a local operations and development system. It does not include malware behavior, credential theft, unauthorized access, network flooding, firmware modification, security bypass, or live trading.
