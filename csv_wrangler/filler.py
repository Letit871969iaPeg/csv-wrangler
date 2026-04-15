"""Fill missing (empty) values in specified columns with a default or strategy."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


FILL_STRATEGIES = {"forward", "backward", "constant"}


class FillError(Exception):
    """Raised when a fill operation cannot be completed."""


@dataclass
class FillSpec:
    column: str
    strategy: str = "constant"
    value: str = ""

    def __post_init__(self) -> None:
        if self.strategy not in FILL_STRATEGIES:
            raise FillError(
                f"Unknown fill strategy {self.strategy!r}. "
                f"Choose from: {sorted(FILL_STRATEGIES)}"
            )
        if self.strategy == "constant" and self.value == "" and self.value is not None:
            pass  # empty string constant is valid


@dataclass
class FillResult:
    filled_count: int = 0
    columns_affected: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        cols = ", ".join(self.columns_affected) or "none"
        return f"FillResult: {self.filled_count} cells filled across columns: {cols}"


def fill_rows(
    rows: Iterable[dict[str, str]],
    specs: list[FillSpec],
) -> tuple[list[dict[str, str]], FillResult]:
    """Fill missing values in *rows* according to *specs*.

    Returns the transformed rows and a :class:`FillResult` summary.
    """
    if not specs:
        return list(rows), FillResult()

    rows_list = list(rows)
    filled_count = 0
    columns_affected: set[str] = set()

    for spec in specs:
        prev_value: str = ""
        # Collect non-empty values for backward fill
        non_empty: list[str] = [
            r.get(spec.column, "") for r in rows_list if r.get(spec.column, "")
        ]
        backward_idx = 0

        for i, row in enumerate(rows_list):
            if spec.column not in row:
                raise FillError(f"Column {spec.column!r} not found in row {i}")
            current = row[spec.column]
            if current == "":
                if spec.strategy == "constant":
                    row[spec.column] = spec.value
                elif spec.strategy == "forward":
                    row[spec.column] = prev_value
                elif spec.strategy == "backward":
                    # find next non-empty
                    future = next(
                        (r[spec.column] for r in rows_list[i + 1:] if r.get(spec.column, "")),
                        "",
                    )
                    row[spec.column] = future
                if row[spec.column] != "":
                    filled_count += 1
                    columns_affected.add(spec.column)
            else:
                prev_value = current

    return rows_list, FillResult(
        filled_count=filled_count,
        columns_affected=sorted(columns_affected),
    )
