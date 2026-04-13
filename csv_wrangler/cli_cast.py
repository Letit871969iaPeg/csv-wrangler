"""CLI sub-command: cast — coerce column types in a CSV file."""
from __future__ import annotations

import csv
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from csv_wrangler.caster import CastError, CastSpec, cast_rows


def add_cast_subcommand(subparsers) -> None:  # noqa: ANN001
    """Register the *cast* sub-command onto *subparsers*."""
    p: ArgumentParser = subparsers.add_parser(
        "cast",
        help="Coerce column values to int, float, bool, or date.",
    )
    p.add_argument("input", help="Input CSV file (use - for stdin)")
    p.add_argument("-o", "--output", default="-", help="Output CSV file (default: stdout)")
    p.add_argument(
        "-c",
        "--cast",
        metavar="COL:TYPE",
        action="append",
        dest="casts",
        default=[],
        help="Column and target type, e.g. age:int or score:float. Repeatable.",
    )
    p.add_argument(
        "--lenient",
        action="store_true",
        default=False,
        help="On cast failure leave original value instead of raising an error.",
    )
    p.add_argument(
        "--date-format",
        default="%Y-%m-%d",
        help="strptime format string for date columns (default: %%Y-%%m-%%d).",
    )
    p.set_defaults(func=_run_cast)


def _parse_cast_args(raw: List[str], strict: bool, date_format: str) -> List[CastSpec]:
    specs: List[CastSpec] = []
    for token in raw:
        parts = token.split(":")
        if len(parts) != 2:
            raise CastError(f"Invalid cast spec {token!r}. Expected COL:TYPE.")
        col, typ = parts
        specs.append(
            CastSpec(column=col.strip(), target_type=typ.strip(),
                     date_format=date_format, strict=strict)
        )
    return specs


def _run_cast(args: Namespace) -> int:
    strict = not args.lenient
    try:
        specs = _parse_cast_args(args.casts, strict, args.date_format)
    except CastError as exc:
        print(f"cast: {exc}", file=sys.stderr)
        return 1

    in_fh = open(args.input, newline="") if args.input != "-" else sys.stdin
    out_fh = open(args.output, "w", newline="") if args.output != "-" else sys.stdout

    try:
        reader = csv.DictReader(in_fh)
        fieldnames = reader.fieldnames or []
        writer = csv.DictWriter(out_fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in cast_rows(reader, specs):
            writer.writerow(row)
    except CastError as exc:
        print(f"cast: {exc}", file=sys.stderr)
        return 1
    finally:
        if args.input != "-":
            in_fh.close()
        if args.output != "-":
            out_fh.close()

    return 0
