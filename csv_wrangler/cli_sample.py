"""CLI sub-command: sample — draw a random sample from a CSV file."""
from __future__ import annotations

import argparse
import csv
import sys
from typing import Iterator

from csv_wrangler.sampler import SampleError, reservoir_sample, sample_rows


def add_sample_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "sample",
        help="Draw a random sample of rows from a CSV file.",
    )
    p.add_argument("input", help="Path to input CSV (use '-' for stdin).")
    p.add_argument("-o", "--output", default="-", help="Output path (default: stdout).")

    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("-n", "--count", type=int, metavar="N", help="Absolute number of rows to sample.")
    group.add_argument("-f", "--fraction", type=float, metavar="F", help="Fraction of rows to sample (0.0–1.0).")

    p.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility.")
    p.add_argument(
        "--reservoir",
        action="store_true",
        help="Use reservoir sampling (memory-efficient for large files).",
    )
    p.set_defaults(func=_run_sample)


def _iter_csv(path: str) -> Iterator[dict[str, str]]:
    fh = sys.stdin if path == "-" else open(path, newline="", encoding="utf-8")
    try:
        yield from csv.DictReader(fh)
    finally:
        if path != "-":
            fh.close()


def _run_sample(args: argparse.Namespace) -> int:
    try:
        if args.reservoir:
            if args.fraction is not None:
                print("error: --reservoir requires -n/--count, not --fraction.", file=sys.stderr)
                return 1
            result = reservoir_sample(
                _iter_csv(args.input),
                n=args.count,
                seed=args.seed,
            )
        else:
            result = sample_rows(
                _iter_csv(args.input),
                n=args.count,
                fraction=args.fraction,
                seed=args.seed,
            )
    except SampleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not result.rows:
        return 0

    out = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(out, fieldnames=list(result.rows[0].keys()))
        writer.writeheader()
        writer.writerows(result.rows)
    finally:
        if args.output != "-":
            out.close()

    return 0
