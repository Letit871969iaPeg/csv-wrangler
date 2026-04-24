"""Min-max and z-score scaling for numeric CSV columns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


class ScaleError(Exception):
    """Raised when scaling cannot be applied."""


@dataclass
class ScaleSpec:
    column: str
    method: str  # 'minmax' | 'zscore'
    dest: str = ""

    def __post_init__(self) -> None:
        if not self.column:
            raise ScaleError("column must not be empty")
        if self.method not in ("minmax", "zscore"):
            raise ScaleError(f"unknown method {self.method!r}; use 'minmax' or 'zscore'")
        if not self.dest:
            self.dest = self.column


@dataclass
class ScaleResult:
    columns_scaled: list[str] = field(default_factory=list)
    rows_processed: int = 0
    skipped_non_numeric: int = 0

    def __str__(self) -> str:
        return (
            f"scaled {len(self.columns_scaled)} column(s) "
            f"over {self.rows_processed} row(s); "
            f"{self.skipped_non_numeric} non-numeric value(s) left unchanged"
        )


def scale_rows(
    rows: Iterable[dict[str, str]],
    specs: list[ScaleSpec],
) -> tuple[list[dict[str, str]], ScaleResult]:
    """Apply scaling specs to *rows* and return (output_rows, result)."""
    all_rows = list(rows)
    result = ScaleResult()

    for spec in specs:
        numeric: list[tuple[int, float]] = []
        for idx, row in enumerate(all_rows):
            raw = row.get(spec.column, "")
            try:
                numeric.append((idx, float(raw)))
            except ValueError:
                result.skipped_non_numeric += 1

        if not numeric:
            continue

        values = [v for _, v in numeric]
        if spec.method == "minmax":
            lo, hi = min(values), max(values)
            span = hi - lo
            for idx, v in numeric:
                scaled = (v - lo) / span if span else 0.0
                all_rows[idx][spec.dest] = f"{scaled:.6g}"
        else:  # zscore
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std = variance ** 0.5
            for idx, v in numeric:
                scaled = (v - mean) / std if std else 0.0
                all_rows[idx][spec.dest] = f"{scaled:.6g}"

        if spec.column not in result.columns_scaled:
            result.columns_scaled.append(spec.column)

    result.rows_processed = len(all_rows)
    return all_rows, result
