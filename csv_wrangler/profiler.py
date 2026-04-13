"""Column profiling utilities for CSV data."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class ColumnProfile:
    name: str
    total: int = 0
    non_empty: int = 0
    unique_values: set = field(default_factory=set)
    min_length: int | None = None
    max_length: int | None = None

    @property
    def fill_rate(self) -> float:
        """Fraction of rows that are non-empty (0.0 – 1.0)."""
        if self.total == 0:
            return 0.0
        return self.non_empty / self.total

    @property
    def unique_count(self) -> int:
        return len(self.unique_values)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"ColumnProfile({self.name!r}: total={self.total}, "
            f"fill_rate={self.fill_rate:.1%}, unique={self.unique_count}, "
            f"min_len={self.min_length}, max_len={self.max_length})"
        )


def profile_column(name: str, values: Iterable[str]) -> ColumnProfile:
    """Build a :class:`ColumnProfile` from an iterable of string values."""
    prof = ColumnProfile(name=name)
    for value in values:
        prof.total += 1
        if value and value.strip():
            prof.non_empty += 1
            length = len(value)
            prof.min_length = length if prof.min_length is None else min(prof.min_length, length)
            prof.max_length = length if prof.max_length is None else max(prof.max_length, length)
        prof.unique_values.add(value)
    return prof


def profile_rows(
    rows: Iterable[dict[str, str]],
    columns: list[str] | None = None,
) -> dict[str, ColumnProfile]:
    """Profile every column across all *rows*.

    Args:
        rows: Iterable of dicts representing CSV rows.
        columns: Explicit list of column names to profile.  When *None* the
            columns are inferred from the first row.

    Returns:
        Mapping of column name → :class:`ColumnProfile`.
    """
    rows = list(rows)
    if not rows:
        return {}

    cols = columns if columns is not None else list(rows[0].keys())
    col_values: dict[str, list[str]] = {c: [] for c in cols}

    for row in rows:
        for col in cols:
            col_values[col].append(row.get(col, ""))

    return {col: profile_column(col, vals) for col, vals in col_values.items()}
