"""CLI subcommand: infer — infer column types from a CSV file."""
from __future__ import annotations
import argparse
import csv
import json
import sys
from csv_wrangler.typer import infer_types


def add_infer_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("infer", help="Infer column types from a CSV file")
    p.add_argument("input", help="Input CSV file (use - for stdin)")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        metavar="FLOAT",
        help="Only show columns at or above this confidence (0.0–1.0)",
    )
    p.set_defaults(func=_run_infer)


def _iter_csv(path: str):
    """Yield rows as dicts from a CSV file path, or stdin if path is '-'."""
    fh = sys.stdin if path == "-" else open(path, newline="", encoding="utf-8")
    try:
        yield from csv.DictReader(fh)
    finally:
        if path != "-":
            fh.close()


def _run_infer(args: argparse.Namespace) -> int:
    """Execute the infer subcommand, printing inferred column types."""
    try:
        rows = list(_iter_csv(args.input))
    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print("No data found.", file=sys.stderr)
        return 1

    results = infer_types(rows)
    filtered = {
        col: info
        for col, info in results.items()
        if info.confidence >= args.min_confidence
    }

    if args.format == "json":
        payload = [
            {
                "column": info.column,
                "type": info.inferred_type,
                "confidence": round(info.confidence, 4),
                "sample_count": info.sample_count,
            }
            for info in filtered.values()
        ]
        print(json.dumps(payload, indent=2))
    else:
        for info in filtered.values():
            print(str(info))

    return 0
