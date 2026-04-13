"""Random and deterministic sampling of CSV rows."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable, Iterator


class SampleError(Exception):
    """Raised when sampling parameters are invalid."""


@dataclass
class SampleResult:
    rows: list[dict[str, str]] = field(default_factory=list)
    total_input: int = 0

    @property
    def sample_count(self) -> int:
        return len(self.rows)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"SampleResult(sample={self.sample_count}, "
            f"total_input={self.total_input})"
        )


def sample_rows(
    rows: Iterable[dict[str, str]],
    n: int | None = None,
    fraction: float | None = None,
    seed: int | None = None,
) -> SampleResult:
    """Return a sample of *rows*.

    Exactly one of *n* or *fraction* must be supplied.

    Args:
        rows:     Iterable of row dicts.
        n:        Absolute number of rows to return.
        fraction: Proportion of rows to return (0.0 – 1.0 inclusive).
        seed:     Optional RNG seed for reproducibility.

    Returns:
        A :class:`SampleResult` containing the sampled rows.
    """
    if (n is None) == (fraction is None):
        raise SampleError("Specify exactly one of 'n' or 'fraction'.")

    if n is not None and n < 0:
        raise SampleError("'n' must be a non-negative integer.")

    if fraction is not None and not (0.0 <= fraction <= 1.0):
        raise SampleError("'fraction' must be between 0.0 and 1.0.")

    rng = random.Random(seed)
    all_rows = list(rows)
    total = len(all_rows)

    if n is not None:
        k = min(n, total)
    else:
        k = round(total * fraction)  # type: ignore[operator]

    sampled = rng.sample(all_rows, k) if k <= total else list(all_rows)
    return SampleResult(rows=sampled, total_input=total)


def reservoir_sample(
    rows: Iterator[dict[str, str]],
    n: int,
    seed: int | None = None,
) -> SampleResult:
    """Memory-efficient reservoir sampling for large streams."""
    if n < 0:
        raise SampleError("'n' must be a non-negative integer.")

    rng = random.Random(seed)
    reservoir: list[dict[str, str]] = []
    total = 0

    for total, row in enumerate(rows, start=1):
        if len(reservoir) < n:
            reservoir.append(row)
        else:
            j = rng.randint(0, total - 1)
            if j < n:
                reservoir[j] = row

    return SampleResult(rows=reservoir, total_input=total)
