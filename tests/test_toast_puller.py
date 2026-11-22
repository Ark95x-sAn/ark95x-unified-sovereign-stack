"""Unit tests for the read-only Toast puller (no live network)."""

from __future__ import annotations

import json
from typing import Any, Dict

import httpx
import pytest

from integrations.toast.cli import cmd_health, cmd_pull, main
from integrations.toast.client import ToastClient
from integrations.toast.config import ToastConfig, missing_credentials
from integrations.toast.report import (
    business_dates_yesterday_and_today,
    summarize_cash,
    summarize_sales,
)


def test_missing_credentials_detects_blank_and_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TOAST_CLIENT_ID", raising=False)
    monkeypatch.delenv("TOAST_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("TOAST_API_HOSTNAME", raising=False)
    monkeypatch.delenv("TOAST_RESTAURANT_GUID", raising=False)
    assert missing_credentials() == [
        "TOAST_CLIENT_ID",
        "TOAST_CLIENT_SECRET",
        "TOAST_API_HOSTNAME",
        "TOAST_RESTAURANT_GUID",
    ]

    monkeypatch.setenv("TOAST_CLIENT_ID", "id")
    monkeypatch.setenv("TOAST_CLIENT_SECRET", " ")
    monkeypatch.setenv("TOAST_API_HOSTNAME", "ws-api.example.toast")
    monkeypatch.setenv("TOAST_RESTAURANT_GUID", "guid")
    assert missing_credentials() == ["TOAST_CLIENT_SECRET"]


def test_health_fail_closed_without_credentials(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in (
        "TOAST_CLIENT_ID",
        "TOAST_CLIENT_SECRET",
        "TOAST_API_HOSTNAME",
        "TOAST_RESTAURANT_GUID",
    ):
        monkeypatch.delenv(name, raising=False)
    code = cmd_health(allow_missing=False)
    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["network"] is False
    assert payload["ok"] is False
    assert "TOAST_CLIENT_ID" in payload["missing"]


def test_health_allow_missing_exits_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in (
        "TOAST_CLIENT_ID",
        "TOAST_CLIENT_SECRET",
        "TOAST_API_HOSTNAME",
        "TOAST_RESTAURANT_GUID",
    ):
        monkeypatch.delenv(name, raising=False)
    assert cmd_health(allow_missing=True) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["missing"]


def test_pull_fail_closed_without_credentials(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in (
        "TOAST_CLIENT_ID",
        "TOAST_CLIENT_SECRET",
        "TOAST_API_HOSTNAME",
        "TOAST_RESTAURANT_GUID",
    ):
        monkeypatch.delenv(name, raising=False)
    assert cmd_pull() == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "pull"
    assert payload["error"]
    assert payload["days"] == []


def test_summarize_sales_excludes_voided_and_deferred() -> None:
    orders = [
        {
            "voided": False,
            "deleted": False,
            "excessFood": False,
            "checks": [
                {
                    "amount": 100.0,
                    "taxAmount": 8.0,
                    "voided": False,
                    "deleted": False,
                    "selections": [
                        {"price": 20.0, "deferred": True},
                        {"price": 80.0, "deferred": False},
                    ],
                    "appliedServiceCharges": [
                        {
                            "chargeAmount": 5.0,
                            "serviceChargeCategory": "FUNDRAISING_CAMPAIGN",
                        }
                    ],
                    "payments": [
                        {
                            "type": "CREDIT",
                            "amount": 83.0,
                            "tipAmount": 10.0,
                            "refund": {"refundAmount": 2.0, "tipRefundAmount": 1.0},
                        }
                    ],
                }
            ],
        },
        {"voided": True, "checks": [{"amount": 50.0}]},
    ]
    summary = summarize_sales("20261121", orders)
    # 100 - 20 deferred - 5 fundraising - 2 refund = 73
    assert summary.net_sales == 73.0
    assert summary.order_count == 2
    assert summary.voided_order_count == 1
    assert summary.check_count == 1
    assert summary.tip_total == 10.0
    assert summary.payment_by_type["CREDIT"] == 83.0


def test_summarize_cash_groups_types() -> None:
    entries = [
        {"type": "CASH_IN", "amount": 50},
        {"type": "PAY_OUT", "amount": -25},
        {"type": "CASH_IN", "amount": 10},
    ]
    deposits = [{"amount": 100.5}, {"amount": 20}]
    summary = summarize_cash("20261121", entries, deposits)
    assert summary.entry_count == 3
    assert summary.entries_net_amount == 35.0
    assert summary.deposits_total == 120.5
    assert summary.by_type["CASH_IN"]["count"] == 2
    assert summary.by_type["PAY_OUT"]["amount"] == -25.0


def test_business_dates_yesterday_and_today() -> None:
    from datetime import date

    dates = business_dates_yesterday_and_today(today=date(2026, 11, 22))
    assert dates == ["20261121", "20261122"]


def _mock_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("/authentication/v1/authentication/login"):
        return httpx.Response(
            200,
            json={
                "status": "SUCCESS",
                "token": {
                    "tokenType": "Bearer",
                    "expiresIn": 3600,
                    "accessToken": "test-token",
                },
            },
        )
    if "ordersBulk" in path:
        return httpx.Response(
            200,
            json=[
                {
                    "voided": False,
                    "deleted": False,
                    "excessFood": False,
                    "checks": [
                        {
                            "amount": 42.5,
                            "taxAmount": 3.0,
                            "voided": False,
                            "deleted": False,
                            "selections": [],
                            "appliedServiceCharges": [],
                            "payments": [
                                {"type": "CASH", "amount": 45.5, "tipAmount": 3.0}
                            ],
                        }
                    ],
                }
            ],
        )
    if path.endswith("/cashmgmt/v1/entries"):
        return httpx.Response(
            200, json=[{"type": "CASH_IN", "amount": 10.0}]
        )
    if path.endswith("/cashmgmt/v1/deposits"):
        return httpx.Response(200, json=[{"amount": 200.0}])
    return httpx.Response(404, json={"error": "not found"})


def test_client_pull_with_mock_transport() -> None:
    config = ToastConfig(
        client_id="id",
        client_secret="secret",
        api_hostname="ws-api.example.toast",
        restaurant_guid="11111111-2222-3333-4444-555555555555",
    )
    transport = httpx.MockTransport(_mock_handler)
    with ToastClient(config, transport=transport) as client:
        auth = client.authenticate()
        assert auth["authenticated"] is True
        orders = client.get_orders_for_business_date("20261121")
        entries = client.get_cash_entries("20261121")
        deposits = client.get_cash_deposits("20261121")
    sales = summarize_sales("20261121", orders)
    cash = summarize_cash("20261121", entries, deposits)
    assert sales.net_sales == 42.5
    assert cash.deposits_total == 200.0
    assert cash.by_type["CASH_IN"]["amount"] == 10.0


def test_cli_main_health_allow_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in (
        "TOAST_CLIENT_ID",
        "TOAST_CLIENT_SECRET",
        "TOAST_API_HOSTNAME",
        "TOAST_RESTAURANT_GUID",
    ):
        monkeypatch.delenv(name, raising=False)
    assert main(["health", "--allow-missing"]) == 0
    out = capsys.readouterr().out
    assert "fail-closed" in out.lower() or "missing" in out.lower()


def test_config_base_url_normalizes_scheme() -> None:
    cfg = ToastConfig(
        client_id="a",
        client_secret="b",
        api_hostname="ws-api.example.toast",
        restaurant_guid="guid",
    )
    assert cfg.base_url == "https://ws-api.example.toast"
    cfg2 = ToastConfig(
        client_id="a",
        client_secret="b",
        api_hostname="https://ws-api.example.toast/",
        restaurant_guid="guid",
    )
    assert cfg2.base_url == "https://ws-api.example.toast"
