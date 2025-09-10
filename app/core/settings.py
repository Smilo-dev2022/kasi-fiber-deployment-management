import os
from functools import lru_cache
from typing import List


class Settings:
    NMS_HMAC_SECRET: str = os.getenv("NMS_HMAC_SECRET", "dev-secret")
    NMS_IP_WHITELIST: str = os.getenv("NMS_IP_WHITELIST", "127.0.0.1,::1")
    QUIET_HOURS: str = os.getenv("QUIET_HOURS", "")  # e.g. "22:00-06:00"
    TENANT_REQUIRED: bool = os.getenv("TENANT_REQUIRED", "false").lower() == "true"
    DEFAULT_TENANT_ID: str = os.getenv("DEFAULT_TENANT_ID", "default")
    P1_SLA_MINUTES: int = int(os.getenv("P1_SLA_MINUTES", "30"))
    P2_SLA_MINUTES: int = int(os.getenv("P2_SLA_MINUTES", "120"))
    P3_SLA_MINUTES: int = int(os.getenv("P3_SLA_MINUTES", "360"))
    P4_SLA_MINUTES: int = int(os.getenv("P4_SLA_MINUTES", "1440"))

    @property
    def ip_allowlist(self) -> List[str]:
        return [ip.strip() for ip in self.NMS_IP_WHITELIST.split(",") if ip.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

