# Sintra business-context handoff

This increment adds an offline credit planner and reusable handoff templates to the existing Network-95 stack. It does not add a mission controller, connector, listener, model call, or background task.

## Placement

| Component | Jarvis layer | Responsibility |
|---|---|---|
| Existing Core | Brain / orchestration | Current mission and accepted state |
| Sintra Brain AI | Memory | Explicitly curated business knowledge |
| Sintra Helper | Hosted tools / domain | One bounded artifact returned for review |
| Offline planner | Tools / interfaces | Calculate an envelope from supplied usage |
| Optional Grok | Hosted tools / research | Dated public sources and counterarguments |

Sintra's [integration documentation](https://help.sintra.ai/en/articles/12929400-integrations-explained) says it has no public API. The bridge starts with native knowledge import and a returned artifact. It supplies no invented HTTP adapter. A connected application is not evidence of live Brain synchronization; use the [knowledge-management rules](https://help.sintra.ai/en/articles/11758256-how-to-manage-knowledge-in-the-brain-ai).

## First run

1. Fill `templates/sintra_business_context.md` with the minimum ordinary business facts needed for one task. Keep private records in separately authorized workflows.
2. Read the intended workspace's actual balance and billing reset from Usage & Billing.
3. Load the standalone Markdown in Brain AI → All Knowledge. Confirm its revision and native item location.
4. Give one available Helper a bounded task. Require an accurate context readback, complete artifact, sources, assumptions, and usage receipt. Save its return in the existing Core workflow after review.
5. Reconcile all native usage before assigning another task. A later knowledge update requires its own save and retrieval check.

No native action was performed by the planner. A prepared context file, parsed JSON return, or passing local test is not proof of account import, inter-device delivery, or a commercial outcome.

## Credit planning

The current ceiling is 20 credits per day. The [published standard plan](https://help.sintra.ai/en/articles/9607367-plans-and-pricing) lists a monthly allowance; the authenticated account supplies its actual entitlement. The [credit guide](https://help.sintra.ai/en/articles/12606676-workspace-credits) explains variable task usage. Native charges can exceed a prompt estimate.

```sh
python tools/sintra_credit_gate.py --balance 250 --days 30 --spent-today 0 --reserve 25 --next-task 5
```

The numbers above are a hypothetical example. It reports a 7.5-credit envelope. `--balance` is current after today's charges, `--spent-today` includes all charged workspace activity, and `--pending` covers uncharged committed work. Count the current day in `--days`. Omitted balance, days, or today's usage returns HOLD. A supplied task estimate can fit or exceed the calculated envelope; it is never an authorization or a platform-enforced cap.

The planner reconstructs the start-of-day pool as `balance + spent_today`, paces the non-reserved credits across the remaining days, and subtracts today's use and pending work. It also applies the 20-credit ceiling and remaining pool. Result states are `HOLD`, `BUDGET_ONLY`, and `FITS_ESTIMATE`.

## Optional research return

Use one public question in an existing Grok interface if available. Require the observation/publication date, source URL, claim, contrary evidence, uncertainty, and a falsification test. A source-backed finding enters Core only after review. [xAI documents API X Search](https://docs.x.ai/developers/tools/x-search), but any later API calls require a separately configured budget; Sintra credits are unrelated. This increment contains no Grok client or API key handling.

## Verification

```sh
python -m unittest discover -s tests -p test_sintra_credit_gate.py -v
```

Twelve focused tests cover missing inputs, monthly pacing, ceiling, spent/pending usage, reserve, task estimates, invalid values, and CLI behavior. The dedicated `sintra-planning.yml` workflow preserves test failures and uses no application credentials. It runs only the isolated planner checks, independently of the historical generic CI command that masks pytest failures. A hosted result proves that runner's test outcome, not deployment on GM700/RTX/Surface.

Source review: official Sintra and xAI documents on 2026-10-05; repository base `092918af13c9e0270b63e7482dd6490f30dce9cf`. Local planner requires only Python's standard library and opens no network ports. Code follows this repository's license. Hosted platform terms and access remain separate. No service deployment or installation is required to use the planner.

