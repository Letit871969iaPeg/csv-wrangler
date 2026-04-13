"""Load and parse a YAML/JSON validation schema into ColumnSpec objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from csv_wrangler.validator import ColumnSpec

try:
    import yaml  # type: ignore

    _YAML_AVAILABLE = True
except ModuleNotFoundError:
    _YAML_AVAILABLE = False


class SchemaError(Exception):
    """Raised when a schema file cannot be parsed or is structurally invalid."""


def _load_raw(path: Path) -> Any:
    """Load raw data from a JSON or YAML file."""
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise SchemaError(f"Invalid JSON in {path}: {exc}") from exc

    if suffix in {".yaml", ".yml"}:
        if not _YAML_AVAILABLE:
            raise SchemaError(
                "PyYAML is required to load YAML schemas. Install it with: pip install pyyaml"
            )
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise SchemaError(f"Invalid YAML in {path}: {exc}") from exc

    raise SchemaError(f"Unsupported schema format: {path.suffix!r} (use .json, .yaml, or .yml)")


def _parse_spec(raw: dict[str, Any]) -> ColumnSpec:
    """Convert a raw dict entry into a :class:`ColumnSpec`."""
    try:
        name = raw["name"]
    except KeyError:
        raise SchemaError(f"Schema entry missing required key 'name': {raw!r}")

    return ColumnSpec(
        name=name,
        required=raw.get("required", True),
        pattern=raw.get("pattern"),
        min_length=raw.get("min_length"),
        max_length=raw.get("max_length"),
        allowed_values=raw.get("allowed_values", []),
    )


def load_schema(path: str | Path) -> list[ColumnSpec]:
    """Load a validation schema from *path* and return a list of :class:`ColumnSpec`.

    The schema file must be JSON or YAML and contain a top-level ``columns`` list.
    Each entry may have the following keys:

    - ``name`` (str, required)
    - ``required`` (bool, default True)
    - ``pattern`` (str regex, optional)
    - ``min_length`` (int, optional)
    - ``max_length`` (int, optional)
    - ``allowed_values`` (list[str], optional)
    """
    path = Path(path)
    if not path.exists():
        raise SchemaError(f"Schema file not found: {path}")

    raw = _load_raw(path)

    if not isinstance(raw, dict) or "columns" not in raw:
        raise SchemaError("Schema must be a mapping with a top-level 'columns' key")

    columns = raw["columns"]
    if not isinstance(columns, list):
        raise SchemaError("'columns' must be a list")

    return [_parse_spec(entry) for entry in columns]
