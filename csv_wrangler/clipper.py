"""Clip numeric column values to a specified [min, max] range."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional


class ClipError(Exception):
    """Raised when clipping cannot be performed."""


@dataclass
class ClipSpec:
    column: str
    low: Optional[float] = None
    high: Optional[float] = None

    def __post_init__(self) -> None:
        if self.low is None and self.high is None:
            raise ClipError("ClipSpec requires at least one of 'low' or 'high'")
        if self.low is not None and self.high is not None and self.low > self.high:
            raise ClipError(
                f"'low' ({self.low}) must be <= 'high' ({self.high})"
            )


@dataclass
class ClipResult:
    clipped_count: int = 0
    columns_affected: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        cols = ", ".join(self.columns_affected) if self.columns_affected else "none"
        return (
            f"ClipResult(clipped={self.clipped_count}, columns=[{cols}])"
        )


def clip_rows(
    rows: Iterable[Dict[str, str]],
    specs: List[ClipSpec],
    *,
    strict: bool = True,
) -> tuple[Iterator[Dict[str, str]], ClipResult]:
    """Clip values in *rows* according to *specs*.

    Returns a (generator, ClipResult) tuple.  The result is populated lazily
    as the generator is consumed.
    """
    result = ClipResult()
    affected: set[str] = set()

    def _iter() -> Iterator[Dict[str, str]]:
        for row in rows:
            out = dict(row)
            for spec in specs:
                if spec.column not in out:
                    if strict:
                        raise ClipError(
                            f"Column '{spec.column}' not found in row"
                        )
                    continue
                raw = out[spec.column]
                if raw == "":
                    continue
                try:
                    val = float(raw)
                except ValueError:
                    if strict:
                        raise ClipError(
                            f"Cannot convert '{raw}' to float in column '{spec.column}'"
                        )
                    continue
                clipped = val
                if spec.low is not None:
                    clipped = max(clipped, spec.low)
                if spec.high is not None:
                    clipped = min(clipped, spec.high)
                if clipped != val:
                    result.clipped_count += 1
                    affected.add(spec.column)
                # Preserve int-like representation where possible
                out[spec.column] = (
                    str(int(clipped)) if clipped == int(clipped) else str(clipped)
                )
            yield out
        result.columns_affected = sorted(affected)

    return _iter(), result
