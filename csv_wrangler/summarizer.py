"""Summarize CSV data: row count, column stats, and value frequency."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator


@dataclass
class ColumnSummary:
    name: str
    total: int = 0
    filled: int = 0
    top_values: list[tuple[str, int]] = field(default_factory=list)

    @property
    def fill_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.filled / self.total

    def __str__(self) -> str:
        top = ", ".join(f"{v!r}:{c}" for v, c in self.top_values[:3])
        return (
            f"Column({self.name!r} total={self.total} "
            f"fill={self.fill_rate:.0%} top=[{top}])"
        )


@dataclass
class DataSummary:
    row_count: int = 0
    columns: dict[str, ColumnSummary] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = [f"Rows: {self.row_count}"]
        for col in self.columns.values():
            lines.append(f"  {col}")
        return "\n".join(lines)


def summarize_rows(
    rows: Iterable[dict[str, str]],
    top_n: int = 5,
) -> DataSummary:
    """Consume an iterable of dicts and return a DataSummary."""
    summary = DataSummary()
    counters: dict[str, Counter] = {}

    for row in rows:
        summary.row_count += 1
        for col, value in row.items():
            if col not in summary.columns:
                summary.columns[col] = ColumnSummary(name=col)
                counters[col] = Counter()
            cs = summary.columns[col]
            cs.total += 1
            if value.strip():
                cs.filled += 1
            counters[col][value] += 1

    for col, counter in counters.items():
        summary.columns[col].top_values = counter.most_common(top_n)

    return summary


def iter_summary_lines(summary: DataSummary) -> Iterator[str]:
    """Yield human-readable lines describing the summary."""
    yield f"Total rows: {summary.row_count}"
    for cs in summary.columns.values():
        yield f"  {cs.name}: fill={cs.fill_rate:.1%}, unique={len(cs.top_values)}"
        for value, count in cs.top_values:
            display = repr(value) if value else "(empty)"
            yield f"    {display}: {count}"
