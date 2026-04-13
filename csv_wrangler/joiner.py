"""Join two CSV row iterables on a common key column."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional


class JoinError(Exception):
    """Raised when a join operation cannot be completed."""


@dataclass
class JoinResult:
    rows: List[Dict[str, str]] = field(default_factory=list)
    left_unmatched: int = 0
    right_unmatched: int = 0

    @property
    def matched(self) -> int:
        return len(self.rows) - self.left_unmatched - self.right_unmatched

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"JoinResult(rows={len(self.rows)}, matched={self.matched}, "
            f"left_unmatched={self.left_unmatched}, "
            f"right_unmatched={self.right_unmatched})"
        )


def join_rows(
    left: Iterable[Dict[str, str]],
    right: Iterable[Dict[str, str]],
    key: str,
    how: str = "inner",
) -> JoinResult:
    """Join *left* and *right* row streams on *key*.

    Parameters
    ----------
    left, right:
        Iterables of ``{column: value}`` dicts.
    key:
        The column name used as the join key (must exist in both streams).
    how:
        One of ``'inner'``, ``'left'``, or ``'right'``.
    """
    if how not in {"inner", "left", "right"}:
        raise JoinError(f"Unknown join type {how!r}; expected 'inner', 'left', or 'right'.")

    left_rows = list(left)
    right_rows = list(right)

    if left_rows and key not in left_rows[0]:
        raise JoinError(f"Key column {key!r} not found in left rows.")
    if right_rows and key not in right_rows[0]:
        raise JoinError(f"Key column {key!r} not found in right rows.")

    # Build lookup from right keyed by join column
    right_lookup: Dict[str, List[Dict[str, str]]] = {}
    for row in right_rows:
        right_lookup.setdefault(row[key], []).append(row)

    result = JoinResult()
    matched_right_keys: set = set()

    for lrow in left_rows:
        k = lrow[key]
        matches = right_lookup.get(k)
        if matches:
            matched_right_keys.add(k)
            for rrow in matches:
                merged = {**rrow, **lrow}  # left values win on conflict
                result.rows.append(merged)
        else:
            if how == "left":
                result.rows.append(dict(lrow))
                result.left_unmatched += 1

    if how == "right":
        for rrow in right_rows:
            k = rrow[key]
            if k not in matched_right_keys:
                result.rows.append(dict(rrow))
                result.right_unmatched += 1

    return result
