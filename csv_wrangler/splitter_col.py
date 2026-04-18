"""Column splitter: split one column into multiple by a delimiter."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Iterator


class ColSplitError(Exception):
    pass


@dataclass
class ColSplitSpec:
    column: str
    delimiter: str
    into: list[str]
    drop_source: bool = True

    def __post_init__(self) -> None:
        if not self.column:
            raise ColSplitError("column must not be empty")
        if not self.delimiter:
            raise ColSplitError("delimiter must not be empty")
        if len(self.into) < 2:
            raise ColSplitError("into must have at least 2 target column names")


@dataclass
class ColSplitResult:
    rows_processed: int = 0
    rows_split: int = 0
    columns_added: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"ColSplitResult(processed={self.rows_processed}, "
            f"split={self.rows_split}, added={self.columns_added})"
        )


def split_column(
    rows: Iterable[dict[str, str]],
    spec: ColSplitSpec,
) -> tuple[list[dict[str, str]], ColSplitResult]:
    result = ColSplitResult(columns_added=list(spec.into))
    output: list[dict[str, str]] = []
    for row in rows:
        result.rows_processed += 1
        if spec.column not in row:
            raise ColSplitError(f"column '{spec.column}' not found in row")
        parts = row[spec.column].split(spec.delimiter, maxsplit=len(spec.into) - 1)
        new_row = dict(row)
        split_happened = False
        for i, name in enumerate(spec.into):
            new_row[name] = parts[i] if i < len(parts) else ""
            if i < len(parts):
                split_happened = True
        if spec.drop_source:
            new_row.pop(spec.column, None)
        if split_happened:
            result.rows_split += 1
        output.append(new_row)
    return output, result


def _iter(
    rows: Iterable[dict[str, str]],
    spec: ColSplitSpec,
) -> Iterator[dict[str, str]]:
    for row in rows:
        if spec.column not in row:
            raise ColSplitError(f"column '{spec.column}' not found in row")
        parts = row[spec.column].split(spec.delimiter, maxsplit=len(spec.into) - 1)
        new_row = dict(row)
        for i, name in enumerate(spec.into):
            new_row[name] = parts[i] if i < len(parts) else ""
        if spec.drop_source:
            new_row.pop(spec.column, None)
        yield new_row
