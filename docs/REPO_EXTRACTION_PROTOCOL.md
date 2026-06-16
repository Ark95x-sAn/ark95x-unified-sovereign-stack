# Repository Review Protocol

## Purpose
Every candidate software project must be reviewed before it is added to Jarvis.

## Required Fields

- Name
- URL
- Source observed
- Plain-English purpose
- Jarvis layer
- Install method
- Container support
- Local capability
- Hosted service requirement
- Network ports
- Configuration values
- Data stored
- Files changed
- Maintenance signal
- License
- Risk label
- First safe test
- Decision: include now, include later, or reject
- Notes

## Jarvis Layers

- Brain: agent orchestration, planning, routing
- Inference: local model serving
- Memory: vector store, recall, context, RAG
- Automation: workflows and triggers
- Tools: approved integrations and local actions
- Dashboard: command center and reports
- Security: configuration review and policy
- Data: databases, queues, streams, storage
- Domain: real estate, finance, or research modules

## Decision Rules

Use now only if the candidate supports the current build phase, can be tested safely, maps to a Jarvis layer, has clear setup instructions, does not require exposed secrets, and supports a local or container-based setup path.

Use later if it is useful but not needed yet.

Reject if it is redundant, unclear, not maintained, unsafe for the current environment, or unrelated to the Jarvis architecture.

## Final Review Format

Decision:
Reason:
Next move:
Registry update required: yes or no
