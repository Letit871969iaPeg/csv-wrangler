"""Convert numeric or boolean column values to formatted strings."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional


class StringifyError(Exception):
    """Raised when stringification cannot be performed."""


@dataclass
class StringifySpec:
    column: str
    dest: str = ""
    decimal_places: Optional[int] = None
    true_value: str = "true"
    false_value: str = "false"
    prefix: str = ""
    suffix: str = ""

    def __post_init__(self) -> None:
        if not self.column:
            raise StringifyError("column must not be empty")
        if self.decimal_places is not None and self.decimal_places < 0:
            raise StringifyError("decimal_places must be >= 0")
        if not self.dest:
            self.dest = self.column

    def apply(self, value: str) -> str:
        stripped = value.strip()
        if stripped.lower() in ("true", "false", "1", "0"):
            result = (
                self.true_value
                if stripped.lower() in ("true", "1")
                else self.false_value
            )
        elif self.decimal_places is not None:
            try:
                num = float(stripped)
                result = f"{num:.{self.decimal_places}f}"
            except ValueError:
                result = stripped
        else:
            result = stripped
        return f"{self.prefix}{result}{self.suffix}"


@dataclass
class StringifyResult:
    converted_count: int = 0
    skipped_columns: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [f"converted={self.converted_count}"]
        if self.skipped_columns:
            parts.append(f"skipped={self.skipped_columns}")
        return f"StringifyResult({', '.join(parts)})"


def stringify_rows(
    rows: Iterable[Dict[str, str]],
    specs: List[StringifySpec],
) -> Iterator[Dict[str, str]]:
    result = StringifyResult()
    skipped: List[str] = []

    for row in rows:
        out = dict(row)
        for spec in specs:
            if spec.column not in row:
                if spec.column not in skipped:
                    skipped.append(spec.column)
                continue
            out[spec.dest] = spec.apply(row[spec.column])
            result.converted_count += 1
        yield out

    result.skipped_columns = skipped
    return result


def stringify_rows_with_result(
    rows: Iterable[Dict[str, str]],
    specs: List[StringifySpec],
) -> tuple[List[Dict[str, str]], StringifyResult]:
    result = StringifyResult()
    skipped: List[str] = []
    output: List[Dict[str, str]] = []

    for row in rows:
        out = dict(row)
        for spec in specs:
            if spec.column not in row:
                if spec.column not in skipped:
                    skipped.append(spec.column)
                continue
            out[spec.dest] = spec.apply(row[spec.column])
            result.converted_count += 1
        output.append(out)

    result.skipped_columns = skipped
    return output, result
