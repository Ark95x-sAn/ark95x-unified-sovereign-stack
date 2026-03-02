# ARK95X DAILY SYNC PROTOCOL
## Infinity Loop Bootstrap Command - Send to ALL Agents at Session Start

---

## THE MASTER PROMPT (Copy & Send to Every AI Agent Session)

```
You are resuming work on the ARK95X Unified Sovereign Stack.

REPO: https://github.com/Ark95x-sAn/ark95x-unified-sovereign-stack
OWNER: Ark95x-sAn | Network-95 LLC | Leland, Iowa
DATE: [TODAY'S DATE]
SESSION TYPE: Deep Long Session - Handoff & Finish Through

--- SYNC PROTOCOL ---

1. READ SESSION_STATE.md in the repo for current progress
2. READ the open GitHub Issues to see what's pending
3. CHECK the last commit history to see what was done
4. PICK UP where the last session left off - no restarts
5. BUILD on top of what exists - never overwrite progress

--- RULES ---

- NO INFINITY LOOPS: If you detect repeated work or circular patterns, STOP and move to the next task
- HANDOFF PROTOCOL: Before session ends, update SESSION_STATE.md with exactly where you stopped
- TEST EVERYTHING: After building, verify imports work and files are valid
- TRAIN EACH SYSTEM: Each module should have a working test that proves it loads
- CLOSE ISSUES: When a migration task is done, close the GitHub issue
- COMMIT OFTEN: Small commits > big commits. Push after each module

--- CURRENT PRIORITIES ---

PHASE 1 - Code Migration (Issues #1-14):
Migrate actual source code from each original repo into unified stack modules.
For each module: copy core files, update imports, verify module loads.

PHASE 2 - Integration Testing:
Run main.py --check to verify all 14 modules import cleanly.
Fix any circular imports or dependency conflicts.

PHASE 3 - Daily Merge & Upgrade:
Pull latest from all source repos, merge improvements into unified stack.
Update SESSION_STATE.md with progress.
Drop updates to Notion project board.

--- DATA EXCHANGE FORMAT ---

When handing off between agents/sessions, include:
- COMPLETED: [list of tasks finished]
- BLOCKED: [list of blockers or stalled scripts]
- NEXT: [exact next step for the next session]
- COMMIT_HASH: [last commit made]
- MODULES_TESTED: [which modules pass import test]

--- FORBIDDEN PATTERNS (Break These Loops) ---

- Re-creating files that already exist
- Re-reading the same page more than twice
- Starting over from scratch when progress exists
- Asking for confirmation on pre-approved actions
- Getting stuck on browser extension interference (use Tab+Enter pattern)

--- MEMORY SYNC ---

This project uses persistent memory across sessions.
Key facts: 17 repos merged into 14 module directories.
Stack: Python/TS, CrewAI, LangChain, FastAPI, Docker, n8n.
Location: Leland, Iowa. Entities: Network-95 LLC, Nordskog Properties LLC.
The user works late sessions (1-4 AM CST) and prefers autonomous execution.
```

---

## HOW TO USE THIS PROMPT

1. **Start of every AI session** (ChatGPT, Claude, Perplexity Comet, Grok, Ollama):
   - Paste the Master Prompt above
   - The agent reads SESSION_STATE.md and picks up where the last one left off

2. **End of every session**:
   - Agent updates SESSION_STATE.md with handoff data
   - Agent closes any completed GitHub issues
   - Agent commits all work

3. **Daily Cycle**:
   - Morning: Agent reads state, migrates next module
   - Afternoon: Integration testing across modules
   - Night: Merge upgrades, update Notion, prepare next day's handoff

---

## PLATFORM-SPECIFIC NOTES

| Platform | Best For | Session Command |
|----------|----------|----------------|
| Perplexity Comet | Browser ops, GitHub file creation, issue management | Full Master Prompt |
| ChatGPT | Code generation, module logic, test writing | Master Prompt + paste source repo code |
| Claude | Architecture review, refactoring, documentation | Master Prompt + ask for code review |
| Grok | Quick lookups, API research, debugging | Master Prompt + specific error |
| Ollama (local) | Private code processing, bulk transforms | Master Prompt + local file paths |
