"""Bulk column renaming via a mapping dictionary."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


@dataclass
class RenameResult:
    renamed_count: int = 0
    skipped_columns: list[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        parts = [f"Renamed {self.renamed_count} column(s)"]
        if self.skipped_columns:
            skipped = ", ".join(self.skipped_columns)
            parts.append(f"skipped (not found): {skipped}")
        return "; ".join(parts)


def rename_rows(
    rows: Iterable[Dict[str, str]],
    mapping: Dict[str, str],
    strict: bool = False,
) -> tuple[Iterator[Dict[str, str]], RenameResult]:
    """Rename columns in *rows* according to *mapping*.

    Args:
        rows: Iterable of row dicts.
        mapping: ``{old_name: new_name}`` pairs.
        strict: When *True*, raise :class:`RenameError` if any key in
                *mapping* is absent from the first row's headers.

    Returns:
        A ``(iterator, RenameResult)`` tuple.  The iterator yields
        transformed rows; the result object carries statistics.

    Raises:
        RenameError: If *mapping* is empty, contains duplicate target
                     names, or *strict* is True and a source column is
                     missing.
    """
    if not mapping:
        raise RenameError("mapping must contain at least one entry")

    target_names = list(mapping.values())
    if len(target_names) != len(set(target_names)):
        raise RenameError("mapping contains duplicate target column names")

    rows_list = list(rows)
    if not rows_list:
        return iter([]), RenameResult(renamed_count=0)

    first_headers = set(rows_list[0].keys())
    missing = [src for src in mapping if src not in first_headers]

    if strict and missing:
        raise RenameError(
            f"strict mode: source column(s) not found: {', '.join(missing)}"
        )

    effective_mapping = {k: v for k, v in mapping.items() if k not in missing}
    result = RenameResult(
        renamed_count=len(effective_mapping),
        skipped_columns=missing,
    )

    def _iter() -> Iterator[Dict[str, str]]:
        for row in rows_list:
            yield {
                effective_mapping.get(col, col): val
                for col, val in row.items()
            }

    return _iter(), result
