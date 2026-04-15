"""Column reordering for CSV rows."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


class ReorderError(Exception):
    """Raised when reordering cannot be performed."""


@dataclass
class ReorderResult:
    reordered_count: int = 0
    skipped_columns: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [f"reordered={self.reordered_count}"]
        if self.skipped_columns:
            parts.append(f"skipped={self.skipped_columns}")
        return f"ReorderResult({', '.join(parts)})"


def reorder_rows(
    rows: Iterable[dict[str, str]],
    columns: list[str],
    *,
    drop_rest: bool = False,
) -> tuple[ReorderResult, Iterator[dict[str, str]]]:
    """Reorder columns in each row.

    Args:
        rows: Input rows as dicts.
        columns: Desired column order (must exist in rows).
        drop_rest: If True, columns not listed are dropped; otherwise appended.

    Returns:
        A (ReorderResult, iterator) tuple.
    """
    rows_list = list(rows)
    if not rows_list:
        return ReorderResult(), iter([])

    all_keys = list(rows_list[0].keys())
    missing = [c for c in columns if c not in all_keys]
    if missing:
        raise ReorderError(f"Columns not found in data: {missing}")

    skipped = [k for k in all_keys if k not in columns]

    result = ReorderResult(
        reordered_count=len(rows_list),
        skipped_columns=skipped if drop_rest else [],
    )

    def _iter() -> Iterator[dict[str, str]]:
        for row in rows_list:
            ordered = {c: row[c] for c in columns}
            if not drop_rest:
                for k in all_keys:
                    if k not in ordered:
                        ordered[k] = row[k]
            yield ordered

    return result, _iter()
