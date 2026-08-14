#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data" / "narrative-output-layer.schema.json"
STORY_DIR = ROOT / "outputs" / "stories" / "20260712-disobedience-subjectivity"
LEDGER = STORY_DIR / "story-source-ledger.json"
LONGFORM = STORY_DIR / "story-longform.md"
STRUCTURE = STORY_DIR / "story-structure-map.md"
REPORT = STORY_DIR / "story-validation-report.md"

CLAIM_TYPES = {"FACT", "INFERENCE", "ANALOGY", "METAPHOR", "PENDING"}


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValidationError(f"JSON_LOAD_FAILED {path}: {exc}") from exc


def ensure(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise ValidationError(f"FILE_MISSING {path}")


def validate_required(schema: dict, data: dict) -> None:
    required = schema.get("required", [])
    for key in required:
        if key not in data:
            raise ValidationError(f"MISSING_TOP_LEVEL_FIELD {key}")


def validate_claims(data: dict) -> None:
    sources = {row["source_id"] for row in data["sources"]}
    if len(sources) != len(data["sources"]):
        raise ValidationError("DUPLICATE_SOURCE_ID")
    for section in data["sections"]:
        for row in section["assertions"]:
            claim_type = row["claim_type"]
            if claim_type not in CLAIM_TYPES:
                raise ValidationError(f"BAD_CLAIM_TYPE {claim_type}")
            if row["source_id"] not in sources:
                raise ValidationError(f"UNKNOWN_SOURCE_ID {row['source_id']}")
            if not row["mapped_variables"]:
                raise ValidationError(f"EMPTY_MAPPED_VARIABLES {row['assertion_id']}")
            if not row["non_isomorphic_limits"]:
                raise ValidationError(f"EMPTY_NON_ISO_LIMITS {row['assertion_id']}")
    for source in data["sources"]:
        locator = source.get("locator", "")
        if locator.startswith("/") or locator.startswith("file:") or locator.startswith("C:\\"):
            raise ValidationError(f"ABSOLUTE_PATH_IN_SOURCE {source['source_id']}")
        if source["source_type"] == "local_note" and not source.get("content_sha256"):
            raise ValidationError(f"MISSING_LOCAL_CONTENT_SHA {source['source_id']}")


def validate_supporting_files() -> None:
    for path in [LONGFORM, STRUCTURE, REPORT]:
        ensure(path)
        if not path.read_text(encoding="utf-8").strip():
            raise ValidationError(f"EMPTY_FILE {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate narrative output layer package")
    parser.add_argument("--ledger", default=str(LEDGER))
    parser.add_argument("--schema", default=str(SCHEMA))
    args = parser.parse_args()

    schema = read_json(Path(args.schema))
    data = read_json(Path(args.ledger))

    validate_required(schema, data)
    validate_claims(data)
    validate_supporting_files()

    print("ALL_NARRATIVE_OUTPUT_VALID")
    print(f"validated_story={data['story_id']}")
    print(f"sections={len(data['sections'])}")
    print(f"sources={len(data['sources'])}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"NARRATIVE_OUTPUT_INVALID: {exc}", file=sys.stderr)
        raise SystemExit(1)
