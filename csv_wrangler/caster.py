"""Type-casting module: coerce CSV column values to int, float, bool, or date."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Iterable, Iterator, List


class CastError(Exception):
    """Raised when a cast specification is invalid or a value cannot be coerced."""


_BOOL_TRUE = {"1", "true", "yes", "y"}
_BOOL_FALSE = {"0", "false", "no", "n", ""}


@dataclass
class CastSpec:
    column: str
    target_type: str  # "int" | "float" | "bool" | "date"
    date_format: str = "%Y-%m-%d"
    strict: bool = True  # if False, leave original value on failure

    def __post_init__(self) -> None:
        valid = {"int", "float", "bool", "date"}
        if self.target_type not in valid:
            raise CastError(
                f"Unknown target type {self.target_type!r}. Choose from {valid}."
            )

    def cast(self, value: str) -> object:
        """Coerce *value* to the target type."""
        try:
            if self.target_type == "int":
                return int(value)
            if self.target_type == "float":
                return float(value)
            if self.target_type == "bool":
                low = value.strip().lower()
                if low in _BOOL_TRUE:
                    return True
                if low in _BOOL_FALSE:
                    return False
                raise ValueError(f"Cannot parse {value!r} as bool")
            if self.target_type == "date":
                return date.fromisoformat(value) if self.date_format == "%Y-%m-%d" \
                    else __import__("datetime").datetime.strptime(value, self.date_format).date()
        except (ValueError, TypeError) as exc:
            if self.strict:
                raise CastError(
                    f"Column {self.column!r}: cannot cast {value!r} to "
                    f"{self.target_type}: {exc}"
                ) from exc
            return value
        return value  # unreachable but satisfies type checkers


@dataclass
class CastResult:
    casted: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"CastResult(casted={self.casted}, skipped={self.skipped}, "
            f"errors={len(self.errors)})"
        )


def cast_rows(
    rows: Iterable[Dict[str, str]],
    specs: List[CastSpec],
) -> Iterator[Dict[str, object]]:
    """Yield rows with column values coerced according to *specs*.

    Columns not mentioned in *specs* are passed through unchanged.
    """
    if not specs:
        yield from rows  # type: ignore[misc]
        return

    spec_map = {s.column: s for s in specs}
    for row in rows:
        new_row: Dict[str, object] = {}
        for key, val in row.items():
            if key in spec_map:
                new_row[key] = spec_map[key].cast(val)
            else:
                new_row[key] = val
        yield new_row
