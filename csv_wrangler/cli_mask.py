"""CLI sub-command: mask — redact or partially mask column values."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import List

from csv_wrangler.masker import MaskError, MaskSpec, mask_rows


def add_mask_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "mask",
        help="Redact or partially mask column values.",
    )
    p.add_argument("input", help="Input CSV file (use - for stdin).")
    p.add_argument("-o", "--output", default="-", help="Output CSV file (default: stdout).")
    p.add_argument(
        "-s",
        "--spec",
        dest="specs",
        action="append",
        required=True,
        metavar="COL[:MODE[:KEEP[:CHAR]]]",
        help=(
            "Mask spec. Format: column[:mode[:keep[:char]]]. "
            "mode is full|partial|first|last (default full). "
            "keep is number of chars to reveal (default 4). "
            "char is mask character (default *). "
            "May be repeated."
        ),
    )
    p.set_defaults(func=_run_mask)


def _parse_specs(raw_specs: List[str]) -> List[MaskSpec]:
    """Parse raw spec strings into MaskSpec objects.

    Each spec string has the format: column[:mode[:keep[:char]]]
    Raises ValueError if the 'keep' field is not a valid integer.
    """
    specs: List[MaskSpec] = []
    for raw in raw_specs:
        parts = raw.split(":")
        column = parts[0]
        mode = parts[1] if len(parts) > 1 else "full"
        char = parts[3] if len(parts) > 3 else "*"
        try:
            keep = int(parts[2]) if len(parts) > 2 else 4
        except ValueError:
            raise ValueError(
                f"Invalid 'keep' value {parts[2]!r} in spec {raw!r}: must be an integer."
            )
        specs.append(MaskSpec(column=column, mode=mode, char=char, keep=keep))
    return specs


def _run_mask(args: argparse.Namespace) -> int:
    try:
        specs = _parse_specs(args.specs)
    except (MaskError, ValueError) as exc:
        print(f"mask: configuration error: {exc}", file=sys.stderr)
        return 1

    try:
        in_fh = sys.stdin if args.input == "-" else open(args.input, newline="", encoding="utf-8")
        reader = csv.DictReader(in_fh)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    except OSError as exc:
        print(f"mask: cannot open input: {exc}", file=sys.stderr)
        return 1

    row_iter, result = mask_rows(rows, specs)
    masked_rows = list(row_iter)

    try:
        out_fh = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")
        writer = csv.DictWriter(out_fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(masked_rows)
    except OSError as exc:
        print(f"mask: cannot write output: {exc}", file=sys.stderr)
        return 1
    finally:
        if args.input != "-":
            in_fh.close()  # type: ignore[union-attr]
        if args.output != "-":
            out_fh.close()  # type: ignore[union-attr]

    if result.skipped_columns:
        print(f"mask: warning: columns not found: {result.skipped_columns}", file=sys.stderr)

    print(
        f"mask: {result.masked_count} value(s) masked across {len(specs)} spec(s).",
        file=sys.stderr,
    )
    return 0
