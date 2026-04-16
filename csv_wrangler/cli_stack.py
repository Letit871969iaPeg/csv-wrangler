"""CLI subcommand: stack (melt/unpivot columns into key-value rows)."""
from __future__ import annotations
import csv
import sys
from argparse import ArgumentParser, Namespace
from csv_wrangler.stacker import StackError, stack_rows


def add_stack_subcommand(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "stack",
        help="Melt value columns into key-value rows (unpivot).",
    )
    p.add_argument("input", help="Input CSV file (- for stdin)")
    p.add_argument("--id-columns", required=True, help="Comma-separated id column names to keep")
    p.add_argument("--key-column", default="key", help="Name for the new key column")
    p.add_argument("--value-column", default="value", help="Name for the new value column")
    p.add_argument("-o", "--output", default="-", help="Output CSV file (- for stdout)")
    p.set_defaults(func=_run_stack)


def _iter_csv(path: str):
    fh = sys.stdin if path == "-" else open(path, newline="", encoding="utf-8")
    try:
        yield from csv.DictReader(fh)
    finally:
        if path != "-":
            fh.close()


def _run_stack(args: Namespace) -> int:
    id_cols = [c.strip() for c in args.id_columns.split(",") if c.strip()]
    try:
        it, result = stack_rows(
            _iter_csv(args.input),
            id_columns=id_cols,
            key_column=args.key_column,
            value_column=args.value_column,
        )
        rows = list(it)
    except StackError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print(str(result), file=sys.stderr)
        return 0

    out_fh = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(out_fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if args.output != "-":
            out_fh.close()

    print(str(result), file=sys.stderr)
    return 0
