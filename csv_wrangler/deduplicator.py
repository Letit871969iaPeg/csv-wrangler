"""Deduplication utilities for CSV rows."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional, Sequence


class DeduplicationError(Exception):
    """Raised when deduplication cannot be performed."""


@dataclass
class DeduplicationResult:
    """Summary of a deduplication pass."""

    kept: List[dict] = field(default_factory=list)
    dropped: List[dict] = field(default_factory=list)

    @property
    def duplicate_count(self) -> int:
        return len(self.dropped)

    @property
    def total_input(self) -> int:
        return len(self.kept) + len(self.dropped)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"DeduplicationResult(kept={len(self.kept)}, "
            f"dropped={self.duplicate_count}, "
            f"total={self.total_input})"
        )


def _make_key(row: dict, columns: Sequence[str]) -> tuple:
    """Build a hashable key from the specified columns of *row*."""
    return tuple(row.get(col, "") for col in columns)


def deduplicate_rows(
    rows: Iterable[dict],
    key_columns: Optional[Sequence[str]] = None,
    *,
    keep: str = "first",
) -> DeduplicationResult:
    """Remove duplicate rows.

    Parameters
    ----------
    rows:
        Iterable of row dicts.
    key_columns:
        Columns to use for the duplicate key.  ``None`` means use *all*
        columns (entire row).
    keep:
        ``"first"`` keeps the first occurrence; ``"last"`` keeps the last.
    """
    if keep not in ("first", "last"):
        raise DeduplicationError(f"keep must be 'first' or 'last', got {keep!r}")

    all_rows: List[dict] = list(rows)

    if not all_rows:
        return DeduplicationResult()

    if key_columns is not None:
        missing = [c for c in key_columns if c not in all_rows[0]]
        if missing:
            raise DeduplicationError(
                f"Key column(s) not found in rows: {missing}"
            )

    seen: dict[tuple, int] = {}
    result = DeduplicationResult()

    for idx, row in enumerate(all_rows):
        key = _make_key(row, key_columns) if key_columns else tuple(sorted(row.items()))
        if key not in seen:
            seen[key] = idx
        elif keep == "last":
            # Mark the previously kept row as dropped and keep this one
            result.dropped.append(all_rows[seen[key]])
            seen[key] = idx

    kept_indices = set(seen.values())
    for idx, row in enumerate(all_rows):
        if idx in kept_indices:
            result.kept.append(row)
        elif keep == "first":
            result.dropped.append(row)

    return result
