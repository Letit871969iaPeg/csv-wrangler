"""Extract a substring from a column using a regex capture group."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator


class ExtractError(Exception):
    """Raised when extraction configuration or execution fails."""


@dataclass
class ExtractSpec:
    column: str
    pattern: str
    dest: str = ""
    group: int = 1
    on_no_match: str = ""  # value written when pattern does not match

    def __post_init__(self) -> None:
        if not self.column:
            raise ExtractError("column must not be empty")
        if not self.pattern:
            raise ExtractError("pattern must not be empty")
        if self.group < 1:
            raise ExtractError("group must be >= 1")
        try:
            re.compile(self.pattern)
        except re.error as exc:
            raise ExtractError(f"invalid regex pattern: {exc}") from exc
        if not self.dest:
            self.dest = self.column


@dataclass
class ExtractResult:
    matched_count: int = 0
    unmatched_count: int = 0
    specs: list[ExtractSpec] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [f"matched={self.matched_count}", f"unmatched={self.unmatched_count}"]
        return f"ExtractResult({', '.join(parts)})"


def _iter(
    rows: Iterator[dict[str, str]],
    specs: list[ExtractSpec],
    result: ExtractResult,
) -> Iterator[dict[str, str]]:
    compiled = [(spec, re.compile(spec.pattern)) for spec in specs]
    for row in rows:
        out = dict(row)
        for spec, rx in compiled:
            if spec.column not in out:
                raise ExtractError(f"column not found: {spec.column!r}")
            m = rx.search(out[spec.column])
            if m:
                try:
                    out[spec.dest] = m.group(spec.group)
                except IndexError:
                    raise ExtractError(
                        f"pattern has no group {spec.group}: {spec.pattern!r}"
                    )
                result.matched_count += 1
            else:
                out[spec.dest] = spec.on_no_match
                result.unmatched_count += 1
        yield out


def extract_rows(
    rows: Iterator[dict[str, str]],
    specs: list[ExtractSpec],
) -> tuple[Iterator[dict[str, str]], ExtractResult]:
    """Return a lazy iterator of transformed rows and a shared result object."""
    if not specs:
        raise ExtractError("at least one ExtractSpec is required")
    result = ExtractResult(specs=specs)
    return _iter(rows, specs, result), result
