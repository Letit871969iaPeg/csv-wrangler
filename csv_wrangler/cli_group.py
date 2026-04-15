"""CLI sub-command: group — group rows by key columns and count."""
from __future__ import annotations

import csv
import sys
from argparse import ArgumentParser, Namespace
from typing import Iterator, Dict

from csv_wrangler.grouper import GroupError, group_rows_with_result


def _iter_csv(path: str) -> Iterator[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        yield from reader


def add_group_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "group",
        help="Group rows by key columns and emit a count per group.",
    )
    p.add_argument("input", help="Input CSV file path.")
    p.add_argument(
        "-k",
        "--key",
        dest="keys",
        metavar="COLUMN",
        action="append",
        required=True,
        help="Key column to group by (repeatable).",
    )
    p.add_argument(
        "-c",
        "--count-column",
        default="_count",
        metavar="NAME",
        help="Name for the output count column (default: _count).",
    )
    p.add_argument(
        "-o",
        "--output",
        default="-",
        metavar="FILE",
        help="Output CSV file path (default: stdout).",
    )
    p.set_defaults(func=_run_group)


def _run_group(args: Namespace) -> int:
    try:
        rows = list(_iter_csv(args.input))
        output_rows, result = group_rows_with_result(
            rows,
            key_columns=args.keys,
            count_column=args.count_column,
        )
    except GroupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not output_rows:
        print("warning: no groups produced.", file=sys.stderr)
        return 0

    fieldnames = list(output_rows[0].keys())

    if args.output == "-":
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    else:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)

    print(str(result), file=sys.stderr)
    return 0
