"""Group CSV rows by one or more key columns and emit aggregate sub-rows."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List


class GroupError(Exception):
    """Raised when grouping fails."""


@dataclass
class GroupResult:
    group_count: int = 0
    total_rows: int = 0
    key_columns: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        keys = ", ".join(self.key_columns) if self.key_columns else "(none)"
        return (
            f"GroupResult: {self.group_count} groups from {self.total_rows} rows "
            f"(keys: {keys})"
        )


def group_rows(
    rows: Iterable[Dict[str, str]],
    key_columns: List[str],
    count_column: str = "_count",
) -> Iterator[Dict[str, str]]:
    """Group *rows* by *key_columns*, yielding one summary row per group.

    Each output row contains the key column values plus a *count_column* that
    holds the number of input rows in that group.

    Raises
    ------
    GroupError
        If *key_columns* is empty or a key column is missing from the first row.
    """
    if not key_columns:
        raise GroupError("At least one key column must be specified.")

    counts: Dict[tuple, int] = defaultdict(int)
    seen_columns: List[str] = []
    total = 0

    for row in rows:
        if not seen_columns:
            for col in key_columns:
                if col not in row:
                    raise GroupError(f"Key column '{col}' not found in row.")
            seen_columns = list(row.keys())
        key = tuple(row[col] for col in key_columns)
        counts[key] += 1
        total += 1

    for key_values, count in counts.items():
        out: Dict[str, str] = {col: val for col, val in zip(key_columns, key_values)}
        out[count_column] = str(count)
        yield out


def group_rows_with_result(
    rows: Iterable[Dict[str, str]],
    key_columns: List[str],
    count_column: str = "_count",
) -> tuple[List[Dict[str, str]], GroupResult]:
    """Convenience wrapper that materialises grouped rows and returns a result."""
    output: List[Dict[str, str]] = []
    counts: Dict[tuple, int] = defaultdict(int)
    total = 0

    if not key_columns:
        raise GroupError("At least one key column must be specified.")

    for row in rows:
        if total == 0:
            for col in key_columns:
                if col not in row:
                    raise GroupError(f"Key column '{col}' not found in row.")
        key = tuple(row[col] for col in key_columns)
        counts[key] += 1
        total += 1

    for key_values, count in counts.items():
        out: Dict[str, str] = {col: val for col, val in zip(key_columns, key_values)}
        out[count_column] = str(count)
        output.append(out)

    result = GroupResult(
        group_count=len(output),
        total_rows=total,
        key_columns=list(key_columns),
    )
    return output, result
