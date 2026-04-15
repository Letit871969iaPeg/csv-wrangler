"""CLI sub-command: annotate — add computed columns to a CSV."""

from __future__ import annotations

import argparse
import csv
import sys
from typing import Dict, Iterator, List

from csv_wrangler.annotator import AnnotateError, AnnotateSpec, annotate_rows


def _iter_csv(path: str) -> Iterator[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def _parse_specs(raw: List[str]) -> List[AnnotateSpec]:
    """Parse strings of the form  ``column=python_expression``.

    The expression is evaluated with ``row`` bound to the current row dict.
    Example:  ``full_name=row['first'] + ' ' + row['last']``
    """
    specs: List[AnnotateSpec] = []
    for item in raw:
        if "=" not in item:
            raise AnnotateError(
                f"invalid spec {item!r}: expected 'column=expression'"
            )
        col, expr_src = item.split("=", 1)
        col = col.strip()
        expr_src = expr_src.strip()
        try:
            code = compile(expr_src, "<annotate>", "eval")
        except SyntaxError as exc:
            raise AnnotateError(f"syntax error in expression for '{col}': {exc}") from exc

        def _make_fn(c=code):
            def _fn(row: Dict[str, str]) -> str:  # noqa: ANN001
                return str(eval(c, {"__builtins__": {}}, {"row": row}))  # noqa: S307
            return _fn

        specs.append(AnnotateSpec(column=col, expression=_make_fn()))
    return specs


def add_annotate_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "annotate",
        help="add computed columns derived from existing values",
    )
    p.add_argument("input", help="input CSV file")
    p.add_argument("-o", "--output", default="-", help="output file (default: stdout)")
    p.add_argument(
        "-c",
        "--column",
        dest="specs",
        metavar="COL=EXPR",
        action="append",
        default=[],
        help="column=expression pair (repeatable)",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="allow overwriting existing columns",
    )
    p.set_defaults(func=_run_annotate)


def _run_annotate(args: argparse.Namespace) -> int:
    try:
        specs = _parse_specs(args.specs)
    except AnnotateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for spec in specs:
        spec.overwrite = args.overwrite

    rows = _iter_csv(args.input)
    iterator, result = annotate_rows(rows, specs)

    out = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")
    try:
        writer: csv.DictWriter | None = None
        try:
            for row in iterator:
                if writer is None:
                    writer = csv.DictWriter(out, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)
        except AnnotateError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    finally:
        if out is not sys.stdout:
            out.close()

    print(
        f"annotated {result.row_count} rows; "
        f"added {len(result.added_columns)} column(s)",
        file=sys.stderr,
    )
    return 0
