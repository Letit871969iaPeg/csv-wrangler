"""CLI subcommand: parse-dates."""
from __future__ import annotations
import argparse
import csv
import sys
from typing import Iterator

from csv_wrangler.dateparser import DateParseError, DateSpec, parse_dates


def _iter_csv(path: str) -> Iterator[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def _parse_specs(raw: list[str]) -> list[DateSpec]:
    specs: list[DateSpec] = []
    for token in raw:
        parts = token.split(":")
        column = parts[0]
        in_fmt = parts[1] if len(parts) > 1 else None
        out_fmt = parts[2] if len(parts) > 2 else "%Y-%m-%d"
        dest = parts[3] if len(parts) > 3 else None
        specs.append(DateSpec(column=column, in_format=in_fmt, out_format=out_fmt, dest=dest))
    return specs


def add_date_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("parse-dates", help="Parse and reformat date columns")
    p.add_argument("input", help="Input CSV file")
    p.add_argument("--spec", metavar="COL[:IN_FMT[:OUT_FMT[:DEST]]]",
                   action="append", dest="specs", default=[],
                   help="Date column spec (repeatable)")
    p.add_argument("-o", "--output", default="-", help="Output file (default: stdout)")
    p.add_argument("--summary", action="store_true", help="Print summary to stderr")
    p.set_defaults(func=_run_date)


def _run_date(args: argparse.Namespace) -> int:
    try:
        specs = _parse_specs(args.specs)
    except DateParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rows = list(_iter_csv(args.input))
    if not rows:
        return 0

    out_rows, result = parse_dates(rows, specs)

    if args.output == "-":
        writer = csv.DictWriter(sys.stdout, fieldnames=list(out_rows[0].keys()))
    else:
        fh = open(args.output, "w", newline="", encoding="utf-8")
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))

    writer.writeheader()
    writer.writerows(out_rows)

    if args.output != "-":
        fh.close()

    if args.summary:
        print(str(result), file=sys.stderr)

    return 0
