"""Condense multiple columns into one by concatenating their values."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Iterator


class CondenserError(Exception):
    pass


@dataclass
class CondenserSpec:
    columns: list[str]
    dest: str
    delimiter: str = " "
    drop_sources: bool = True

    def __post_init__(self) -> None:
        if not self.columns:
            raise CondenserError("columns must not be empty")
        if not self.dest:
            raise CondenserError("dest must not be empty")
        if len(self.columns) < 2:
            raise CondenserError("at least two source columns are required")


@dataclass
class CondenserResult:
    condensed_count: int = 0
    skipped_rows: int = 0

    def __str__(self) -> str:
        return (
            f"CondenserResult(condensed={self.condensed_count}, "
            f"skipped={self.skipped_rows})"
        )


def condense_rows(
    rows: Iterable[dict[str, str]],
    spec: CondenserSpec,
) -> tuple[list[dict[str, str]], CondenserResult]:
    result = CondenserResult()
    output: list[dict[str, str]] = []
    for row in rows:
        missing = [c for c in spec.columns if c not in row]
        if missing:
            result.skipped_rows += 1
            output.append(row)
            continue
        condensed = spec.delimiter.join(row[c] for c in spec.columns)
        new_row = dict(row)
        if spec.drop_sources:
            for c in spec.columns:
                del new_row[c]
        new_row[spec.dest] = condensed
        result.condensed_count += 1
        output.append(new_row)
    return output, result
