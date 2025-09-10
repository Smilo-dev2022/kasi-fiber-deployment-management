from __future__ import annotations

import os
from typing import Dict


DEFAULT_SLA_MINUTES: Dict[str, int] = {
    "Permissions": 72 * 60,
    "PolePlanting": 48 * 60,
    "CAC": 24 * 60,
    "Stringing": 48 * 60,
    "Invoicing": 24 * 60,
}

_sla_cache: Dict[str, int] | None = None


def get_sla_minutes() -> Dict[str, int]:
    global _sla_cache
    if _sla_cache is None:
        _sla_cache = DEFAULT_SLA_MINUTES.copy()
    return _sla_cache


def update_sla_minutes(new_map: Dict[str, int]) -> Dict[str, int]:
    global _sla_cache
    _sla_cache = DEFAULT_SLA_MINUTES.copy()
    _sla_cache.update({k: int(v) for k, v in new_map.items()})
    return _sla_cache

