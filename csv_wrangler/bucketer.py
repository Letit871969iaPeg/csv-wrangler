"""Bucket numeric column values into labeled bins."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional, Tuple


class BucketError(Exception):
    """Raised when bucketing configuration or data is invalid."""


@dataclass
class BucketSpec:
    column: str
    edges: List[float]
    labels: List[str]
    dest: str = ""
    default: str = "other"

    def __post_init__(self) -> None:
        if not self.column:
            raise BucketError("column must not be empty")
        if len(self.edges) < 2:
            raise BucketError("edges must contain at least two values")
        if len(self.labels) != len(self.edges) - 1:
            raise BucketError(
                f"expected {len(self.edges) - 1} labels for "
                f"{len(self.edges)} edges, got {len(self.labels)}"
            )
        for i in range(len(self.edges) - 1):
            if self.edges[i] >= self.edges[i + 1]:
                raise BucketError("edges must be strictly increasing")
        if not self.dest:
            self.dest = f"{self.column}_bucket"

    def assign(self, value: str) -> str:
        """Return the label for *value*, or *default* if out of range."""
        try:
            v = float(value)
        except (ValueError, TypeError):
            return self.default
        for i in range(len(self.edges) - 1):
            if self.edges[i] <= v < self.edges[i + 1]:
                return self.labels[i]
        # include upper bound in last bucket
        if v == self.edges[-1]:
            return self.labels[-1]
        return self.default


@dataclass
class BucketResult:
    bucketed_count: int = 0
    default_count: int = 0
    specs: List[BucketSpec] = field(default_factory=list)

    def __str__(self) -> str:
        cols = ", ".join(s.column for s in self.specs)
        return (
            f"BucketResult(cols=[{cols}], "
            f"bucketed={self.bucketed_count}, "
            f"default={self.default_count})"
        )


def bucket_rows(
    rows: Iterable[dict],
    specs: List[BucketSpec],
) -> Tuple[Iterator[dict], BucketResult]:
    """Yield rows with new bucket columns added; return a result summary."""
    result = BucketResult(specs=list(specs))

    def _iter() -> Iterator[dict]:
        for row in rows:
            out = dict(row)
            for spec in specs:
                label = spec.assign(row.get(spec.column, ""))
                out[spec.dest] = label
                if label == spec.default:
                    result.default_count += 1
                else:
                    result.bucketed_count += 1
            yield out

    return _iter(), result
