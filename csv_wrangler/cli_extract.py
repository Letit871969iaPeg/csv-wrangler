"""CLI subcommand: extract — pull regex capture groups into new columns."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import Iterator

from csv_wrangler.extractor import ExtractError, ExtractSpec, extract_rows


def _iter_csv(path: str) -> Iterator[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def _parse_specs(raw: list[str]) -> list[ExtractSpec]:
    """Parse strings like 'column:pattern', 'column:pattern:dest', or
    'column:pattern:dest:group' into ExtractSpec objects."""
    specs: list[ExtractSpec] = []
    for token in raw:
        parts = token.split(":", 3)
        if len(parts) < 2:
            raise ExtractError(
                f"spec must be 'column:pattern[:dest[:group]]', got: {token!r}"
            )
        column = parts[0]
        pattern = parts[1]
        dest = parts[2] if len(parts) > 2 else ""
        group = int(parts[3]) if len(parts) > 3 else 1
        specs.append(ExtractSpec(column=column, pattern=pattern, dest=dest, group=group))
    return specs


def add_extract_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "extract",
        help="Extract regex capture groups into columns.",
    )
    p.add_argument("input", help="Input CSV file (use - for stdin).")
    p.add_argument("-o", "--output", default="-", help="Output CSV file (default: stdout).")
    p.add_argument(
        "-s",
        "--spec",
        dest="specs",
        action="append",
        default=[],
        metavar="COL:PATTERN[:DEST[:GROUP]]",
        help="Extraction spec; may be repeated.",
    )
    p.set_defaults(func=_run_extract)


def _run_extract(args: argparse.Namespace) -> int:
    try:
        specs = _parse_specs(args.specs)
    except ExtractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    source = sys.stdin if args.input == "-" else None
    rows = (
        csv.DictReader(source)
        if source
        else _iter_csv(args.input)
    )

    try:
        it, result = extract_rows(iter(rows), specs)
        first = next(it, None)
        if first is None:
            return 0

        out = open(args.output, "w", newline="", encoding="utf-8") if args.output != "-" else sys.stdout
        try:
            writer = csv.DictWriter(out, fieldnames=list(first.keys()))
            writer.writeheader()
            writer.writerow(first)
            writer.writerows(it)
        finally:
            if args.output != "-":
                out.close()

        print(
            f"extract: {result.matched_count} matched, {result.unmatched_count} unmatched",
            file=sys.stderr,
        )
        return 0
    except ExtractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
