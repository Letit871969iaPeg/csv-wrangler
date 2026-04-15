"""Transpose CSV rows into columns and vice versa."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


class TransposeError(Exception):
    """Raised when transposition cannot be performed."""


@dataclass
class TransposeResult:
    rows_in: int = 0
    columns_in: int = 0
    rows_out: int = 0
    columns_out: int = 0
    _rows: list[dict[str, str]] = field(default_factory=list, repr=False)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"TransposeResult(rows_in={self.rows_in}, columns_in={self.columns_in}, "
            f"rows_out={self.rows_out}, columns_out={self.columns_out})"
        )

    @property
    def output_rows(self) -> list[dict[str, str]]:
        return list(self._rows)


def transpose_rows(
    rows: Iterable[dict[str, str]],
    *,
    index_column: str = "field",
) -> TransposeResult:
    """Transpose an iterable of row dicts so that each original column
    becomes a row in the output.

    The *index_column* names the column that will hold original field names.
    Remaining columns are named ``row_0``, ``row_1``, etc.

    Raises :class:`TransposeError` if *index_column* clashes with an existing
    column name in the first row.
    """
    all_rows: list[dict[str, str]] = list(rows)
    if not all_rows:
        return TransposeResult()

    headers = list(all_rows[0].keys())
    if index_column in headers:
        raise TransposeError(
            f"index_column '{index_column}' clashes with an existing column; "
            "choose a different name via --index-column."
        )

    row_labels = [f"row_{i}" for i in range(len(all_rows))]
    out_headers = [index_column] + row_labels

    output: list[dict[str, str]] = []
    for col in headers:
        new_row: dict[str, str] = {index_column: col}
        for label, src_row in zip(row_labels, all_rows):
            new_row[label] = src_row.get(col, "")
        output.append(new_row)

    return TransposeResult(
        rows_in=len(all_rows),
        columns_in=len(headers),
        rows_out=len(output),
        columns_out=len(out_headers),
        _rows=output,
    )
