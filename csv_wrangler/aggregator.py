"""Column aggregation: sum, mean, min, max, count over a column."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Literal

AggOp = Literal["sum", "mean", "min", "max", "count"]
VALID_OPS: frozenset = frozenset({"sum", "mean", "min", "max", "count"})


class AggregateError(Exception):
    """Raised when aggregation cannot be completed."""


@dataclass
class AggSpec:
    column: str
    op: AggOp

    def __post_init__(self) -> None:
        if self.op not in VALID_OPS:
            raise AggregateError(
                f"Unknown aggregation op '{self.op}'. Valid: {sorted(VALID_OPS)}"
            )


@dataclass
class AggResult:
    spec: AggSpec
    value: float
    row_count: int

    def __str__(self) -> str:
        return (
            f"{self.spec.op}({self.spec.column})={self.value} "
            f"[n={self.row_count}]"
        )


def aggregate(
    rows: Iterable[Dict[str, str]],
    specs: List[AggSpec],
) -> List[AggResult]:
    """Aggregate *rows* according to each AggSpec.

    Raises AggregateError if a column is missing or a value is non-numeric
    (for numeric ops).
    """
    rows_list = list(rows)
    results: List[AggResult] = []

    for spec in specs:
        col = spec.column
        op = spec.op

        if op == "count":
            results.append(AggResult(spec=spec, value=float(len(rows_list)), row_count=len(rows_list)))
            continue

        values: List[float] = []
        for i, row in enumerate(rows_list):
            if col not in row:
                raise AggregateError(
                    f"Column '{col}' not found in row {i}."
                )
            raw = row[col].strip()
            try:
                values.append(float(raw))
            except ValueError:
                raise AggregateError(
                    f"Cannot convert '{raw}' to float in column '{col}' (row {i})."
                )

        if not values:
            raise AggregateError(f"No rows to aggregate for column '{col}'.")

        if op == "sum":
            result_val = sum(values)
        elif op == "mean":
            result_val = sum(values) / len(values)
        elif op == "min":
            result_val = min(values)
        elif op == "max":
            result_val = max(values)
        else:  # pragma: no cover
            raise AggregateError(f"Unhandled op '{op}'.")

        results.append(AggResult(spec=spec, value=result_val, row_count=len(rows_list)))

    return results
