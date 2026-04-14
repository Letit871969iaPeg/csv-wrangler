"""Normalize string values in CSV columns (strip, lowercase, uppercase, titlecase)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

VALID_MODES = {"strip", "lower", "upper", "title"}


class NormalizeError(ValueError):
    """Raised when normalization configuration or input is invalid."""


@dataclass
class NormalizeSpec:
    column: str
    mode: str

    def __post_init__(self) -> None:
        if self.mode not in VALID_MODES:
            raise NormalizeError(
                f"Invalid mode {self.mode!r}. Must be one of: {sorted(VALID_MODES)}"
            )


@dataclass
class NormalizeResult:
    normalized_count: int = 0
    skipped_columns: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [f"normalized={self.normalized_count}"]
        if self.skipped_columns:
            parts.append(f"skipped={self.skipped_columns}")
        return f"NormalizeResult({', '.join(parts)})"


def _apply_mode(value: str, mode: str) -> str:
    if mode == "strip":
        return value.strip()
    if mode == "lower":
        return value.lower()
    if mode == "upper":
        return value.upper()
    if mode == "title":
        return value.title()
    raise NormalizeError(f"Unknown mode: {mode!r}")


def normalize_rows(
    rows: Iterable[dict[str, str]],
    specs: list[NormalizeSpec],
) -> tuple[Iterator[dict[str, str]], NormalizeResult]:
    """Apply normalization specs to rows. Returns (iterator, result)."""
    result = NormalizeResult()
    rows_list = list(rows)

    if not rows_list:
        return iter([]), result

    headers = set(rows_list[0].keys())
    active_specs: list[NormalizeSpec] = []
    for spec in specs:
        if spec.column not in headers:
            result.skipped_columns.append(spec.column)
        else:
            active_specs.append(spec)

    def _iter() -> Iterator[dict[str, str]]:
        for row in rows_list:
            new_row = dict(row)
            for spec in active_specs:
                new_row[spec.column] = _apply_mode(new_row[spec.column], spec.mode)
                result.normalized_count += 1
            yield new_row

    return _iter(), result
