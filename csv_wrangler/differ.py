"""Diff two CSV row-sets and report added, removed, and changed rows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

Row = Dict[str, str]


@dataclass
class DiffResult:
    key_column: str
    added: List[Row] = field(default_factory=list)
    removed: List[Row] = field(default_factory=list)
    changed: List[Tuple[Row, Row]] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = [
            f"Key column : {self.key_column}",
            f"Added      : {len(self.added)}",
            f"Removed    : {len(self.removed)}",
            f"Changed    : {len(self.changed)}",
        ]
        return "\n".join(lines)


class DiffError(Exception):
    """Raised when diffing cannot proceed."""


def diff_rows(
    before: Iterable[Row],
    after: Iterable[Row],
    key_column: str,
) -> DiffResult:
    """Compare two sequences of rows keyed on *key_column*.

    Args:
        before: Original rows.
        after:  Updated rows.
        key_column: Column whose value uniquely identifies a row.

    Returns:
        A :class:`DiffResult` describing the differences.

    Raises:
        DiffError: If *key_column* is absent from any row or duplicate keys
                   are found in either dataset.
    """
    before_map: Dict[str, Row] = {}
    after_map: Dict[str, Row] = {}

    for idx, row in enumerate(before):
        if key_column not in row:
            raise DiffError(
                f"Key column '{key_column}' missing in before-row {idx}"
            )
        key = row[key_column]
        if key in before_map:
            raise DiffError(f"Duplicate key '{key}' in before dataset")
        before_map[key] = row

    for idx, row in enumerate(after):
        if key_column not in row:
            raise DiffError(
                f"Key column '{key_column}' missing in after-row {idx}"
            )
        key = row[key_column]
        if key in after_map:
            raise DiffError(f"Duplicate key '{key}' in after dataset")
        after_map[key] = row

    result = DiffResult(key_column=key_column)

    for key, old_row in before_map.items():
        if key not in after_map:
            result.removed.append(old_row)
        elif after_map[key] != old_row:
            result.changed.append((old_row, after_map[key]))

    for key, new_row in after_map.items():
        if key not in before_map:
            result.added.append(new_row)

    return result
