"""Environment-backed configuration for the Toast puller (placeholders only)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

REQUIRED_ENV_VARS = (
    "TOAST_CLIENT_ID",
    "TOAST_CLIENT_SECRET",
    "TOAST_API_HOSTNAME",
    "TOAST_RESTAURANT_GUID",
)

OPTIONAL_ENV_VARS = (
    "TOAST_USER_ACCESS_TYPE",  # default TOAST_MACHINE_CLIENT
)


@dataclass(frozen=True)
class ToastConfig:
    """Runtime config loaded from environment variables."""

    client_id: str
    client_secret: str
    api_hostname: str
    restaurant_guid: str
    user_access_type: str = "TOAST_MACHINE_CLIENT"
    timeout_seconds: float = 30.0

    @property
    def base_url(self) -> str:
        host = self.api_hostname.strip()
        if host.startswith("https://") or host.startswith("http://"):
            return host.rstrip("/")
        return f"https://{host.rstrip('/')}"

    @classmethod
    def from_env(cls) -> "ToastConfig":
        missing = missing_credentials()
        if missing:
            raise ConfigError(
                "Missing required Toast env vars: "
                + ", ".join(missing)
                + ". Copy placeholders from .env.example; do not hardcode secrets."
            )
        return cls(
            client_id=os.environ["TOAST_CLIENT_ID"].strip(),
            client_secret=os.environ["TOAST_CLIENT_SECRET"].strip(),
            api_hostname=os.environ["TOAST_API_HOSTNAME"].strip(),
            restaurant_guid=os.environ["TOAST_RESTAURANT_GUID"].strip(),
            user_access_type=os.environ.get(
                "TOAST_USER_ACCESS_TYPE", "TOAST_MACHINE_CLIENT"
            ).strip()
            or "TOAST_MACHINE_CLIENT",
        )


class ConfigError(RuntimeError):
    """Raised when required credentials/config are missing or invalid."""


def missing_credentials(environ: dict | None = None) -> List[str]:
    """Return names of required env vars that are unset or blank."""
    env = environ if environ is not None else os.environ
    missing: List[str] = []
    for name in REQUIRED_ENV_VARS:
        value = env.get(name)
        if value is None or not str(value).strip():
            missing.append(name)
    return missing
