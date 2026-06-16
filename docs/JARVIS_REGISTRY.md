# Jarvis Registry

This file is the durable project index for tools, repos, workflows, decisions, and next actions.

## Review Template

```text
Name:
URL:
Layer:
Purpose:
Install method:
Runs locally:
External dependency:
Required ports:
Risk notes:
First test:
Decision:
Reason:
```

## Layers

- Brain / orchestration
- Inference / local model
- Memory / vector store
- Automation / workflow
- Tools / interfaces
- Dashboard / observability
- Security / policy
- Data / database
- Domain module

## Decision Rules

Include now when the component is local-first, easy to test, documented, and directly useful.

Include later when the component is useful but not needed for the minimum stack.

Reject when the component is redundant, unclear, unsafe, unmaintained, or outside the architecture.
