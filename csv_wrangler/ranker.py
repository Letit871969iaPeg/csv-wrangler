"""Rank rows by a numeric column, optionally partitioned by a group column."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


class RankError(Exception):
    """Raised when ranking cannot be performed."""


@dataclass
class RankSpec:
    column: str
    dest: str = "rank"
    group_by: str | None = None
    ascending: bool = True
    method: str = "dense"  # 'dense' | 'row'

    def __post_init__(self) -> None:
        if not self.column:
            raise RankError("column must not be empty")
        if not self.dest:
            raise RankError("dest must not be empty")
        if self.method not in ("dense", "row"):
            raise RankError(f"method must be 'dense' or 'row', got {self.method!r}")


@dataclass
class RankResult:
    ranked_count: int = 0
    skipped_count: int = 0

    def __str__(self) -> str:
        return (
            f"RankResult(ranked={self.ranked_count}, skipped={self.skipped_count})"
        )


def rank_rows(
    rows: Iterable[dict[str, str]],
    spec: RankSpec,
) -> tuple[list[dict[str, str]], RankResult]:
    """Assign rank values to rows sorted by *spec.column*.

    Returns a (rows, result) pair.  Rows that lack *spec.column* or whose
    value cannot be converted to float are skipped (rank left empty).
    """
    all_rows = list(rows)
    result = RankResult()

    # Collect (index, numeric_value, group_key)
    keyed: list[tuple[int, float, str]] = []
    for idx, row in enumerate(all_rows):
        raw = row.get(spec.column, "")
        try:
            val = float(raw)
        except (ValueError, TypeError):
            result.skipped_count += 1
            continue
        group = row.get(spec.group_by, "") if spec.group_by else ""
        keyed.append((idx, val, group))

    # Group by partition key
    from collections import defaultdict

    groups: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for idx, val, grp in keyed:
        groups[grp].append((idx, val))

    for grp_items in groups.values():
        sorted_items = sorted(
            grp_items, key=lambda t: t[1], reverse=not spec.ascending
        )
        if spec.method == "dense":
            rank = 1
            prev: float | None = None
            for idx, val in sorted_items:
                if prev is not None and val != prev:
                    rank += 1
                all_rows[idx][spec.dest] = str(rank)
                prev = val
                result.ranked_count += 1
        else:  # row
            for rank, (idx, _) in enumerate(sorted_items, start=1):
                all_rows[idx][spec.dest] = str(rank)
                result.ranked_count += 1

    return all_rows, result
