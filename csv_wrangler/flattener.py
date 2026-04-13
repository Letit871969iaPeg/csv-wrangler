"""Flattener: expand delimited multi-value fields into multiple rows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


class FlattenError(Exception):
    """Raised when flattening cannot be performed."""


@dataclass
class FlattenResult:
    input_rows: int = 0
    output_rows: int = 0
    columns_expanded: list[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"FlattenResult(input={self.input_rows}, "
            f"output={self.output_rows}, "
            f"expanded={self.columns_expanded})"
        )


def flatten_rows(
    rows: Iterable[dict[str, str]],
    column: str,
    delimiter: str = "|",
) -> tuple[Iterator[dict[str, str]], FlattenResult]:
    """Expand *column* by splitting on *delimiter*, yielding one row per value.

    Args:
        rows: Iterable of CSV row dicts.
        column: The column whose values should be split.
        delimiter: Character (or string) used to split values.

    Returns:
        A tuple of (row iterator, FlattenResult).

    Raises:
        FlattenError: If *delimiter* is an empty string.
    """
    if not delimiter:
        raise FlattenError("delimiter must be a non-empty string")

    result = FlattenResult(columns_expanded=[column])

    def _iter() -> Iterator[dict[str, str]]:
        for row in rows:
            result.input_rows += 1
            if column not in row:
                raise FlattenError(
                    f"column '{column}' not found in row: {list(row.keys())}"
                )
            raw = row[column]
            parts = [p.strip() for p in raw.split(delimiter)] if raw else [raw]
            for part in parts:
                result.output_rows += 1
                yield {**row, column: part}

    return _iter(), result
