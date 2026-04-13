"""Format a DataSummary into various output representations."""
from __future__ import annotations

import csv
import io
import json
from typing import Literal

from csv_wrangler.summarizer import DataSummary

OutputFormat = Literal["text", "json", "csv"]


def format_summary(summary: DataSummary, fmt: OutputFormat = "text") -> str:
    """Render a DataSummary as text, JSON, or CSV."""
    if fmt == "json":
        return _to_json(summary)
    if fmt == "csv":
        return _to_csv(summary)
    return _to_text(summary)


def _to_text(summary: DataSummary) -> str:
    lines = [f"Rows: {summary.row_count}"]
    for cs in summary.columns.values():
        lines.append(
            f"  {cs.name}: fill={cs.fill_rate:.1%} "
            f"top={[v for v, _ in cs.top_values[:3]]}"
        )
    return "\n".join(lines)


def _to_json(summary: DataSummary) -> str:
    data = {
        "row_count": summary.row_count,
        "columns": {
            name: {
                "total": cs.total,
                "filled": cs.filled,
                "fill_rate": round(cs.fill_rate, 4),
                "top_values": [
                    {"value": v, "count": c} for v, c in cs.top_values
                ],
            }
            for name, cs in summary.columns.items()
        },
    }
    return json.dumps(data, indent=2)


def _to_csv(summary: DataSummary) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["column", "total", "filled", "fill_rate", "top_value", "top_count"])
    for cs in summary.columns.values():
        top_v, top_c = cs.top_values[0] if cs.top_values else ("", 0)
        writer.writerow(
            [cs.name, cs.total, cs.filled, f"{cs.fill_rate:.4f}", top_v, top_c]
        )
    return buf.getvalue()
