"""Vertical merger: stack multiple CSV row iterables into one stream."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

Row = dict[str, str]


class MergeError(Exception):
    """Raised when rows cannot be merged due to incompatible headers."""


@dataclass
class MergeResult:
    rows: list[Row] = field(default_factory=list)
    source_counts: list[int] = field(default_factory=list)

    @property
    def total_rows(self) -> int:
        return sum(self.source_counts)

    @property
    def source_count(self) -> int:
        return len(self.source_counts)

    def __str__(self) -> str:  # pragma: no cover
        parts = [f"MergeResult: {self.total_rows} rows from {self.source_count} source(s)"]
        for i, count in enumerate(self.source_counts, 1):
            parts.append(f"  source {i}: {count} row(s)")
        return "\n".join(parts)


def merge_rows(
    sources: Iterable[Iterable[Row]],
    *,
    require_same_columns: bool = True,
    fill_missing: bool = False,
    fill_value: str = "",
) -> MergeResult:
    """Merge multiple row iterables vertically.

    Parameters
    ----------
    sources:
        An iterable of row iterables to stack.
    require_same_columns:
        When *True* (default) raise :class:`MergeError` if any source has
        columns that differ from the first source.  Ignored when
        *fill_missing* is *True*.
    fill_missing:
        When *True*, missing columns in any source are filled with
        *fill_value* instead of raising an error.
    fill_value:
        The placeholder used when *fill_missing* is *True*.
    """
    result = MergeResult()
    reference_columns: list[str] | None = None
    all_columns: list[str] = []

    collected: list[list[Row]] = []

    for source in sources:
        source_rows = list(source)
        if not source_rows:
            collected.append([])
            result.source_counts.append(0)
            continue

        cols = list(source_rows[0].keys())

        if reference_columns is None:
            reference_columns = cols
            all_columns = list(cols)
        else:
            new_cols = [c for c in cols if c not in all_columns]
            if new_cols:
                if fill_missing:
                    all_columns.extend(new_cols)
                elif require_same_columns:
                    raise MergeError(
                        f"Column mismatch: expected {reference_columns}, got {cols}"
                    )

            missing = [c for c in all_columns if c not in cols]
            if missing and not fill_missing and require_same_columns:
                raise MergeError(
                    f"Column mismatch: expected {reference_columns}, got {cols}"
                )

        collected.append(source_rows)
        result.source_counts.append(len(source_rows))

    for source_rows in collected:
        for row in source_rows:
            if fill_missing:
                normalised = {col: row.get(col, fill_value) for col in all_columns}
                result.rows.append(normalised)
            else:
                result.rows.append(row)

    return result
