"""Zip (interleave) rows from two row sequences by position."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Dict


class ZipError(Exception):
    """Raised when zip_rows encounters an unrecoverable problem."""


@dataclass
class ZipResult:
    rows: List[Dict[str, str]] = field(default_factory=list)
    left_count: int = 0
    right_count: int = 0
    output_count: int = 0
    truncated: bool = False

    def __str__(self) -> str:  # pragma: no cover
        trunc = " (truncated to shorter side)" if self.truncated else ""
        return (
            f"ZipResult: left={self.left_count} right={self.right_count}"
            f" output={self.output_count}{trunc}"
        )


def zip_rows(
    left: Iterable[Dict[str, str]],
    right: Iterable[Dict[str, str]],
    *,
    prefix_left: str = "left_",
    prefix_right: str = "right_",
    strict: bool = False,
) -> ZipResult:
    """Merge rows from *left* and *right* side-by-side by position.

    Each output row contains all columns from both sides, with columns
    prefixed by *prefix_left* / *prefix_right* to avoid collisions.

    If *strict* is True a :class:`ZipError` is raised when the two
    sequences have different lengths; otherwise the result is truncated
    to the shorter sequence and ``ZipResult.truncated`` is set.
    """
    left_rows = list(left)
    right_rows = list(right)

    left_count = len(left_rows)
    right_count = len(right_rows)

    if left_count != right_count:
        if strict:
            raise ZipError(
                f"Row count mismatch: left has {left_count} rows,"
                f" right has {right_count} rows."
            )
        truncated = True
    else:
        truncated = False

    merged: List[Dict[str, str]] = []
    for l_row, r_row in zip(left_rows, right_rows):
        combined: Dict[str, str] = {}
        for k, v in l_row.items():
            combined[f"{prefix_left}{k}"] = v
        for k, v in r_row.items():
            combined[f"{prefix_right}{k}"] = v
        merged.append(combined)

    return ZipResult(
        rows=merged,
        left_count=left_count,
        right_count=right_count,
        output_count=len(merged),
        truncated=truncated,
    )
