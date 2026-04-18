"""Column-level deduplication: remove duplicate values within a column, replacing repeats with empty string."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Iterator


class ColDedupeError(ValueError):
    pass


@dataclass
class ColDedupeSpec:
    column: str

    def __post_init__(self) -> None:
        if not self.column:
            raise ColDedupeError("column must not be empty")


@dataclass
class ColDedupeResult:
    cleared_count: int = 0
    columns_processed: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        cols = ", ".join(self.columns_processed) if self.columns_processed else "none"
        return f"ColDedupe: cleared {self.cleared_count} duplicate(s) across [{cols}]"


Row = dict[str, str]


def dedupe_column_rows(
    rows: Iterable[Row],
    specs: list[ColDedupeSpec],
) -> tuple[list[Row], ColDedupeResult]:
    result = ColDedupeResult(columns_processed=[s.column for s in specs])
    seen: dict[str, str | None] = {s.column: None for s in specs}
    out: list[Row] = []
    for row in rows:
        new_row = dict(row)
        for spec in specs:
            col = spec.column
            if col not in new_row:
                raise ColDedupeError(f"column not found: {col!r}")
            val = new_row[col]
            if val == seen[col]:
                new_row[col] = ""
                result.cleared_count += 1
            else:
                seen[col] = val
        out.append(new_row)
    return out, result
