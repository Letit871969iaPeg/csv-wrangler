"""Date parsing and formatting for CSV columns."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Iterator


class DateParseError(Exception):
    pass


_COMMON_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
    "%Y/%m/%d", "%d-%m-%Y", "%m-%d-%Y",
    "%Y%m%d", "%d.%m.%Y",
]


@dataclass
class DateSpec:
    column: str
    in_format: str | None = None
    out_format: str = "%Y-%m-%d"
    dest: str | None = None

    def __post_init__(self) -> None:
        if not self.column:
            raise DateParseError("column must not be empty")
        if not self.out_format:
            raise DateParseError("out_format must not be empty")


@dataclass
class DateResult:
    converted_count: int = 0
    failed_count: int = 0
    columns_affected: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"DateResult(converted={self.converted_count}, "
            f"failed={self.failed_count}, "
            f"columns={self.columns_affected})"
        )


def _parse_value(value: str, in_format: str | None) -> datetime | None:
    if in_format:
        try:
            return datetime.strptime(value, in_format)
        except ValueError:
            return None
    for fmt in _COMMON_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_dates(
    rows: Iterable[dict[str, str]],
    specs: list[DateSpec],
) -> tuple[list[dict[str, str]], DateResult]:
    result = DateResult(columns_affected=[s.dest or s.column for s in specs])
    output: list[dict[str, str]] = []
    for row in rows:
        new_row = dict(row)
        for spec in specs:
            raw = row.get(spec.column, "")
            if not raw:
                continue
            parsed = _parse_value(raw, spec.in_format)
            dest = spec.dest or spec.column
            if parsed is not None:
                new_row[dest] = parsed.strftime(spec.out_format)
                result.converted_count += 1
            else:
                result.failed_count += 1
        output.append(new_row)
    return output, result
