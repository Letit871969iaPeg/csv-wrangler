"""Truncate CSV rows to a maximum number of characters per field."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


class TruncateError(ValueError):
    """Raised when truncation configuration is invalid."""


@dataclass
class TruncateResult:
    """Summary of a truncation pass."""

    total_rows: int = 0
    truncated_cells: int = 0
    columns_affected: set[str] = field(default_factory=set)

    @property
    def was_lossy(self) -> bool:
        return self.truncated_cells > 0

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"TruncateResult(rows={self.total_rows}, "
            f"truncated_cells={self.truncated_cells}, "
            f"columns_affected={sorted(self.columns_affected)})"
        )


def truncate_rows(
    rows: Iterable[dict[str, str]],
    max_length: int,
    columns: list[str] | None = None,
    ellipsis_str: str = "...",
) -> tuple[Iterator[dict[str, str]], TruncateResult]:
    """Truncate string values in *rows* to *max_length* characters.

    Parameters
    ----------
    rows:
        Iterable of row dicts.
    max_length:
        Maximum number of characters allowed per field value.  Must be >= 1.
    columns:
        Restrict truncation to these column names.  ``None`` means all columns.
    ellipsis_str:
        Suffix appended when a value is truncated.  Its length must be less
        than *max_length*.

    Returns
    -------
    A ``(iterator, result)`` tuple where *iterator* lazily yields truncated
    rows and *result* accumulates statistics.
    """
    if max_length < 1:
        raise TruncateError(f"max_length must be >= 1, got {max_length}")
    if len(ellipsis_str) >= max_length:
        raise TruncateError(
            f"ellipsis_str length ({len(ellipsis_str)}) must be "
            f"less than max_length ({max_length})"
        )

    result = TruncateResult()
    cut = max_length - len(ellipsis_str)

    def _iter() -> Iterator[dict[str, str]]:
        for row in rows:
            result.total_rows += 1
            new_row: dict[str, str] = {}
            for col, val in row.items():
                if columns is not None and col not in columns:
                    new_row[col] = val
                    continue
                if len(val) > max_length:
                    new_row[col] = val[:cut] + ellipsis_str
                    result.truncated_cells += 1
                    result.columns_affected.add(col)
                else:
                    new_row[col] = val
            yield new_row

    return _iter(), result
