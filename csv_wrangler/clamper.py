"""Clamp numeric column values to a [min, max] range, replacing out-of-range
values with the nearest boundary rather than dropping rows."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional


class ClampError(Exception):
    """Raised when clamping cannot be applied."""


@dataclass
class ClampSpec:
    column: str
    low: Optional[float] = None
    high: Optional[float] = None
    dest: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.column:
            raise ClampError("column must not be empty")
        if self.low is None and self.high is None:
            raise ClampError("at least one of low or high must be specified")
        if self.low is not None and self.high is not None and self.low >= self.high:
            raise ClampError("low must be strictly less than high")

    @property
    def target(self) -> str:
        return self.dest if self.dest else self.column


@dataclass
class ClampResult:
    clamped_count: int = 0
    columns_affected: List[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        cols = ", ".join(self.columns_affected) if self.columns_affected else "none"
        return f"clamped {self.clamped_count} value(s) across column(s): {cols}"


def _clamp_value(raw: str, spec: ClampSpec) -> tuple[str, bool]:
    """Return (clamped_string, was_changed)."""
    try:
        val = float(raw)
    except ValueError:
        return raw, False

    original = val
    if spec.low is not None and val < spec.low:
        val = spec.low
    if spec.high is not None and val > spec.high:
        val = spec.high

    if val == original:
        return raw, False

    # Preserve int-like appearance when possible
    if val == int(val):
        return str(int(val)), True
    return str(val), True


def clamp_rows(
    rows: Iterable[Dict[str, str]],
    specs: List[ClampSpec],
) -> tuple[Iterator[Dict[str, str]], ClampResult]:
    result = ClampResult()
    affected: set[str] = set()

    def _iter() -> Iterator[Dict[str, str]]:
        for row in rows:
            out = dict(row)
            for spec in specs:
                if spec.column not in row:
                    raise ClampError(f"column not found: {spec.column!r}")
                new_val, changed = _clamp_value(row[spec.column], spec)
                out[spec.target] = new_val
                if changed:
                    result.clamped_count += 1
                    affected.add(spec.target)
            yield out
        result.columns_affected = sorted(affected)

    return _iter(), result
