"""Shared helpers for the deterministic risk-scoring functions."""


def contains_any(value: str | None, keywords: list[str]) -> bool:
    """True if ``value`` case-insensitively contains any of ``keywords``."""
    if not value:
        return False
    lower = value.lower()
    return any(keyword.lower() in lower for keyword in keywords)
