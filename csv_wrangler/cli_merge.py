"""CLI sub-command: merge — stack multiple CSV files vertically."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterator

from csv_wrangler.merger import MergeError, merge_rows

Row = dict[str, str]


def _iter_csv(path: str) -> list[Row]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def add_merge_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "merge",
        help="Stack multiple CSV files vertically into one output file.",
    )
    p.add_argument(
        "inputs",
        nargs="+",
        metavar="INPUT",
        help="Two or more CSV files to merge.",
    )
    p.add_argument(
        "-o", "--output",
        metavar="OUTPUT",
        default="-",
        help="Output CSV file (default: stdout).",
    )
    p.add_argument(
        "--fill-missing",
        action="store_true",
        default=False,
        help="Fill missing columns with an empty string instead of raising an error.",
    )
    p.add_argument(
        "--fill-value",
        metavar="VALUE",
        default="",
        help="Value to use when --fill-missing is active (default: empty string).",
    )
    p.add_argument(
        "--allow-column-mismatch",
        action="store_true",
        default=False,
        help="Do not raise an error when column sets differ across sources.",
    )
    p.set_defaults(func=_run_merge)


def _run_merge(args: argparse.Namespace) -> int:
    if len(args.inputs) < 2:
        print("error: merge requires at least two input files.", file=sys.stderr)
        return 1

    sources = []
    for path in args.inputs:
        if not Path(path).exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        sources.append(_iter_csv(path))

    try:
        result = merge_rows(
            sources,
            require_same_columns=not (args.fill_missing or args.allow_column_mismatch),
            fill_missing=args.fill_missing,
            fill_value=args.fill_value,
        )
    except MergeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not result.rows:
        return 0

    fieldnames = list(result.rows[0].keys())

    if args.output == "-":
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(result.rows)
    else:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(result.rows)

    print(
        f"Merged {result.total_rows} row(s) from {result.source_count} source(s).",
        file=sys.stderr,
    )
    return 0
