"""Infer column types from CSV data."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable


class TypeInferError(Exception):
    pass


@dataclass
class ColumnTypeInfo:
    column: str
    inferred_type: str  # int, float, bool, date, string
    sample_count: int = 0
    match_count: int = 0

    @property
    def confidence(self) -> float:
        if self.sample_count == 0:
            return 0.0
        return self.match_count / self.sample_count

    def __str__(self) -> str:
        return (
            f"{self.column}: {self.inferred_type} "
            f"(confidence={self.confidence:.0%}, samples={self.sample_count})"
        )


_BOOL_VALUES = {"true", "false", "yes", "no", "1", "0"}


def _try_int(v: str) -> bool:
    try:
        int(v)
        return True
    except ValueError:
        return False


def _try_float(v: str) -> bool:
    try:
        float(v)
        return True
    except ValueError:
        return False


def _try_date(v: str) -> bool:
    import re
    return bool(re.match(r"\d{4}-\d{2}-\d{2}", v))


def infer_column_type(column: str, values: Iterable[str]) -> ColumnTypeInfo:
    samples = [v.strip() for v in values if v.strip() != ""]
    n = len(samples)
    if n == 0:
        return ColumnTypeInfo(column=column, inferred_type="string", sample_count=0, match_count=0)

    for type_name, checker in [
        ("bool", lambda v: v.lower() in _BOOL_VALUES),
        ("int", _try_int),
        ("float", _try_float),
        ("date", _try_date),
    ]:
        matches = sum(1 for v in samples if checker(v))
        if matches / n >= 0.9:
            return ColumnTypeInfo(column=column, inferred_type=type_name, sample_count=n, match_count=matches)

    return ColumnTypeInfo(column=column, inferred_type="string", sample_count=n, match_count=n)


def infer_types(rows: Iterable[dict[str, str]]) -> dict[str, ColumnTypeInfo]:
    all_rows = list(rows)
    if not all_rows:
        return {}
    columns = list(all_rows[0].keys())
    return {
        col: infer_column_type(col, [r.get(col, "") for r in all_rows])
        for col in columns
    }
