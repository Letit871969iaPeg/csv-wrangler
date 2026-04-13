"""CLI sub-command: sort — sort a CSV file by one or more columns."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Optional

from csv_wrangler.sorter import SortError, parse_sort_keys, sort_rows


def add_sort_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *sort* sub-command on an existing subparsers action."""
    p = subparsers.add_parser(
        "sort",
        help="Sort CSV rows by one or more columns.",
        description=(
            "Sort rows in INPUT by KEY columns.  Each KEY may include a "
            "direction suffix separated by a colon, e.g. 'age:desc'."
        ),
    )
    p.add_argument("input", metavar="INPUT", help="Path to the input CSV file.")
    p.add_argument(
        "keys",
        metavar="KEY",
        nargs="+",
        help="Column name(s) to sort by, optionally suffixed with :asc or :desc.",
    )
    p.add_argument(
        "-o", "--output",
        metavar="OUTPUT",
        default=None,
        help="Write sorted CSV to OUTPUT instead of stdout.",
    )
    p.set_defaults(func=_run_sort)


def _run_sort(args: argparse.Namespace) -> int:
    """Execute the sort sub-command; returns an exit code."""
    try:
        sort_keys = parse_sort_keys(args.keys)
    except SortError as exc:
        print(f"sort: {exc}", file=sys.stderr)
        return 1

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"sort: file not found: {input_path}", file=sys.stderr)
        return 1

    with input_path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames: List[str] = list(reader.fieldnames or [])
        try:
            sorted_rows = list(sort_rows(list(reader), sort_keys))
        except SortError as exc:
            print(f"sort: {exc}", file=sys.stderr)
            return 1

    out_stream = (
        open(args.output, "w", newline="")  # noqa: WPS515
        if args.output
        else sys.stdout
    )
    try:
        writer = csv.DictWriter(out_stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted_rows)
    finally:
        if args.output:
            out_stream.close()

    return 0
