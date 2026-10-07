# Network-95 command prototype

This module routes requests and records local outcomes. Its default Manus,
ZenCode and VibeCoder implementations have no execution adapters. Their tool
and skill lists are a capability catalogue, not proof of installed or running
tools. Running a preset does not research, build, deploy or review its subject.

## Current interfaces

| Interface | Implemented behavior | Execution limit |
|---|---|---|
| `unified_crew.py` | Synchronous role dispatch and in-memory outcome records | Default agents return `not_implemented`; custom output remains unverified |
| `dispatcher.py` | Stable priority ordering, per-task history and hooks | Batch dispatch is sequential; records are not durable Core mission state |
| `agents/` | Asynchronous local agent calls and ordered batch outcomes | Default handlers are placeholders; no verified completion is issued |
| `protocol_router.py` | Local MCP action-handler invocation and outcome logging | Agent cards do not send requests; A2A and ACP transports are unimplemented |
| `command_center_api.py` | Prototype HTTP access to the asynchronous objects | Authentication and target admission remain separate work; do not expose it as an authorized worker |

The synchronous crew and asynchronous registry are separate existing code paths.
They share the rule that a local worker report cannot verify itself. Neither
replaces the [existing Core authority](../docs/N95_INTEGRATION.md).

## Outcome contract

| Outcome | Meaning |
|---|---|
| `not_implemented` | The requested default adapter is absent; no work was executed |
| `blocked` | The request or worker selection cannot be admitted |
| `failed` | Invocation failed or returned an invalid result; possible effects stay uncertain |
| `reported` | A local handler returned a claimed result; independent verification has not occurred |
| `empty` | An asynchronous batch contained no tasks |
| `partial` | A reported or partial result is mixed with other outcomes; inspect each record |

Command results retain `verified: false`. `executed: null` represents an unknown
execution outcome, including a custom handler report or exception. It must not
be treated as `false` or as success. Default placeholders use `executed: false`.
The asynchronous batch returns one indexed record per input in input order;
invalid and unknown-agent requests remain visible. Success claims from custom
handlers remain local reports, even when they contain their own verification
field. Manus does not automatically retry an uncertain attempt.

The asynchronous registry snapshots finite, plain JSON. It rejects non-string
object keys, more than 32 levels of nesting, more than 10,000 visited values
(including keys), and more than 1,048,576 characters of text or serialized ASCII
JSON per snapshot. Invalid input remains an indexed blocked record; invalid
handler output becomes a serializable failure without retaining raw objects.

The router uses `local_handler_returned` for a registered MCP callback and keeps
its output under `handler_result`. That is not network delivery. Its envelope
retains `delivered: false` and `transport_verified: false`; missing adapters and
handler failures remain explicit. Cancellation is recorded and propagated.

## Inspect a preset locally

From the repository root, using Python 3.11 or newer:

```sh
python -m command.run_crew --mode quick --quiet
```

The command prints a JSON outcome summary and exits with **code 2** because the
preset has no bound executor or verifier. A normal quick run contains three
`not_implemented` outcomes and zero verified tasks. `--quiet` suppresses the
banner. `--fury` is existing request metadata; it does not grant authority,
enable tools or establish parallel execution.

Programmatic callers retain the synchronous string-return interface:

```python
from command.dispatcher import Dispatcher, DispatchRequest
from command.unified_crew import UnifiedCrew

dispatcher = Dispatcher(crew=UnifiedCrew(), fury=False)
dispatcher.batch_route([
    DispatchRequest("Prepare a brief from approved example documents", "research"),
    DispatchRequest("Review the example implementation", "code"),
])
print(dispatcher.summary())
print(dispatcher.history)
```

History retains the original request, task status, full result text, execution
uncertainty and the verification boundary. Callback exceptions are recorded in
`hook_errors`; they do not retry a task or erase later batch requests. Unknown
categories remain blocked. The shared in-memory records retain outcome labels;
placeholder text must not be ingested as completed work or learned evidence.

## Verify the contracts

The focused tests use only Python's standard library, fake local handlers and
temporary test state. They make no model or device calls:

```sh
python -m unittest discover -s tests -p 'test_command_*outcomes.py' -v
```

These tests establish the local result contract. A physical worker still needs
authenticated identity, scoped authority, durable Core state, a real execution
receipt and independent acceptance through the existing integration sequence.
See the [Jarvis Registry](../docs/JARVIS_REGISTRY.md) for this repair's exact
verification scope and remaining work.
