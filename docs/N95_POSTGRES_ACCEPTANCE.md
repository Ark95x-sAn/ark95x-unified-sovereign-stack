# PostgreSQL acceptance plan

Status: PREPARED. No host runtime test has run.
Source base: c153e0a66329673bb44c5203c0b54911c9905fe3.
Scope: existing Core PostgreSQL authority; no replacement mission queue.

## Configuration correction

The root Compose file parsed as YAML but gave Core a null ports field and a malformed env_file scalar. The review branch corrects those fields, requires POSTGRES_PASSWORD at all three existing database references, and binds the PostgreSQL host port to 127.0.0.1.

Local Python/PyYAML checks reproduced the original field defects and verified the corrected structure, password references and loopback binding. These checks are not Docker Compose validation.

The existing URL connection format requires URL-safe password characters or explicit percent encoding. Existing PostgreSQL volume credentials do not change when POSTGRES_PASSWORD changes. Other services' defaults remain outside this patch.

## Before runtime

- Record the actual host, checkout commit, Docker/Compose versions, selected PostgreSQL image digest and target data volume.
- Verify the controlling 52 GiB (55,834,574,848 bytes) free-space floor and additional test/backup headroom on the actual workspace/data volumes.
- Use a private environment file with no credentials in version control or receipts.
- Run docker compose config --quiet locally. Record exit status without printing rendered credentials.
- Define a separate test project/container, a new empty test data volume and a separate restore database. Never reuse production volumes or containers for the restart test.
- Launch only the isolated PostgreSQL test service after reviewing that isolated configuration; do not launch the full root stack.
- Keep Defender, Firewall, account access and existing services unchanged.

## Tests and required evidence

| Test | Action | Acceptance |
| --- | --- | --- |
| Connection | Authenticate with the intended test role | Correct database/user identity; server readiness alone is insufficient |
| Write/read | Commit a non-sensitive fixture record and read by its exact ID | All fixture fields match; record readback digest |
| Atomicity | Force an error within a multi-write transaction | No partial record set persists |
| Replay | Repeat the same request, then reuse its key with conflicting data | Existing Core idempotency behavior is preserved; conflicting replay rejects |
| Role denial | Attempt a prohibited operation using the worker test role | Denied without changing data |
| Restart | Restart only the isolated PostgreSQL container, retaining its test volume | Reconnect and reproduce committed fixture fields/digest |
| Backup/restore | Use the selected version's supported pg_dump/pg_restore procedure; restore into a different empty database | Restore exits successfully; fixture row counts, fields and digest match |
| Failure reporting | Exercise a missing record and disconnected backend | Not-found and failure remain distinct from success |

The fixture schema is not a production Core migration. Map current Core engine/schema and transaction contracts before claiming C1 completion. A backup file existing is not restore proof; service health is not persistence proof. Role provisioning and grants must be reviewed for the actual test instance.

## One receipt

Capture commit, actual host, image digest, database/schema identity, role names (no credentials), exact sanitized commands, exit codes, timestamps, comparison results and artifact digests.
Each test is PASS, FAIL or NOT_RUN. Preserve raw error evidence. Do not map a Linux fixture or hosted runner to a Windows physical-host pass.

Current results:
- Local structure checks: PASS.
- Docker Compose validation: NOT_RUN.
- Database connection, transactions, roles, restart and restore: NOT_RUN.
- Physical deployment, Core C1/C2 acceptance and ROI: NOT_VERIFIED.

Runtime blocker here: Docker and PostgreSQL executables are unavailable in this execution workspace.
Next action: run quiet Compose validation and isolated PostgreSQL acceptance through an authenticated intended-host session. Review evidence before merge/deployment claims.
