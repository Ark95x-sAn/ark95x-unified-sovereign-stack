"""CLI entrypoint: health (fail-closed) or pull yesterday/today baselines."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import List, Optional, Sequence

from .client import ToastApiError, ToastClient
from .config import ConfigError, ToastConfig, missing_credentials
from .report import (
    DailyBaselineReport,
    business_dates_yesterday_and_today,
    mask_guid,
    summarize_cash,
    summarize_sales,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m integrations.toast",
        description=(
            "Read-only Toast POS puller for daily sales + cash flow baselines. "
            "Reports what came back, then exits. No writes, no Beekeeper, "
            "no inventory/bank/HA wiring."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    health = sub.add_parser(
        "health",
        help="Dry-run / fail-closed credential check without calling Toast.",
    )
    health.add_argument(
        "--require-credentials",
        action="store_true",
        help="Exit non-zero if required env vars are missing (default).",
    )
    health.add_argument(
        "--allow-missing",
        action="store_true",
        help="Exit zero even when credentials are missing (still report).",
    )

    pull = sub.add_parser(
        "pull",
        help="Authenticate and pull yesterday + today sales/cash summaries.",
    )
    pull.add_argument(
        "--business-date",
        action="append",
        dest="business_dates",
        metavar="YYYYMMDD",
        help="Override dates (repeatable). Default: yesterday and today (UTC).",
    )
    pull.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON report (default).",
    )
    return parser


def cmd_health(allow_missing: bool = False) -> int:
    missing = missing_credentials()
    report = {
        "ok": not missing or allow_missing,
        "mode": "health",
        "network": False,
        "required_env": [
            "TOAST_CLIENT_ID",
            "TOAST_CLIENT_SECRET",
            "TOAST_API_HOSTNAME",
            "TOAST_RESTAURANT_GUID",
        ],
        "optional_env": ["TOAST_USER_ACCESS_TYPE"],
        "missing": missing,
        "message": (
            "Credentials present; live pull not attempted in health mode."
            if not missing
            else "Credentials missing — fail-closed. Set env from .env.example."
        ),
        "test_commands": {
            "health": "python -m integrations.toast health",
            "pull": "python -m integrations.toast pull",
            "pytest": "python -m pytest -q tests/test_toast_puller.py",
        },
        "docs": [
            "https://doc.toasttab.com/doc/devguide/authentication.html",
            "https://doc.toasttab.com/openapi/orders/operation/ordersBulkGet/",
            "https://doc.toasttab.com/openapi/cashmanagement/operation/entriesGet/",
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if missing and not allow_missing:
        return 2
    return 0


def cmd_pull(business_dates: Optional[Sequence[str]] = None) -> int:
    try:
        config = ToastConfig.from_env()
    except ConfigError as exc:
        report = DailyBaselineReport(
            generated_at=_now_iso(),
            restaurant_guid_masked="unset",
            mode="pull",
            error=str(exc),
        )
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 2

    dates = list(business_dates) if business_dates else business_dates_yesterday_and_today()
    report = DailyBaselineReport(
        generated_at=_now_iso(),
        restaurant_guid_masked=mask_guid(config.restaurant_guid),
        mode="pull",
    )

    try:
        with ToastClient(config) as client:
            report.auth = dict(client.authenticate())
            for business_date in dates:
                orders = client.get_orders_for_business_date(business_date)
                entries = client.get_cash_entries(business_date)
                deposits = client.get_cash_deposits(business_date)
                sales = summarize_sales(business_date, orders)
                cash = summarize_cash(business_date, entries, deposits)
                report.days.append(
                    {
                        "business_date": business_date,
                        "sales": sales.__dict__,
                        "cash": cash.__dict__,
                    }
                )
    except ToastApiError as exc:
        report.error = str(exc)
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 1
    except Exception as exc:  # noqa: BLE001 — surface unexpected pull failures
        report.error = f"Unexpected pull failure: {exc}"
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 1

    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "health":
        allow_missing = bool(getattr(args, "allow_missing", False))
        return cmd_health(allow_missing=allow_missing)
    if args.command == "pull":
        dates: Optional[List[str]] = getattr(args, "business_dates", None)
        return cmd_pull(business_dates=dates)
    parser.error(f"Unknown command: {args.command}")
    return 2


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
