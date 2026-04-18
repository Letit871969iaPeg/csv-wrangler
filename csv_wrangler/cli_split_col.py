"""CLI subcommand: split-col — split a column into multiple columns."""
from __future__ import annotations
import argparse
import csv
import sys
from csv_wrangler.splitter_col import ColSplitError, ColSplitSpec, _iter


def add_split_col_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "split-col",
        help="Split one column into multiple columns by a delimiter",
    )
    p.add_argument("input", help="Input CSV file (use - for stdin)")
    p.add_argument("-o", "--output", default="-", help="Output CSV file (default: stdout)")
    p.add_argument("-c", "--column", required=True, help="Column to split")
    p.add_argument("-d", "--delimiter", required=True, help="Delimiter to split on")
    p.add_argument("-i", "--into", required=True, nargs="+", help="Target column names")
    p.add_argument("--keep-source", action="store_true", help="Keep original column")
    p.set_defaults(func=_run_split_col)


def _iter_csv(path: str) -> tuple[list[str], list[dict[str, str]]]:
    fh = sys.stdin if path == "-" else open(path, newline="", encoding="utf-8")
    try:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    finally:
        if path != "-":
            fh.close()
    return fieldnames, rows


def _run_split_col(args: argparse.Namespace) -> int:
    try:
        spec = ColSplitSpec(
            column=args.column,
            delimiter=args.delimiter,
            into=args.into,
            drop_source=not args.keep_source,
        )
    except ColSplitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _, rows = _iter_csv(args.input)

    try:
        out_rows = list(_iter(rows, spec))
    except ColSplitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not out_rows:
        return 0

    fieldnames = list(out_rows[0].keys())
    fh = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    finally:
        if args.output != "-":
            fh.close()
    return 0
