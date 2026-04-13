"""Column value masking (redaction / partial masking) for sensitive data."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

_VALID_MODES = {"full", "partial", "first", "last"}


class MaskError(Exception):
    """Raised when masking configuration or execution fails."""


@dataclass
class MaskSpec:
    column: str
    mode: str = "full"          # full | partial | first | last
    char: str = "*"
    keep: int = 4               # chars to keep for partial/first/last

    def __post_init__(self) -> None:
        if self.mode not in _VALID_MODES:
            raise MaskError(
                f"Invalid mode {self.mode!r}. Choose from {sorted(_VALID_MODES)}."
            )
        if len(self.char) != 1:
            raise MaskError("mask char must be exactly one character.")
        if self.keep < 0:
            raise MaskError("keep must be >= 0.")


@dataclass
class MaskResult:
    masked_count: int = 0
    skipped_columns: list[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"MaskResult(masked_count={self.masked_count}, "
            f"skipped={self.skipped_columns})"
        )


def _mask_value(value: str, spec: MaskSpec) -> str:
    """Apply masking to a single string value."""
    if not value:
        return value
    c, k = spec.char, spec.keep
    if spec.mode == "full":
        return c * len(value)
    if spec.mode == "partial":
        visible = min(k, len(value))
        return c * (len(value) - visible) + value[-visible:]
    if spec.mode == "first":
        visible = min(k, len(value))
        return value[:visible] + c * (len(value) - visible)
    # last
    visible = min(k, len(value))
    return c * (len(value) - visible) + value[-visible:]


def mask_rows(
    rows: Iterable[dict[str, str]],
    specs: list[MaskSpec],
) -> tuple[Iterator[dict[str, str]], MaskResult]:
    """Return an iterator of masked rows and a MaskResult summary."""
    result = MaskResult()
    rows_list = list(rows)

    if not rows_list:
        return iter([]), result

    headers = set(rows_list[0].keys())
    active: list[MaskSpec] = []
    for spec in specs:
        if spec.column not in headers:
            result.skipped_columns.append(spec.column)
        else:
            active.append(spec)

    def _iter() -> Iterator[dict[str, str]]:
        for row in rows_list:
            new_row = dict(row)
            for spec in active:
                original = new_row.get(spec.column, "")
                new_row[spec.column] = _mask_value(original, spec)
                if original:
                    result.masked_count += 1
            yield new_row

    return _iter(), result
