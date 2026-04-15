"""CLI subcommand: reorder columns in a CSV file."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from csv_wrangler.reorderer import ReorderError, reorder_rows


def add_reorder_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "reorder",
        help="Reorder (and optionally drop) columns in a CSV file.",
    )
    p.add_argument("input", help="Input CSV file (use - for stdin).")
    p.add_argument("columns", nargs="+", help="Column names in desired order.")
    p.add_argument("-o", "--output", default="-", help="Output file (default: stdout).")
    p.add_argument(
        "--drop-rest",
        action="store_true",
        help="Drop columns not listed in COLUMNS.",
    )
    p.set_defaults(func=_run_reorder)


def _iter_csv(path: str) -> list[dict[str, str]]:
    src = sys.stdin if path == "-" else open(path, newline="", encoding="utf-8")
    try:
        return list(csv.DictReader(src))
    finally:
        if path != "-":
            src.close()  # type: ignore[union-attr]


def _run_reorder(args: argparse.Namespace) -> int:
    try:
        rows = _iter_csv(args.input)
        result, out_iter = reorder_rows(rows, args.columns, drop_rest=args.drop_rest)
        out_rows = list(out_iter)
    except ReorderError as exc:
        print(f"reorder error: {exc}", file=sys.stderr)
        return 1

    if not out_rows:
        return 0

    dest = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(dest, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    finally:
        if args.output != "-":
            dest.close()  # type: ignore[union-attr]

    print(str(result), file=sys.stderr)
    return 0
