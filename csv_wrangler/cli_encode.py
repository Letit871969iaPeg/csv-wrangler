"""CLI sub-command: encode — encode column values with a chosen scheme."""
from __future__ import annotations

import csv
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from csv_wrangler.encoder import EncodeError, EncodeSpec, encode_rows


def add_encode_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    p: ArgumentParser = subparsers.add_parser(
        "encode",
        help="Encode column values (base64, hex, url, md5, sha256).",
    )
    p.add_argument("input", help="Input CSV file (use '-' for stdin).")
    p.add_argument("-o", "--output", default="-", help="Output CSV file (default: stdout).")
    p.add_argument(
        "-e",
        "--encode",
        metavar="COL:SCHEME[:DEST]",
        action="append",
        dest="specs",
        required=True,
        help="Encoding spec. Repeat for multiple columns.",
    )
    p.set_defaults(func=_run_encode)


def _parse_specs(raw: List[str]) -> List[EncodeSpec]:
    specs: List[EncodeSpec] = []
    for token in raw:
        parts = token.split(":")
        if len(parts) < 2:
            raise EncodeError(f"Invalid spec '{token}'. Expected COL:SCHEME[:DEST].")
        col, scheme = parts[0], parts[1]
        dest = parts[2] if len(parts) >= 3 else ""
        specs.append(EncodeSpec(column=col, scheme=scheme, dest=dest))
    return specs


def _run_encode(args: Namespace) -> int:
    try:
        specs = _parse_specs(args.specs)
    except EncodeError as exc:
        print(f"encode: {exc}", file=sys.stderr)
        return 1

    in_fh = sys.stdin if args.input == "-" else open(args.input, newline="", encoding="utf-8")
    out_fh = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")

    try:
        reader = csv.DictReader(in_fh)
        rows = list(reader)
        if not rows:
            return 0
        encoded_iter, result = encode_rows(rows, specs)
        encoded_rows = list(encoded_iter)
        writer = csv.DictWriter(out_fh, fieldnames=list(encoded_rows[0].keys()))
        writer.writeheader()
        writer.writerows(encoded_rows)
        if result.skipped_columns:
            print(f"encode: skipped missing columns: {result.skipped_columns}", file=sys.stderr)
    finally:
        if in_fh is not sys.stdin:
            in_fh.close()
        if out_fh is not sys.stdout:
            out_fh.close()

    return 0
