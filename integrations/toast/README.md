# Toast puller (read-only baselines)

Pull **yesterday** and **today** sales + cash flow summaries from the Toast POS API, print a structured JSON report, and exit.

## Scope

- OAuth client-credentials login (`POST /authentication/v1/authentication/login`)
- Orders (read): `GET /orders/v2/ordersBulk?businessDate=yyyyMMdd`
- Cash (read): `GET /cashmgmt/v1/entries?businessDate=yyyyMMdd`
- Deposits (read): `GET /cashmgmt/v1/deposits?businessDate=yyyyMMdd`

## Hard exclusions

Do **not** build or wire from this package:

- inventory automation
- order adjustments / write endpoints
- bank sweeps / velocity banking
- Home Assistant, Frigate, Alexa
- Beekeeper / hive.db integration

## Environment

Copy placeholders from the repo `.env.example`:

| Variable | Required | Purpose |
|---|---|---|
| `TOAST_CLIENT_ID` | yes | Toast API client identifier |
| `TOAST_CLIENT_SECRET` | yes | Toast API client secret |
| `TOAST_API_HOSTNAME` | yes | Hostname from Toast (sandbox or production) |
| `TOAST_RESTAURANT_GUID` | yes | Restaurant GUID for `Toast-Restaurant-External-ID` |
| `TOAST_USER_ACCESS_TYPE` | no | Default `TOAST_MACHINE_CLIENT` |

Never commit real secrets.

## Commands

```bash
# Fail-closed health / dry-run (no network)
python -m integrations.toast health

# Health that still exits 0 when credentials are absent (CI-friendly dry report)
python -m integrations.toast health --allow-missing

# Live pull (requires credentials)
python -m integrations.toast pull

# Optional single/multi date override
python -m integrations.toast pull --business-date 20261121 --business-date 20261122
```

## Tests

```bash
python -m pytest -q tests/test_toast_puller.py
```

## Docs

- [Authentication](https://doc.toasttab.com/doc/devguide/authentication.html)
- [ordersBulk](https://doc.toasttab.com/openapi/orders/operation/ordersBulkGet/)
- [Cash entries](https://doc.toasttab.com/doc/devguide/apiUsingCashManagementApi.html)
- [Cash deposits](https://doc.toasttab.com/doc/devguide/apiGetCashDeposits.html)
- [Net sales calculation](https://doc.toasttab.com/doc/devguide/apiOrdersNetSalesCalculation.html)
