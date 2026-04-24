"""Highlight rows matching a condition by adding a marker column."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


class HighlightError(Exception):
    """Raised when highlighting configuration is invalid."""


@dataclass
class HighlightSpec:
    column: str
    pattern: str
    dest: str = "_highlighted"
    match_value: str = "1"
    no_match_value: str = "0"
    case_sensitive: bool = True

    def __post_init__(self) -> None:
        if not self.column:
            raise HighlightError("column must not be empty")
        if not self.pattern:
            raise HighlightError("pattern must not be empty")
        if not self.dest:
            raise HighlightError("dest must not be empty")


@dataclass
class HighlightResult:
    highlighted_count: int = 0
    total_rows: int = 0
    specs: list[HighlightSpec] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"HighlightResult: {self.highlighted_count}/{self.total_rows} rows marked "
            f"across {len(self.specs)} spec(s)"
        )


def highlight_rows(
    rows: Iterable[dict[str, str]],
    specs: list[HighlightSpec],
) -> tuple[Iterator[dict[str, str]], HighlightResult]:
    """Annotate each row with a marker column for each spec.

    Returns an iterator of transformed rows and a HighlightResult summary.
    """
    if not specs:
        raise HighlightError("at least one HighlightSpec is required")

    result = HighlightResult(specs=specs)
    rows_list = list(rows)
    result.total_rows = len(rows_list)

    def _iter() -> Iterator[dict[str, str]]:
        for row in rows_list:
            out = dict(row)
            row_matched = False
            for spec in specs:
                cell = out.get(spec.column, "")
                if spec.column not in out:
                    raise HighlightError(
                        f"column '{spec.column}' not found in row"
                    )
                haystack = cell if spec.case_sensitive else cell.lower()
                needle = spec.pattern if spec.case_sensitive else spec.pattern.lower()
                matched = needle in haystack
                out[spec.dest] = spec.match_value if matched else spec.no_match_value
                if matched:
                    row_matched = True
            if row_matched:
                result.highlighted_count += 1
            yield out

    return _iter(), result
