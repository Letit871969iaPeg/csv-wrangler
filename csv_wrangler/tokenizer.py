"""Tokenizer: split a column's string value into tokens and write them to a new column."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List


class TokenizeError(ValueError):
    """Raised when tokenization configuration or execution fails."""


@dataclass
class TokenizeSpec:
    column: str
    dest: str = ""
    delimiter: str = ""
    pattern: str = ""
    lower: bool = False

    def __post_init__(self) -> None:
        if not self.column:
            raise TokenizeError("column must not be empty")
        if self.delimiter and self.pattern:
            raise TokenizeError("specify delimiter or pattern, not both")
        if not self.dest:
            self.dest = f"{self.column}_tokens"

    def tokenize(self, value: str) -> List[str]:
        text = value.lower() if self.lower else value
        if self.pattern:
            tokens = re.split(self.pattern, text)
        elif self.delimiter:
            tokens = text.split(self.delimiter)
        else:
            tokens = text.split()
        return [t for t in tokens if t]


@dataclass
class TokenizeResult:
    tokenized_count: int = 0
    skipped_count: int = 0
    columns_created: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"TokenizeResult(tokenized={self.tokenized_count}, "
            f"skipped={self.skipped_count}, "
            f"columns={self.columns_created})"
        )


def tokenize_rows(
    rows: Iterable[Dict[str, str]],
    specs: List[TokenizeSpec],
) -> Iterator[Dict[str, str]]:
    """Yield rows with each spec's destination column populated with tokens."""
    for row in rows:
        out = dict(row)
        for spec in specs:
            if spec.column not in row:
                raise TokenizeError(f"column not found: {spec.column!r}")
            tokens = spec.tokenize(row[spec.column])
            out[spec.dest] = "|".join(tokens)
        yield out


def tokenize_rows_with_result(
    rows: Iterable[Dict[str, str]],
    specs: List[TokenizeSpec],
) -> tuple[TokenizeResult, Iterator[Dict[str, str]]]:
    """Return a (result, iterator) pair; result is populated after iteration."""
    result = TokenizeResult(
        columns_created=[s.dest for s in specs]
    )

    def _iter() -> Iterator[Dict[str, str]]:
        for row in rows:
            out = dict(row)
            any_tokenized = False
            for spec in specs:
                if spec.column not in row:
                    result.skipped_count += 1
                    continue
                tokens = spec.tokenize(row[spec.column])
                out[spec.dest] = "|".join(tokens)
                any_tokenized = True
            if any_tokenized:
                result.tokenized_count += 1
            yield out

    return result, _iter()
