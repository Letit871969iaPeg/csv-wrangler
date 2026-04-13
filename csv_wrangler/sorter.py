"""Sort CSV rows by one or more columns, with optional direction control."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Literal


class SortError(ValueError):
    """Raised when a sort specification is invalid or a column is missing."""


@dataclass
class SortKey:
    """A single sort criterion."""

    column: str
    direction: Literal["asc", "desc"] = "asc"

    def __post_init__(self) -> None:
        if self.direction not in ("asc", "desc"):
            raise SortError(
                f"Invalid direction {self.direction!r} for column {self.column!r}; "
                "expected 'asc' or 'desc'."
            )


def parse_sort_keys(specs: List[str]) -> List[SortKey]:
    """Parse a list of sort spec strings such as 'name:asc' or 'age:desc'.

    A bare column name (no colon) defaults to ascending order.
    """
    keys: List[SortKey] = []
    for spec in specs:
        if ":" in spec:
            col, _, direction = spec.partition(":")
            keys.append(SortKey(column=col.strip(), direction=direction.strip()))  # type: ignore[arg-type]
        else:
            keys.append(SortKey(column=spec.strip()))
    return keys


def sort_rows(
    rows: Iterable[dict],
    keys: List[SortKey],
) -> Iterator[dict]:
    """Return rows sorted by *keys* in the specified directions.

    All rows are buffered in memory so that a stable multi-key sort can be
    performed in a single pass.

    Raises:
        SortError: if any key column is absent from the first row.
    """
    buffered = list(rows)
    if not buffered:
        return iter([])

    sample = buffered[0]
    missing = [k.column for k in keys if k.column not in sample]
    if missing:
        raise SortError(f"Sort column(s) not found in data: {missing}")

    # Build a compound sort key; apply descending via negation / reverse flag.
    # We sort from the *last* key to the *first* (stable sort trick).
    for sort_key in reversed(keys):
        reverse = sort_key.direction == "desc"
        buffered.sort(
            key=lambda row, col=sort_key.column: (row[col] is None or row[col] == "", row[col] or ""),
            reverse=reverse,
        )

    return iter(buffered)
