"""JSON Schema (draft 2020-12) loader and validator for the Ignition runtime.

Schemas live in ``schemas/ignition_runtime`` (repo-root relative). The loader
is tolerant: schema validation is a secondary safety net; the authoritative
correctness checks are the closed-manifest triple-equality and epistemic
contract enforced in code.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator

from .errors import ManifestError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schemas" / "ignition_runtime"

_SCHEMA_NAMES = (
    "generation_manifest",
    "material_record",
    "candidate",
    "unknown",
    "engineering_signal",
    "operation_receipt",
    "promotion_request",
    "promotion_package",
    "authorization",
)


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict:
    if name not in _SCHEMA_NAMES:
        raise ManifestError(f"unknown schema: {name}")
    path = SCHEMA_DIR / f"{name}.schema.json"
    import json

    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=None)
def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(load_schema(name))


def validate_schema(instance: object, name: str) -> None:
    """Raise ManifestError if ``instance`` violates schema ``name``."""
    errors = sorted(
        _validator(name).iter_errors(instance),
        key=lambda e: list(e.path),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(p) for p in first.path) or "<root>"
        raise ManifestError(f"schema {name} error at {location}: {first.message}")
