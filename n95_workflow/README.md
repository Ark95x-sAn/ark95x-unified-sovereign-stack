# Local source-linked operational brief

This finite, dependency-free Python 3.11+ workflow reads a selected local notes
folder and produces an extractive operational brief. It uses deterministic rules;
it does not invoke an AI model, understand arbitrary notes, verify source claims,
run source instructions, send information, or run in the background.

## Run

From the repository root, with an installed Python 3.11+ interpreter:

```bash
python -m n95_workflow run --input /path/to/selected-notes --output /path/to/private-briefs --as-of 2026-09-06
```

Use explicit, disjoint input and output directories. Output must be outside every
git checkout. On Windows, use absolute local paths and the documented Windows
wrapper if desired. UNC/device-prefixed paths are rejected; the direct Python
entry point also rejects Windows remote mapped drives and unknown drive types.
No install step, package download or internet access is used
by this module. The module itself does not select a customer folder or grant
access to any device.

The selected folder must contain **1–50 regular `.txt`/`.md` files**, UTF-8 encoded,
with **at most 1 MiB of combined input bytes and 10,000 checkbox observations**.
Any nested folder, unsupported file type, symlink, Windows reparse point, special
file, malformed UTF-8, excessive count or size fails the whole run. Originals
are read-only. Keep unrelated files outside the selected folder.

Explicit checkbox examples:

```text
- [ ] Review supplier quote [id:JOB1] [due:2026-09-08] [owner:Ben]
- [x] Confirmed meeting [id:JOB2]
```

Accepted checkbox bullets are `-`, `*` and `+`, with zero to three leading spaces.
`[ ]` is open; `[x]`/`[X]` is completed context. Checkbox examples inside Markdown
fenced blocks or indented code are not extracted as tasks. This is a deliberately
limited line parser, not a full Markdown document interpreter. It does not parse
tables, prose commitments, HTML semantics, inline tasks or natural-language dates.

Optional field names are exactly `[id:...]`, `[due:YYYY-MM-DD]` and `[owner:...]`.
IDs contain 1–64 ASCII letters/digits/underscores/hyphens; owners are nonblank and
at most 80 characters. Invalid or repeated fields remain in exact quotes and
produce warnings; dates are not guessed. Only an explicit ID can group separate
occurrences. Identical text without an ID remains separate source occurrences,
because text alone does not establish task identity.

Different states, due dates, owners, or metadata-stripped task text for the same
ID are surfaced as conflicts. All observations remain available; the workflow
does not choose a winner. Missing fields mean unspecified, not disagreement.
Completed observations remain context. Overdue/today/upcoming labels compare
valid explicit due dates with the exact `--as-of` date supplied by the operator.

`--context-lines 0`, `1`, `2` or `3` selects at most that many initial non-task
lines per file, each capped at 240 characters. Default is one. Truncation is
explicit. These excerpts do not constitute a summary of the file.

## Outputs and repeated runs

A successful run prints JSON containing `content_id`, `output_directory` and
`reused`. The output directory is `<output>/<64-character-content-id>/`, with:

- `brief.md`: open work, completed context, conflicts, bounded excerpts and source inventory.
- `observations.json`: exact checkbox-line quotes, parsed fields, warnings and source references.
- `manifest.json`: source metadata, workflow revision, completion state and output hashes.

Each observation identifies the original filename, one-based line number and
SHA256 of the full original source bytes. Line numbers count LF-separated lines;
a CR immediately before LF is treated as a line ending. Brief source links go to
its inventory, where the filename and full source hash can be checked against the
selected originals. Source files are not copied into the output.

All source text in the brief is rendered as inert fenced text, including image,
HTML and link syntax. Control/bidi characters are rendered as visible escapes;
exact checkbox quotes remain in JSON. The generated Markdown links contain only
controlled source IDs, never source-supplied URLs.

The content ID binds source names/hashes/sizes, explicit as-of date, context
option, workflow version and implementation hash. An unchanged rerun verifies
all three expected output files byte-for-byte and reuses them. Modified output
is rejected without replacement. A changed input, as-of date, option or code
revision creates a new ID and retains the previous completed directory.

All inputs are preflighted and read before output creation. File identity,
timestamps, directory membership and bytes are checked again before publication.
Files are flushed in a temporary sibling directory, then a completed directory
is published by one rename. Detected source changes and handled write failures
leave no new completed directory; staging is removed. The output parent may
remain empty after a failed run.

## Stop and reset

The command exits when its one batch finishes. There is no watcher or service to
stop. Ctrl+C interrupts the batch and cleans its staging directory; rerun the
same command after fixing the cause. Exit codes are 0 for new/verified output,
1 for a workflow/filesystem failure, 2 for invalid command-line syntax, and 130
for Ctrl+C.

For a clean trial, choose a new empty output folder. The workflow has no reset or
delete command. If a machine crash leaves a `.n95-pending-*` directory, first
ensure no run is active, then remove only that abandoned staging directory using
normal file management. Completed outputs and originals need not be deleted.

## Trust boundary and proof

Use directories controlled by the operator and keep them stable while a batch
runs. Pre/post checks reject detected replacement or mutation; they are not a
portable sandbox against a privileged hostile process racing directory ancestry.
On non-Windows systems the operator must select a local filesystem; this small
module does not discover the backing transport of arbitrary OS-mounted filesystems.
Filesystem crash durability and device-specific Windows behavior require their
own environment checks. Local filesystem permissions protect the generated
customer data; do not publish private output merely because the code is public.

The workflow is a usable local extractor, not proof of a profitable service,
time saved, native three-device deployment, model integration, or autonomous
operations. Those claims need separate observed results.

Run its behavioral and adversarial checks:

```bash
python -m unittest discover -s tests -p test_workflow.py -v
```
