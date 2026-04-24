"""CLI sub-command: scale — min-max or z-score normalise numeric columns."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import Iterator

from csv_wrangler.scaler import ScaleError, ScaleSpec, scale_rows


def _iter_csv(path: str) -> Iterator[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def _parse_specs(raw: list[str]) -> list[ScaleSpec]:
    """Parse strings like 'column:method' or 'column:method:dest'."""
    specs: list[ScaleSpec] = []
    for token in raw:
        parts = token.split(":")
        if len(parts) < 2:
            raise ScaleError(
                f"invalid spec {token!r}; expected column:method[:dest]"
            )
        column, method = parts[0], parts[1]
        dest = parts[2] if len(parts) >= 3 else ""
        specs.append(ScaleSpec(column=column, method=method, dest=dest))
    return specs


def add_scale_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "scale",
        help="min-max or z-score scale numeric columns",
    )
    p.add_argument("input", help="input CSV file")
    p.add_argument("-o", "--output", default="-", help="output file (default: stdout)")
    p.add_argument(
        "--spec",
        dest="specs",
        metavar="COL:METHOD[:DEST]",
        action="append",
        default=[],
        required=True,
        help="scaling spec, e.g. score:minmax or score:zscore:score_z",
    )
    p.set_defaults(func=_run_scale)


def _run_scale(args: argparse.Namespace) -> int:
    try:
        specs = _parse_specs(args.specs)
    except ScaleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        rows = list(_iter_csv(args.input))
    except OSError as exc:
        print(f"error reading input: {exc}", file=sys.stderr)
        return 1

    try:
        out_rows, result = scale_rows(rows, specs)
    except ScaleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not out_rows:
        print("warning: no rows to write", file=sys.stderr)
        return 0

    fieldnames = list(out_rows[0].keys())
    if args.output == "-":
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    else:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(out_rows)

    print(result, file=sys.stderr)
    return 0
