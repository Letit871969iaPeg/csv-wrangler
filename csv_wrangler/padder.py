"""Column value padding and alignment utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Literal

PadSide = Literal["left", "right", "both"]


class PadError(ValueError):
    """Raised when padding cannot be applied."""


@dataclass
class PadSpec:
    column: str
    width: int
    fill_char: str = " "
    side: PadSide = "right"
    truncate: bool = False

    def __post_init__(self) -> None:
        if self.width < 1:
            raise PadError(f"width must be >= 1, got {self.width!r}")
        if len(self.fill_char) != 1:
            raise PadError(
                f"fill_char must be exactly one character, got {self.fill_char!r}"
            )
        if self.side not in ("left", "right", "both"):
            raise PadError(f"side must be 'left', 'right', or 'both', got {self.side!r}")


@dataclass
class PadResult:
    total_rows: int = 0
    padded_cells: int = 0
    columns_affected: list[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"PadResult(rows={self.total_rows}, "
            f"padded_cells={self.padded_cells}, "
            f"columns={self.columns_affected})"
        )


def _pad_value(value: str, spec: PadSpec) -> str:
    """Apply padding (and optional truncation) to a single value."""
    if len(value) >= spec.width:
        if spec.truncate:
            return value[: spec.width]
        return value

    if spec.side == "left":
        return value.rjust(spec.width, spec.fill_char)
    if spec.side == "right":
        return value.ljust(spec.width, spec.fill_char)
    # both — centre, bias extra char to the right
    total_pad = spec.width - len(value)
    left_pad = total_pad // 2
    right_pad = total_pad - left_pad
    return spec.fill_char * left_pad + value + spec.fill_char * right_pad


def pad_rows(
    rows: Iterable[dict[str, str]],
    specs: list[PadSpec],
) -> tuple[Iterator[dict[str, str]], PadResult]:
    """Pad columns in *rows* according to *specs*.

    Returns a lazy iterator of transformed rows and a :class:`PadResult`
    summary populated once the iterator is exhausted.
    """
    result = PadResult(columns_affected=sorted({s.column for s in specs}))

    def _iter() -> Iterator[dict[str, str]]:
        for row in rows:
            new_row = dict(row)
            for spec in specs:
                if spec.column not in new_row:
                    raise PadError(
                        f"Column {spec.column!r} not found in row: {list(row.keys())}"
                    )
                original = new_row[spec.column]
                padded = _pad_value(original, spec)
                if padded != original:
                    result.padded_cells += 1
                new_row[spec.column] = padded
            result.total_rows += 1
            yield new_row

    return _iter(), result
