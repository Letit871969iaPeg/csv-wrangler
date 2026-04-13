"""Lightweight progress reporting for pipeline runs."""

from __future__ import annotations

import sys
import time
from typing import Iterator, TypeVar

T = TypeVar("T")


class ProgressBar:
    """Simple terminal progress bar."""

    def __init__(self, total: int, label: str = "Processing", width: int = 40) -> None:
        self.total = total
        self.label = label
        self.width = width
        self._current = 0
        self._start = time.monotonic()

    def update(self, n: int = 1) -> None:
        """Advance the bar by *n* steps."""
        self._current = min(self._current + n, self.total)
        self._render()

    def finish(self) -> None:
        """Mark the bar as complete and move to a new line."""
        self._current = self.total
        self._render()
        sys.stderr.write("\n")
        sys.stderr.flush()

    def _render(self) -> None:
        elapsed = time.monotonic() - self._start
        pct = self._current / self.total if self.total else 1.0
        filled = int(self.width * pct)
        bar = "#" * filled + "-" * (self.width - filled)
        sys.stderr.write(
            f"\r{self.label}: [{bar}] {self._current}/{self.total} "
            f"({pct:.0%}) {elapsed:.1f}s"
        )
        sys.stderr.flush()


def track(iterable: Iterator[T], total: int, label: str = "Processing") -> Iterator[T]:
    """Wrap *iterable* with a progress bar printed to stderr."""
    bar = ProgressBar(total=total, label=label)
    for item in iterable:
        yield item
        bar.update()
    bar.finish()
