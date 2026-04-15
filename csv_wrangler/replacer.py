"""String replacement transformations for CSV columns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator


class ReplaceError(Exception):
    """Raised when a replacement operation fails."""


@dataclass
class ReplaceSpec:
    column: str
    find: str
    replacement: str
    whole_cell: bool = False  # if True, only replace when entire cell matches

    def __post_init__(self) -> None:
        if not self.column:
            raise ReplaceError("column must not be empty")


@dataclass
class ReplaceResult:
    replaced_count: int = 0
    skipped_columns: list = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        parts = [f"replaced={self.replaced_count}"]
        if self.skipped_columns:
            parts.append(f"skipped={self.skipped_columns}")
        return f"ReplaceResult({', '.join(parts)})"


def replace_rows(
    rows: Iterable[Dict[str, str]],
    specs: list[ReplaceSpec],
) -> tuple[list[Dict[str, str]], ReplaceResult]:
    """Apply replacement specs to all rows.

    Returns the transformed rows and a result summary.
    Columns referenced in specs that are absent from the header are recorded
    in *skipped_columns*.
    """
    rows = list(rows)
    if not rows:
        return [], ReplaceResult()

    header = set(rows[0].keys())
    skipped: list[str] = []
    active: list[ReplaceSpec] = []
    for spec in specs:
        if spec.column not in header:
            if spec.column not in skipped:
                skipped.append(spec.column)
        else:
            active.append(spec)

    replaced_count = 0
    out: list[Dict[str, str]] = []
    for row in rows:
        new_row = dict(row)
        for spec in active:
            original = new_row[spec.column]
            if spec.whole_cell:
                if original == spec.find:
                    new_row[spec.column] = spec.replacement
                    replaced_count += 1
            else:
                if spec.find in original:
                    new_row[spec.column] = original.replace(spec.find, spec.replacement)
                    replaced_count += 1
        out.append(new_row)

    return out, ReplaceResult(replaced_count=replaced_count, skipped_columns=skipped)


def _iter(rows: Iterable[Dict[str, str]], specs: list[ReplaceSpec]) -> Iterator[Dict[str, str]]:
    """Streaming variant — yields rows one by one."""
    for row in rows:
        new_row = dict(row)
        for spec in specs:
            if spec.column not in new_row:
                continue
            original = new_row[spec.column]
            if spec.whole_cell:
                if original == spec.find:
                    new_row[spec.column] = spec.replacement
            else:
                new_row[spec.column] = original.replace(spec.find, spec.replacement)
        yield new_row
