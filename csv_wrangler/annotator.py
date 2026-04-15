"""Row annotation: add computed columns derived from existing column values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Iterator, List


class AnnotateError(Exception):
    """Raised when annotation cannot be applied."""


@dataclass
class AnnotateSpec:
    column: str
    expression: Callable[[Dict[str, str]], str]
    overwrite: bool = False

    def __post_init__(self) -> None:
        if not self.column:
            raise AnnotateError("column name must not be empty")
        if not callable(self.expression):
            raise AnnotateError("expression must be callable")


@dataclass
class AnnotateResult:
    added_columns: List[str] = field(default_factory=list)
    overwritten_columns: List[str] = field(default_factory=list)
    row_count: int = 0

    def __str__(self) -> str:
        added = ", ".join(self.added_columns) or "none"
        over = ", ".join(self.overwritten_columns) or "none"
        return (
            f"AnnotateResult(rows={self.row_count}, "
            f"added=[{added}], overwritten=[{over}])"
        )


def annotate_rows(
    rows: Iterable[Dict[str, str]],
    specs: List[AnnotateSpec],
) -> tuple[Iterator[Dict[str, str]], AnnotateResult]:
    """Yield rows with new columns appended according to *specs*."""
    result = AnnotateResult()
    sample: Dict[str, str] = {}

    def _iter() -> Iterator[Dict[str, str]]:
        nonlocal sample
        for i, row in enumerate(rows):
            if i == 0:
                sample = row
                for spec in specs:
                    if spec.column in row:
                        if not spec.overwrite:
                            raise AnnotateError(
                                f"column '{spec.column}' already exists; "
                                "set overwrite=True to replace it"
                            )
                        result.overwritten_columns.append(spec.column)
                    else:
                        result.added_columns.append(spec.column)
            out = dict(row)
            for spec in specs:
                try:
                    out[spec.column] = spec.expression(row)
                except Exception as exc:  # noqa: BLE001
                    raise AnnotateError(
                        f"expression for column '{spec.column}' failed on row {i}: {exc}"
                    ) from exc
            result.row_count += 1
            yield out

    return _iter(), result
