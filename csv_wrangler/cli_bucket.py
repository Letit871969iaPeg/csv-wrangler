"""CLI subcommand: bucket — assign numeric values into labeled bins."""
from __future__ import annotations

import csv
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from csv_wrangler.bucketer import BucketError, BucketSpec, bucket_rows


def _parse_specs(raw: List[str]) -> List[BucketSpec]:
    """Parse specs of the form ``column:e0,e1,...:label0,label1,...[:dest]``."""
    specs: List[BucketSpec] = []
    for token in raw:
        parts = token.split(":")
        if len(parts) < 3:
            raise BucketError(
                f"invalid bucket spec {token!r}; "
                "expected column:edges:labels[:dest]"
            )
        column = parts[0]
        try:
            edges = [float(e) for e in parts[1].split(",")]
        except ValueError as exc:
            raise BucketError(f"non-numeric edge in spec {token!r}: {exc}") from exc
        labels = parts[2].split(",")
        dest = parts[3] if len(parts) >= 4 else ""
        specs.append(
            BucketSpec(column=column, edges=edges, labels=labels, dest=dest)
        )
    return specs


def add_bucket_subcommand(sub) -> None:  # type: ignore[no-untyped-def]
    p: ArgumentParser = sub.add_parser(
        "bucket",
        help="assign numeric column values into labeled bins",
    )
    p.add_argument("input", nargs="?", default="-", help="input CSV (default: stdin)")
    p.add_argument("-o", "--output", default="-", help="output CSV (default: stdout)")
    p.add_argument(
        "-b",
        "--bucket",
        dest="specs",
        metavar="SPEC",
        action="append",
        default=[],
        required=True,
        help="bucket spec: column:e0,e1,...:label0,label1,...[:dest]",
    )
    p.set_defaults(func=_run_bucket)


def _iter_csv(path: str):
    if path == "-":
        reader = csv.DictReader(sys.stdin)
        yield from reader
    else:
        with open(path, newline="", encoding="utf-8") as fh:
            yield from csv.DictReader(fh)


def _run_bucket(args: Namespace) -> int:
    try:
        specs = _parse_specs(args.specs)
    except BucketError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rows = list(_iter_csv(args.input))
    if not rows:
        return 0

    row_iter, result = bucket_rows(rows, specs)
    out_rows = list(row_iter)

    out = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(out, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)
    finally:
        if args.output != "-":
            out.close()

    print(
        f"bucketed {result.bucketed_count} values, "
        f"{result.default_count} fell back to default",
        file=sys.stderr,
    )
    return 0
