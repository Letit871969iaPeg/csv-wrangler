"""Column profiler: compute basic statistics for CSV columns."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence


@dataclass
class ColumnProfile:
    """Statistics for a single column."""

    name: str
    count: int = 0
    empty_count: int = 0
    unique_count: int = 0
    top_values: List[tuple] = field(default_factory=list)  # [(value, freq), ...]
    min_length: Optional[int] = None
    max_length: Optional[int] = None

    @property
    def fill_rate(self) -> float:
        """Fraction of non-empty values."""
        if self.count == 0:
            return 0.0
        return (self.count - self.empty_count) / self.count

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"{self.name}: count={self.count}, empty={self.empty_count}, "
            f"unique={self.unique_count}, fill={self.fill_rate:.0%}, "
            f"len=[{self.min_length},{self.max_length}]"
        )


def profile_column(name: str, values: Sequence[str]) -> ColumnProfile:
    """Build a :class:`ColumnProfile` from a sequence of raw string values."""
    counter: Counter = Counter(values)
    empty_count = counter.get("", 0)
    lengths = [len(v) for v in values if v != ""]

    return ColumnProfile(
        name=name,
        count=len(values),
        empty_count=empty_count,
        unique_count=len(counter),
        top_values=counter.most_common(5),
        min_length=min(lengths) if lengths else None,
        max_length=max(lengths) if lengths else None,
    )


def profile_rows(rows: List[dict]) -> Dict[str, ColumnProfile]:
    """Profile every column found across *rows*."""
    if not rows:
        return {}

    columns: Dict[str, List[str]] = {}
    for row in rows:
        for col, val in row.items():
            columns.setdefault(col, []).append(str(val) if val is not None else "")

    return {col: profile_column(col, vals) for col, vals in columns.items()}
