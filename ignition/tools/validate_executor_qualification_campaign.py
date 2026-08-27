#!/usr/bin/env python3
"""Validate the repository-local IGNITION-143 qualification campaign ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from agent_federation.qualification_campaign import QualificationCampaignError, validate_campaign


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/operations/executor-qualification-campaign-r1.schema.json"
DEFAULT_PATH = ROOT / "data/operations/iterations/143/executor-qualification-campaign-r1.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.path.read_text(encoding="utf-8"))
        schema_errors = [error.json_path + ": " + error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")), format_checker=FormatChecker()).iter_errors(document)]
        if schema_errors:
            raise QualificationCampaignError("; ".join(schema_errors))
        summary = validate_campaign(document)
    except (OSError, json.JSONDecodeError, QualificationCampaignError) as exc:
        parser.error(str(exc))
    print(json.dumps({"status": "QUALIFICATION_CAMPAIGN_OK", **summary}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
