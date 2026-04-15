"""Row-range slicing: keep rows between start and end offsets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


class SliceError(Exception):
    """Raised when slice parameters are invalid."""


@dataclass
class SliceResult:
    rows: list[dict] = field(default_factory=list)
    total_input: int = 0
    start: int = 0
    end: int | None = None

    @property
    def kept_count(self) -> int:
        return len(self.rows)

    @property
    def skipped_count(self) -> int:
        return self.total_input - self.kept_count

    def __str__(self) -> str:  # pragma: no cover
        end_label = self.end if self.end is not None else "end"
        return (
            f"SliceResult(rows={self.kept_count}, "
            f"skipped={self.skipped_count}, "
            f"range=[{self.start}:{end_label}))"
        )


def slice_rows(
    rows: Iterable[dict],
    start: int = 0,
    end: int | None = None,
) -> SliceResult:
    """Return only rows whose 0-based index falls in [start, end).

    Args:
        rows:  Source rows (dicts).
        start: First row index to include (default 0).
        end:   One-past-last row index to include; ``None`` means no upper bound.

    Raises:
        SliceError: If *start* is negative or *end* <= *start*.
    """
    if start < 0:
        raise SliceError(f"start must be >= 0, got {start}")
    if end is not None and end <= start:
        raise SliceError(f"end ({end}) must be greater than start ({start})")

    kept: list[dict] = []
    total = 0
    for idx, row in enumerate(rows):
        total += 1
        if idx < start:
            continue
        if end is not None and idx >= end:
            continue
        kept.append(dict(row))

    return SliceResult(rows=kept, total_input=total, start=start, end=end)
