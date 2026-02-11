"""Uptime Kuma API client wrapper with lazy connection and reconnection."""

import os

from .kuma_api import KumaV2Api


class KumaClient:
    """Thin wrapper around KumaV2Api that manages connection lifecycle."""

    def __init__(self):
        self._api: KumaV2Api | None = None
        self.url = os.environ.get("UPTIME_KUMA_URL", "")
        self.username = os.environ.get("UPTIME_KUMA_USERNAME")
        self.password = os.environ.get("UPTIME_KUMA_PASSWORD")
        self.token = os.environ.get("UPTIME_KUMA_TOKEN")
        self.mfa_token = os.environ.get("UPTIME_KUMA_MFA_TOKEN")

    def _validate_config(self) -> None:
        if not self.url:
            raise ValueError(
                "UPTIME_KUMA_URL environment variable is required"
            )
        if not self.token and not (self.username and self.password):
            raise ValueError(
                "Either UPTIME_KUMA_TOKEN or both UPTIME_KUMA_USERNAME and "
                "UPTIME_KUMA_PASSWORD are required"
            )

    def _connect(self) -> KumaV2Api:
        self._validate_config()
        api = KumaV2Api(self.url)
        if self.token:
            api.login_by_token(self.token)
        else:
            kwargs = {"username": self.username, "password": self.password}
            if self.mfa_token:
                kwargs["token"] = self.mfa_token
            api.login(**kwargs)
        return api

    @property
    def api(self) -> KumaV2Api:
        if self._api is None:
            self._api = self._connect()
        return self._api

    def disconnect(self) -> None:
        if self._api is not None:
            try:
                self._api.disconnect()
            except Exception:
                pass
            self._api = None

    def reconnect(self) -> KumaV2Api:
        self.disconnect()
        self._api = self._connect()
        return self._api
