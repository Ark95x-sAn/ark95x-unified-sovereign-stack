"""Read-only Toast API client (auth + GET sales/cash endpoints only)."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping, Optional

import httpx

from .config import ToastConfig

# Documented read-only paths only — never POST/PUT/PATCH/DELETE business data.
AUTH_PATH = "/authentication/v1/authentication/login"
ORDERS_BULK_PATH = "/orders/v2/ordersBulk"
CASH_ENTRIES_PATH = "/cashmgmt/v1/entries"
CASH_DEPOSITS_PATH = "/cashmgmt/v1/deposits"


class ToastApiError(RuntimeError):
    """HTTP or response-shape failure talking to Toast."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ToastClient:
    """Minimal read-only Toast client.

    Uses OAuth2 client-credentials style login documented by Toast:
    POST /authentication/v1/authentication/login with clientId/clientSecret.
    All subsequent calls are GET with Bearer + Toast-Restaurant-External-ID.
    """

    def __init__(
        self,
        config: ToastConfig,
        *,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self._config = config
        self._access_token: Optional[str] = None
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ToastClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def authenticate(self) -> Mapping[str, Any]:
        """Exchange client credentials for a bearer token. Read-only setup."""
        payload = {
            "clientId": self._config.client_id,
            "clientSecret": self._config.client_secret,
            "userAccessType": self._config.user_access_type,
        }
        response = self._client.post(
            AUTH_PATH,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code >= 400:
            raise ToastApiError(
                f"Toast authentication failed with HTTP {response.status_code}",
                status_code=response.status_code,
            )
        data = response.json()
        token_block = data.get("token") or {}
        access_token = token_block.get("accessToken")
        if not access_token:
            raise ToastApiError(
                "Toast authentication response missing token.accessToken"
            )
        self._access_token = str(access_token)
        # Never return the raw secret; report shape only for operators.
        return {
            "status": data.get("status", "SUCCESS"),
            "token_type": token_block.get("tokenType", "Bearer"),
            "expires_in": token_block.get("expiresIn"),
            "authenticated": True,
        }

    def get_orders_for_business_date(
        self, business_date: str
    ) -> List[Dict[str, Any]]:
        """GET /orders/v2/ordersBulk?businessDate=yyyyMMdd (paginated)."""
        return self._get_paginated(
            ORDERS_BULK_PATH,
            params={"businessDate": business_date},
        )

    def get_cash_entries(self, business_date: str) -> List[Dict[str, Any]]:
        """GET /cashmgmt/v1/entries?businessDate=yyyyMMdd."""
        data = self._get_json(
            CASH_ENTRIES_PATH, params={"businessDate": business_date}
        )
        return _as_list(data)

    def get_cash_deposits(self, business_date: str) -> List[Dict[str, Any]]:
        """GET /cashmgmt/v1/deposits?businessDate=yyyyMMdd."""
        data = self._get_json(
            CASH_DEPOSITS_PATH, params={"businessDate": business_date}
        )
        return _as_list(data)

    def _auth_headers(self) -> MutableMapping[str, str]:
        if not self._access_token:
            raise ToastApiError("Not authenticated; call authenticate() first")
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Toast-Restaurant-External-ID": self._config.restaurant_guid,
            "Accept": "application/json",
        }

    def _get_json(
        self, path: str, *, params: Optional[Mapping[str, Any]] = None
    ) -> Any:
        response = self._client.get(
            path, params=dict(params or {}), headers=self._auth_headers()
        )
        if response.status_code >= 400:
            raise ToastApiError(
                f"Toast GET {path} failed with HTTP {response.status_code}",
                status_code=response.status_code,
            )
        if response.status_code == 204 or not response.content:
            return []
        return response.json()

    def _get_paginated(
        self, path: str, *, params: Mapping[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch all pages from ordersBulk (pageSize capped for safety)."""
        page = 1
        page_size = 100
        collected: List[Dict[str, Any]] = []
        while True:
            query = dict(params)
            query["page"] = page
            query["pageSize"] = page_size
            payload = self._get_json(path, params=query)
            batch = _as_list(payload)
            collected.extend(batch)
            if len(batch) < page_size:
                break
            page += 1
            if page > 500:
                raise ToastApiError(
                    f"Toast GET {path} exceeded pagination safety limit"
                )
        return collected


def _as_list(data: Any) -> List[Dict[str, Any]]:
    if data is None:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("orders", "data", "results", "entries", "deposits"):
            nested = data.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
        return [data]
    return []
