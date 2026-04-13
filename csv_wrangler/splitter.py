"""Split a CSV into multiple files based on the value of a column."""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List


class SplitError(Exception):
    """Raised when splitting cannot be completed."""


@dataclass
class SplitResult:
    """Summary of a split operation."""

    column: str
    output_dir: Path
    files_written: Dict[str, int] = field(default_factory=dict)  # value -> row count

    @property
    def total_rows(self) -> int:
        return sum(self.files_written.values())

    @property
    def file_count(self) -> int:
        return len(self.files_written)

    def __str__(self) -> str:  # pragma: no cover
        lines = [
            f"Split on '{self.column}' → {self.output_dir}",
            f"  Files written : {self.file_count}",
            f"  Total rows    : {self.total_rows}",
        ]
        for value, count in sorted(self.files_written.items()):
            lines.append(f"    {value!r}: {count} row(s)")
        return "\n".join(lines)


def _safe_filename(value: str) -> str:
    """Convert a column value to a safe filename stem."""
    safe = "".join(c if (c.isalnum() or c in "-_.") else "_" for c in value)
    return safe or "__empty__"


def split_rows(
    rows: Iterable[Dict[str, str]],
    column: str,
    output_dir: Path,
    *,
    prefix: str = "",
    extension: str = ".csv",
) -> SplitResult:
    """Split *rows* into separate CSV files keyed by *column* value.

    Parameters
    ----------
    rows:       Input rows (dicts with string keys/values).
    column:     The column whose value determines the output file.
    output_dir: Directory where output files are written (created if absent).
    prefix:     Optional filename prefix, e.g. ``"chunk_"``.
    extension:  File extension including the leading dot (default ``".csv"``).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = SplitResult(column=column, output_dir=output_dir)
    writers: Dict[str, csv.DictWriter] = {}
    handles = {}
    fieldnames: List[str] = []

    try:
        for row in rows:
            if not fieldnames:
                fieldnames = list(row.keys())
            if column not in row:
                raise SplitError(
                    f"Column '{column}' not found in row; available: {list(row.keys())}"
                )
            value = row[column]
            if value not in writers:
                stem = f"{prefix}{_safe_filename(value)}"
                path = output_dir / f"{stem}{extension}"
                fh = open(path, "w", newline="", encoding="utf-8")  # noqa: WPS515
                handles[value] = fh
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                writers[value] = writer
                result.files_written[value] = 0
            writers[value].writerow(row)
            result.files_written[value] += 1
    finally:
        for fh in handles.values():
            fh.close()

    return result
