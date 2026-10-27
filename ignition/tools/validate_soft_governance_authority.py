#!/usr/bin/env python3
"""Fail-closed validator for the ESI soft-governance authority boundary."""

from __future__ import annotations

import argparse
import io
import json
import re
import tokenize
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "data/epistemic-governance/soft-governance-non-authority-invariant-r0.json"
DEFAULT_SCHEMA = ROOT / "schemas/epistemic-governance/soft-governance-non-authority-invariant-r0.schema.json"
DEFAULT_FIXTURES = ROOT / "data/epistemic-governance/authority-negative-fixtures"
RUNTIME_DIRS = (ROOT / "agent_kernel", ROOT / "agent_runtime", ROOT / "agent_federation")


def validate_contract(contract: dict, schema: dict) -> list[str]:
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(contract)]
    if set(contract.get("allowed_effects", [])) & set(contract.get("forbidden_authority_effects", [])):
        errors.append("allowed and forbidden effects overlap")
    required = {"PERMISSION_GRANT", "AUTHORIZATION", "TRUTH_STATUS", "M_AXIS_UPGRADE", "E_AXIS_UPGRADE", "OWNER_ACCEPTANCE", "EPISTEMIC_ACCEPTANCE", "SAFETY_RELEASE"}
    if not required <= set(contract.get("forbidden_authority_effects", [])):
        errors.append("core authority effects are not all forbidden")
    return sorted(set(errors))


def evaluate_attempt(contract: dict, fixture: dict) -> str:
    soft_keys = set(fixture.get("soft_input", {})) & set(contract.get("soft_inputs", []))
    effect = fixture.get("requested_effect")
    if soft_keys and effect in set(contract.get("forbidden_authority_effects", [])):
        return "REJECT_SOFT_AUTHORITY_ESCALATION"
    if effect in set(contract.get("allowed_effects", [])):
        return "ALLOW_BOUNDED_SOFT_EFFECT"
    return "REJECT_UNKNOWN_EFFECT"


def _mask_strings_and_comments(text: str) -> str:
    """Keep source line structure while removing prose from the coupling scan.

    Runtime receipts legitimately mention both advisory soft state and words
    such as ``truth`` or ``permission`` in their claim ceilings.  Treating a
    whole file as one regex subject therefore creates false couplings.  The
    scanner is intended to catch executable same-line coupling, so remove
    literals/comments and preserve newlines before applying the pattern.
    """
    chars = list(text)
    line_offsets: list[int] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        line_offsets.append(offset)
        offset += len(line)
    if not line_offsets:
        line_offsets = [0]
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in tokens:
            if token.type not in {tokenize.STRING, tokenize.COMMENT}:
                continue
            start_row, start_col = token.start
            end_row, end_col = token.end
            start = line_offsets[start_row - 1] + start_col
            end = line_offsets[end_row - 1] + end_col
            for index in range(start, min(end, len(chars))):
                if chars[index] != "\n":
                    chars[index] = " "
    except (IndentationError, tokenize.TokenError):
        # Invalid Python is rejected by the normal test/import path. Keep the
        # source visible here so this safety scan fails closed if it contains a
        # same-line coupling that can still be recognized.
        return text
    return "".join(chars)


def scan_runtime_sources() -> list[str]:
    errors: list[str] = []
    forbidden = re.compile(r"(esi_score|soft_context_exposure|structural_governance_surface).*?(authorize|permission|truth|owner|safety)|(authorize|permission|truth|owner|safety).*?(esi_score|soft_context_exposure|structural_governance_surface)", re.I)
    for directory in RUNTIME_DIRS:
        if not directory.exists():
            continue
        for path in directory.rglob("*.py"):
            code = _mask_strings_and_comments(path.read_text(encoding="utf-8"))
            if any(forbidden.search(line) for line in code.splitlines()):
                errors.append(f"runtime source couples soft input to authority effect: {path.relative_to(ROOT)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--skip-runtime-scan", action="store_true")
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    errors = validate_contract(contract, schema)
    checked = 0
    for path in sorted(args.fixtures.glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        checked += 1
        actual = evaluate_attempt(contract, fixture)
        if actual != fixture.get("expected"):
            errors.append(f"{path.name}: expected {fixture.get('expected')}, got {actual}")
    if not args.skip_runtime_scan:
        errors.extend(scan_runtime_sources())
    if errors:
        print("FAIL")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    print(f"SOFT_GOVERNANCE_AUTHORITY_OK fixtures={checked} runtime_scan={'SKIPPED' if args.skip_runtime_scan else 'PASS'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
