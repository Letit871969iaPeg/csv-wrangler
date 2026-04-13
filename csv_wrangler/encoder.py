"""Encode column values using common schemes (base64, hex, url, hash)."""
from __future__ import annotations

import base64
import hashlib
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List

_SUPPORTED = {"base64", "hex", "url", "md5", "sha256"}


class EncodeError(Exception):
    """Raised when encoding configuration or execution fails."""


@dataclass
class EncodeSpec:
    column: str
    scheme: str
    dest: str = ""

    def __post_init__(self) -> None:
        if self.scheme not in _SUPPORTED:
            raise EncodeError(
                f"Unsupported scheme '{self.scheme}'. Choose from: {sorted(_SUPPORTED)}"
            )
        if not self.dest:
            self.dest = self.column


@dataclass
class EncodeResult:
    encoded_count: int = 0
    skipped_columns: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"EncodeResult(encoded={self.encoded_count}, "
            f"skipped={self.skipped_columns})"
        )


def _encode_value(value: str, scheme: str) -> str:
    raw = value.encode()
    if scheme == "base64":
        return base64.b64encode(raw).decode()
    if scheme == "hex":
        return raw.hex()
    if scheme == "url":
        return urllib.parse.quote(value)
    if scheme == "md5":
        return hashlib.md5(raw).hexdigest()
    if scheme == "sha256":
        return hashlib.sha256(raw).hexdigest()
    raise EncodeError(f"Unknown scheme: {scheme}")


def encode_rows(
    rows: Iterable[Dict[str, str]],
    specs: List[EncodeSpec],
) -> tuple[Iterator[Dict[str, str]], EncodeResult]:
    result = EncodeResult()
    rows_list = list(rows)
    if not rows_list:
        return iter([]), result

    headers = set(rows_list[0].keys())
    active: List[EncodeSpec] = []
    for spec in specs:
        if spec.column not in headers:
            result.skipped_columns.append(spec.column)
        else:
            active.append(spec)

    def _iter() -> Iterator[Dict[str, str]]:
        for row in rows_list:
            new_row = dict(row)
            for spec in active:
                new_row[spec.dest] = _encode_value(row[spec.column], spec.scheme)
                result.encoded_count += 1
            yield new_row

    return _iter(), result
