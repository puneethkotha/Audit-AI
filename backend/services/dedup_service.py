"""In-memory request deduplication. No Redis required."""

import time
from typing import Any

from core.config import settings

# key -> (value, expires_at)
_store: dict[str, tuple[str, float]] = {}


def _evict_expired() -> None:
    """Remove expired entries."""
    now = time.time()
    expired = [k for k, (_, exp) in _store.items() if exp <= now]
    for k in expired:
        del _store[k]


async def get_dedup_key(note_hash: str) -> str | None:
    """Check for deduplicated audit result. Returns audit_id if found."""
    _evict_expired()
    key = f"audit:dedup:{note_hash}"
    entry = _store.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    if entry:
        del _store[key]
    return None


async def set_dedup_key(note_hash: str, audit_id: str) -> None:
    """Store audit_id for deduplication."""
    _evict_expired()
    key = f"audit:dedup:{note_hash}"
    expires_at = time.time() + settings.deduplication_ttl_seconds
    _store[key] = (audit_id, expires_at)
