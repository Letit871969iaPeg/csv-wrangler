"""Count occurrences of values in a column and emit a frequency table."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator


class CountError(Exception):
    """Raised when counting cannot be performed."""


@dataclass
class CountSpec:
    column: str
    dest_value: str = "count"
    dest_column: str = ""
    sort: str = "desc"  # "asc", "desc", or "none"

    def __post_init__(self) -> None:
        if not self.column:
            raise CountError("column must not be empty")
        if self.sort not in ("asc", "desc", "none"):
            raise CountError(f"sort must be 'asc', 'desc', or 'none', got {self.sort!r}")
        if not self.dest_column:
            self.dest_column = f"{self.column}_count"


@dataclass
class CountResult:
    spec: CountSpec
    rows: list[dict[str, str]] = field(default_factory=list)
    total_rows: int = 0

    def __str__(self) -> str:
        return (
            f"CountResult(column={self.spec.column!r}, "
            f"unique={len(self.rows)}, total_input={self.total_rows})"
        )


def count_rows(
    rows: Iterable[dict[str, str]],
    spec: CountSpec,
) -> CountResult:
    """Consume *rows* and return a frequency table for *spec.column*."""
    counter: Counter[str] = Counter()
    total = 0
    for row in rows:
        if spec.column not in row:
            raise CountError(f"column {spec.column!r} not found in row")
        counter[row[spec.column]] += 1
        total += 1

    items = list(counter.items())
    if spec.sort == "desc":
        items.sort(key=lambda x: x[1], reverse=True)
    elif spec.sort == "asc":
        items.sort(key=lambda x: x[1])

    output = [
        {spec.column: value, spec.dest_column: str(count)}
        for value, count in items
    ]
    return CountResult(spec=spec, rows=output, total_rows=total)


def _iter(result: CountResult) -> Iterator[dict[str, str]]:
    yield from result.rows
