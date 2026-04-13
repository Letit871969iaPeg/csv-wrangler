"""Pivot rows by grouping on a key column and spreading a value column."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


class PivotError(Exception):
    """Raised when pivot cannot be performed."""


@dataclass
class PivotResult:
    rows: List[Dict[str, str]] = field(default_factory=list)
    index_column: str = ""
    pivot_column: str = ""
    value_column: str = ""
    pivot_values: List[str] = field(default_factory=list)

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"PivotResult(index={self.index_column!r}, "
            f"pivot={self.pivot_column!r}, "
            f"value={self.value_column!r}, "
            f"rows={self.row_count}, "
            f"pivot_values={self.pivot_values})"
        )


def pivot_rows(
    rows: Iterable[Dict[str, str]],
    index_column: str,
    pivot_column: str,
    value_column: str,
    fill_value: str = "",
    sort_pivot_values: bool = True,
) -> PivotResult:
    """Pivot *rows* so that unique values in *pivot_column* become columns.

    Args:
        rows: Input rows as dicts.
        index_column: Column whose values form the row index.
        pivot_column: Column whose unique values become new column headers.
        value_column: Column supplying the cell values.
        fill_value: Value used when a combination is absent.
        sort_pivot_values: Whether to sort the new column headers.

    Returns:
        A :class:`PivotResult` containing the pivoted rows.
    """
    raw: List[Dict[str, str]] = list(rows)

    if not raw:
        return PivotResult(
            index_column=index_column,
            pivot_column=pivot_column,
            value_column=value_column,
        )

    first = raw[0]
    for col in (index_column, pivot_column, value_column):
        if col not in first:
            raise PivotError(
                f"Column {col!r} not found in data. "
                f"Available columns: {list(first.keys())}"
            )

    # Collect pivot values and build nested mapping: index -> pivot -> value
    pivot_values_set: set = set()
    mapping: Dict[str, Dict[str, str]] = {}

    for row in raw:
        idx = row[index_column]
        pv = row[pivot_column]
        val = row[value_column]
        pivot_values_set.add(pv)
        mapping.setdefault(idx, {})[pv] = val

    pivot_values: List[str] = (
        sorted(pivot_values_set) if sort_pivot_values else list(pivot_values_set)
    )

    output_rows: List[Dict[str, str]] = []
    for idx, pv_map in mapping.items():
        out_row: Dict[str, str] = {index_column: idx}
        for pv in pivot_values:
            out_row[pv] = pv_map.get(pv, fill_value)
        output_rows.append(out_row)

    return PivotResult(
        rows=output_rows,
        index_column=index_column,
        pivot_column=pivot_column,
        value_column=value_column,
        pivot_values=pivot_values,
    )
