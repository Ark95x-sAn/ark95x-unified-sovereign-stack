# Native receipt bridge 0.1.0

This is an isolated, Python 3.11+ standard-library telemetry transport and SQLite
evidence spool. The canonical Network-95 Core 1.4.0 remains mission authority.
The bridge does not replace it, register verified Core nodes, run models, install
updates, execute commands, change money, send messages, or ingest medical data.
Any Core handoff adapter is separately documented and requires its own validation.

The three allowlisted labels are GM700, RTX2080 and SURFACE. Each gets a different
HMAC-SHA256 key. A configured label starts unknown/offline. Only an accepted,
unexpired signed receipt makes it online in the **telemetry** sense. A node label
and HMAC establish possession of that label's secret, not hardware identity,
physical presence, honest sensor data, or proof the claimed producer ran.
Every status includes `observed_at` and per-node `source_time`/`expires_at`.
Saved status and draft exports are historical snapshots; their eligibility must
never be reused as live authorization. Re-read live status before a new decision.

## Run locally

Run from the repository root. Place secret state outside every git checkout.
On Windows, substitute an absolute private directory under your user profile.

```bash
python -m n95_native init --state /tmp/n95-private-state
python -m n95_native serve --state /tmp/n95-private-state --port 8795
```

From another terminal:

```bash
python -m n95_native pulse --state /tmp/n95-private-state --node GM700 --url http://127.0.0.1:8795
python -m n95_native status --state /tmp/n95-private-state
python -m n95_native audit --state /tmp/n95-private-state
python -m n95_native watch --state /tmp/n95-private-state --node GM700 --cycles 3 --interval 30
python -m unittest discover -s tests -p test_native_bridge.py -v
```

Use a fresh directory for a reproducible synthetic three-identity demonstration:

```bash
python -m n95_native demo --state /tmp/n95-demo-state
```

The demo makes three actual HTTP POSTs to an ephemeral loopback port and commits
three SQLite receipts. Its output marks every receipt `synthetic: true` and
`physical_three_device_deployment: false`. It proves transport integration on one
host only. It does not claim access to the user's Windows devices.

`watch` sends fresh signed telemetry for a finite number of cycles (1–120), with
1–300 seconds between attempts. Defaults are three cycles and 30 seconds. Three
consecutive failures open the circuit and end the loop. Ctrl+C stops it. The
completion report distinguishes attempted cycles, accepted receipts and failures.
Any failed attempt or interrupted/incomplete run gives the CLI a nonzero exit code.
It does not install a background service or promise continued operation after exit.

The separate handoff adapter can prepare a digest-bound draft and validate it
against an explicitly supplied existing Core checkout:

```bash
python -m n95_native.core_handoff --state /tmp/n95-private-state --output-dir /tmp/n95-draft-export --core-root /path/to/existing/Network95_Core
```

This is draft export only; it does not submit a mission or execute Core actions.

## State and transport boundary

`init` refuses a nonempty directory and a directory within any git checkout. It
creates `config.json`, `reader.key`, `nodes/GM700.key`, `nodes/RTX2080.key`,
`nodes/SURFACE.key`, and `evidence.sqlite3`. Secrets are generated from the OS
random source and are never printed. POSIX permissions are owner-only; Windows
requires an owner-only ACL supplied by the Windows installer because Python
`chmod` does not establish equivalent Windows ACL isolation. Keep this state out
of sync folders and repositories. No key rotation/provisioning API is included.

The core host needs all verification keys. A producer requires only its own
`nodes/<NODE>.key` under its private state directory. Never copy the full core
state directory to a producer. Securely provision one key per device. Producers
need the identical `n95_native` code revision; a code update requires an explicit
review of configured producer digests. No capabilities are self-registered.

The server binds only `127.0.0.1`; the client accepts only a literal IPv4 loopback
HTTP URL, rejects every HTTP redirect and disables proxy inheritance. Reader
tokens therefore cannot follow a redirect to another endpoint. Actual remote devices need an explicitly
provisioned encrypted tunnel mapping their loopback port to the core's loopback
port. Tailscale alone does not turn a loopback listener into a remote listener.
This package does not set up that transport or certify a three-device deployment.
Do not open this server directly to a LAN or the internet. It has a small,
single-threaded request queue, a three-second socket timeout and 16 KiB body cap;
it is not a hardened public server.

`GET /health` exposes only service liveness. `GET /status` requires
`Authorization: Bearer <reader.key>`. `POST /event` requires a valid node HMAC.
Requests require the literal loopback Host/port and reject browser Origin and
Sec-Fetch-Site headers. There are no CORS permissions, browser writes, or cookie
authentication. Generic errors contain no keys, payloads, or filesystem paths.
Expired signed events are rejected, including old retries. A current, identical
authenticated retry returns its original receipt. A conflicting event ID or
reused node nonce is rejected. Producer clocks must be synchronized: permitted
future skew is 15 seconds, maximum event lifetime is 90 seconds.

## Accepted data and routing

Kinds are exactly `heartbeat` and `system_health`. Both use exactly these bounded
metadata fields: `producer_sha256`, `os`, `python`, `cpu_count`, `synthetic`.
Here `system_health` means computer metadata, never human health. Wearable,
medical, app content, location, free text, nested sensor objects, arbitrary
commands and inferred health information are rejected.

`Store.route("telemetry")` selects the most recent eligible node. Eligibility
requires a fresh signed receipt **and** an existing local bridge source artifact
whose SHA256 matches the configured revision and signed producer digest. Other
capabilities return `blocked` until real adapters and validation are implemented.
The route result is a suggestion (`executed: false`); it dispatches nothing.

Evidence coverage has six required checks: two per configured node. The checks
are (1) a fresh authenticated receipt and (2) an existing local artifact with a
matching signed revision. Output exposes numerator, denominator, and each check.
An older artifact match may remain true after receipt freshness expires. A 100%
demo result means six telemetry checks passed for synthetic identities; it is
not a truth score, security guarantee, health score, business readiness score,
or proof of physical deployment. Synthetic status remains visible in routing.

## Audit scope and limitations

Each accepted event stores canonical JSON, source time/expiry, nonce, receipt
time, sequential number, previous hash and a SHA256 hash of that entire record.
Node signatures are verified before idempotency lookup and again during audit.
SQLite `BEGIN IMMEDIATE` serializes writers; transactions use `synchronous=FULL`.
Status audits and node lookups share one read transaction snapshot, including
when another connection appends concurrently.
The store checks its existing chain before accepting another event and on
restart. Accepted records are durable subject to filesystem/hardware guarantees.
Rejected HTTP requests are not stored as evidence and are not logged with their
payloads. No retention or automatic pruning is enabled.

The chain detects record modification, internal deletion, sequence breaks and
signature corruption against the current keys. It is **tamper-evident, not
tamperproof**. A privileged owner who replaces the database/config/keys, or can
rewrite authenticated records and recompute hashes, can forge history. Tail
deletion, a restored older database, total database replacement and rollback
cannot be reliably detected without an independently retained signed checkpoint.
Keep exported audit-head evidence outside the writer's control before making
stronger integrity claims. Source timestamps and system metadata remain signed
producer assertions, not independent measurements.

This release contains no daemon installer, indefinite pulse scheduler, adaptive
self-modification, external health connectors, Core release adapter, or remote
control shell. Tests verify the defined transport boundary, not those future
capabilities.
