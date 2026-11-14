from datetime import UTC, datetime


def utc_now() -> datetime:
    """Current time as a timezone-aware UTC datetime (patchable in tests)."""
    return datetime.now(UTC)
