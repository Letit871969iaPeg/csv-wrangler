"""CLI subcommand: tokenize — split column values into tokens."""
from __future__ import annotations

import csv
import sys
from argparse import ArgumentParser, Namespace
from typing import Iterator, Dict

from csv_wrangler.tokenizer import TokenizeError, TokenizeSpec, tokenize_rows_with_result


def _iter_csv(path: str) -> Iterator[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def _parse_specs(raw: list[str]) -> list[TokenizeSpec]:
    """Parse spec strings of the form 'column[:dest]'."""
    specs: list[TokenizeSpec] = []
    for item in raw:
        parts = item.split(":")
        column = parts[0]
        dest = parts[1] if len(parts) > 1 else ""
        specs.append(TokenizeSpec(column=column, dest=dest))
    return specs


def add_tokenize_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "tokenize",
        help="Split column values into whitespace/delimiter-separated tokens.",
    )
    p.add_argument("input", help="Input CSV file")
    p.add_argument("output", help="Output CSV file (use - for stdout)")
    p.add_argument(
        "--spec",
        dest="specs",
        metavar="COLUMN[:DEST]",
        action="append",
        required=True,
        help="Column to tokenize and optional destination column name.",
    )
    p.add_argument(
        "--delimiter",
        default="",
        help="Split on this delimiter instead of whitespace.",
    )
    p.add_argument(
        "--pattern",
        default="",
        help="Split on this regex pattern instead of whitespace.",
    )
    p.add_argument(
        "--lower",
        action="store_true",
        default=False,
        help="Lowercase tokens before writing.",
    )
    p.set_defaults(func=_run_tokenize)


def _run_tokenize(args: Namespace) -> int:
    try:
        base_specs = _parse_specs(args.specs)
        specs = [
            TokenizeSpec(
                column=s.column,
                dest=s.dest,
                delimiter=args.delimiter,
                pattern=args.pattern,
                lower=args.lower,
            )
            for s in base_specs
        ]
    except TokenizeError as exc:
        print(f"tokenize: configuration error: {exc}", file=sys.stderr)
        return 1

    rows = _iter_csv(args.input)
    result, it = tokenize_rows_with_result(rows, specs)

    try:
        first = next(it)  # type: ignore[call-overload]
    except StopIteration:
        print("tokenize: input file is empty", file=sys.stderr)
        return 1
    except TokenizeError as exc:
        print(f"tokenize: {exc}", file=sys.stderr)
        return 1

    fieldnames = list(first.keys())
    out = open(args.output, "w", newline="", encoding="utf-8") if args.output != "-" else sys.stdout
    writer = csv.DictWriter(out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(first)
    for row in it:
        writer.writerow(row)
    if args.output != "-":
        out.close()

    print(
        f"tokenize: {result.tokenized_count} rows processed, "
        f"columns created: {result.columns_created}",
        file=sys.stderr,
    )
    return 0
