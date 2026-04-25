"""Route rows into separate buckets based on a column value or expression."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List


class RouteError(Exception):
    """Raised when routing configuration or execution fails."""


@dataclass
class RouteSpec:
    column: str
    routes: Dict[str, str]  # value -> bucket label
    default: str = "__other__"

    def __post_init__(self) -> None:
        if not self.column:
            raise RouteError("column must not be empty")
        if not self.routes:
            raise RouteError("routes mapping must not be empty")
        if not self.default:
            raise RouteError("default bucket label must not be empty")


@dataclass
class RouteResult:
    buckets: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)

    @property
    def total_rows(self) -> int:
        return sum(len(rows) for rows in self.buckets.values())

    @property
    def bucket_count(self) -> int:
        return len(self.buckets)

    def __str__(self) -> str:
        lines = [f"RouteResult: {self.total_rows} rows across {self.bucket_count} buckets"]
        for label, rows in sorted(self.buckets.items()):
            lines.append(f"  {label}: {len(rows)} rows")
        return "\n".join(lines)


def route_rows(
    rows: Iterable[Dict[str, str]],
    spec: RouteSpec,
) -> RouteResult:
    """Partition *rows* into named buckets according to *spec*.

    Rows whose column value matches a key in ``spec.routes`` are placed in the
    corresponding bucket; all others go to ``spec.default``.
    """
    result: RouteResult = RouteResult()

    for row in rows:
        if spec.column not in row:
            raise RouteError(f"column '{spec.column}' not found in row: {list(row.keys())}")
        value = row[spec.column]
        bucket = spec.routes.get(value, spec.default)
        result.buckets.setdefault(bucket, []).append(dict(row))

    return result


def iter_bucket(
    result: RouteResult,
    label: str,
) -> Iterator[Dict[str, str]]:
    """Yield rows from a specific bucket by *label*."""
    for row in result.buckets.get(label, []):
        yield row
