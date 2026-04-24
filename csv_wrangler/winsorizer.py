"""Winsorize numeric columns by clamping outliers at given percentiles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


class WinsorizeError(Exception):
    """Raised when winsorization cannot be applied."""


@dataclass
class WinsorizeSpec:
    column: str
    lower: float = 0.05
    upper: float = 0.95

    def __post_init__(self) -> None:
        if not self.column:
            raise WinsorizeError("column must not be empty")
        if not (0.0 <= self.lower < self.upper <= 1.0):
            raise WinsorizeError(
                f"lower ({self.lower}) must be in [0, 1) and less than upper ({self.upper})"
            )


@dataclass
class WinsorizeResult:
    clamped_low: int = 0
    clamped_high: int = 0
    columns_affected: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        cols = ", ".join(self.columns_affected) if self.columns_affected else "none"
        return (
            f"WinsorizeResult(clamped_low={self.clamped_low}, "
            f"clamped_high={self.clamped_high}, columns={cols})"
        )


def winsorize_rows(
    rows: Iterable[dict[str, str]],
    specs: list[WinsorizeSpec],
) -> tuple[list[dict[str, str]], WinsorizeResult]:
    """Consume *rows*, apply winsorization per spec, return (rows, result)."""
    all_rows = list(rows)
    if not all_rows or not specs:
        return all_rows, WinsorizeResult()

    result = WinsorizeResult()
    for spec in specs:
        values: list[float] = []
        for row in all_rows:
            raw = row.get(spec.column, "")
            try:
                values.append(float(raw))
            except ValueError:
                pass
        if not values:
            continue
        values_sorted = sorted(values)
        n = len(values_sorted)
        low_val = values_sorted[max(0, int(spec.lower * n))]
        high_val = values_sorted[min(n - 1, int(spec.upper * n) - 1)]
        col_low = col_high = 0
        for row in all_rows:
            raw = row.get(spec.column, "")
            try:
                v = float(raw)
            except ValueError:
                continue
            if v < low_val:
                row[spec.column] = str(low_val)
                col_low += 1
            elif v > high_val:
                row[spec.column] = str(high_val)
                col_high += 1
        if col_low or col_high:
            result.columns_affected.append(spec.column)
        result.clamped_low += col_low
        result.clamped_high += col_high

    return all_rows, result
