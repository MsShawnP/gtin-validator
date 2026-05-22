"""In-memory cache for validation results.

Stores raw BatchResult dicts (needed by report generators) keyed by UUID token.
TTL-based eviction, max 100 entries.
"""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

    from gtin_core import BatchResult

TTL_SECONDS = 1800  # 30 minutes
MAX_ENTRIES = 100


class _CacheEntry:
    __slots__ = ("batch_result", "dataframe", "created_at")

    def __init__(
        self, batch_result: BatchResult, dataframe: pd.DataFrame | None
    ) -> None:
        self.batch_result = batch_result
        self.dataframe = dataframe
        self.created_at = time.monotonic()

    def is_expired(self) -> bool:
        return (time.monotonic() - self.created_at) > TTL_SECONDS


_store: dict[str, _CacheEntry] = {}


def _evict() -> None:
    now = time.monotonic()
    expired = [k for k, v in _store.items() if (now - v.created_at) > TTL_SECONDS]
    for k in expired:
        del _store[k]
    while len(_store) > MAX_ENTRIES:
        oldest_key = min(_store, key=lambda k: _store[k].created_at)
        del _store[oldest_key]


def store_result(
    batch_result: Any, dataframe: Any = None
) -> str:
    _evict()
    token = uuid.uuid4().hex
    _store[token] = _CacheEntry(batch_result, dataframe)
    return token


def get_result(token: str) -> _CacheEntry | None:
    entry = _store.get(token)
    if entry is None or entry.is_expired():
        _store.pop(token, None)
        return None
    return entry
