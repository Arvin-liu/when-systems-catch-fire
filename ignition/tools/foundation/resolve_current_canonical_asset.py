#!/usr/bin/env python3
"""Resolve a user-supplied asset reference against Current canonical authority.

This resolver is deliberately exact and fail-closed. Historical files, model
memory and fuzzy similarity are not identity authorities.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
IDENTITY_CARDS_PATH = ROOT / "data/foundation/function-assets/identity-cards.jsonl"
NONFUNCTION_CLAIMS_PATH = ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl"
ALIAS_INDEX_PATH = ROOT / "data/governance/knowledge-experience/alias-index.jsonl"
CORRECTIONS_PATH = ROOT / "data/foundation/function-assets/corrections.jsonl"
LEGACY_MAPPINGS_PATH = ROOT / "data/foundation/mappings/legacy-mappings.jsonl"
FIXTURE_PATH = ROOT / "tests/fixtures/ignition-operating-method/canonical-resolution-r1.json"

IDENTITY_AUTHORITY = "ignition/data/foundation/function-assets/identity-cards.jsonl"
NONFUNCTION_CLAIMS_AUTHORITY = "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl"
ALIAS_AUTHORITY = "ignition/data/governance/knowledge-experience/alias-index.jsonl"
CORRECTION_AUTHORITY = "ignition/data/foundation/function-assets/corrections.jsonl"
LEGACY_MAPPING_AUTHORITY = "ignition/data/foundation/mappings/legacy-mappings.jsonl"

RESOLVED = "RESOLVED_CURRENT_CANONICAL_IDENTITY"
UNRESOLVED = "UNRESOLVED_LEGACY_REFERENCE"
AMBIGUOUS = "AMBIGUOUS_CANONICAL_REFERENCE"


class CanonicalAuthorityError(ValueError):
    """Raised when the Current authority set is structurally inconsistent."""


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise CanonicalAuthorityError(f"{path}:{line_number} is not an object")
        rows.append(value)
    return rows


def _index_unique(rows: Iterable[dict[str, Any]], key: str, authority: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if not isinstance(value, str) or not value:
            raise CanonicalAuthorityError(f"{authority} contains a row without {key}")
        if value in result:
            raise CanonicalAuthorityError(f"{authority} contains duplicate {key}: {value}")
        result[value] = row
    return result


def _stable_correction_id(row: dict[str, Any]) -> str | None:
    stable_id = row.get("stable_id")
    if isinstance(stable_id, str) and stable_id:
        return stable_id
    correction_id = row.get("correction_id")
    if isinstance(correction_id, str) and correction_id.startswith("CORR-98-"):
        return correction_id.removeprefix("CORR-98-")
    return None


def _exact_token(text: str, token: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])", text) is not None


def _canonical_title(record: dict[str, Any], authority: str) -> str:
    title = record.get("title") or record.get("canonical_title")
    if not isinstance(title, str) or not title:
        raise CanonicalAuthorityError(f"{authority} contains a row without title/canonical_title")
    return title


def _looks_like_historical_path(reference: str) -> bool:
    return reference.startswith(("统一函数总表/", "统一案例总表/")) or bool(
        re.search(r"(?:^|/)[^/]+\.(?:md|markdown|json|jsonl|csv)$", reference, re.IGNORECASE)
    )


def _unresolved(reference: str, reason: str, authority_sources: list[str] | None = None) -> dict[str, Any]:
    return {
        "input_reference": reference,
        "resolution_status": UNRESOLVED,
        "failure_reason": reason,
        "canonical_id": None,
        "canonical_title": None,
        "match_kind": None,
        "authority_sources": authority_sources or [IDENTITY_AUTHORITY, NONFUNCTION_CLAIMS_AUTHORITY, ALIAS_AUTHORITY],
        "memory_or_fuzzy_resolution_used": False,
        "historical_file_used_as_identity": False,
        "resolution_establishes_external_truth": False,
    }


def _ambiguous(reference: str, reason: str, candidates: list[str]) -> dict[str, Any]:
    return {
        "input_reference": reference,
        "resolution_status": AMBIGUOUS,
        "failure_reason": reason,
        "candidate_canonical_ids": sorted(set(candidates)),
        "canonical_id": None,
        "canonical_title": None,
        "match_kind": None,
        "authority_sources": [IDENTITY_AUTHORITY, NONFUNCTION_CLAIMS_AUTHORITY, ALIAS_AUTHORITY],
        "memory_or_fuzzy_resolution_used": False,
        "historical_file_used_as_identity": False,
        "resolution_establishes_external_truth": False,
    }


def _resolved(
    reference: str,
    record: dict[str, Any],
    match_kind: str,
    authority_sources: list[str],
    *,
    alias: dict[str, Any] | None = None,
    corrections: list[dict[str, Any]] | None = None,
    registry_kind: str = "FUNCTION_ASSET",
    identity_authority: str = IDENTITY_AUTHORITY,
) -> dict[str, Any]:
    canonical_title = _canonical_title(record, identity_authority)
    result: dict[str, Any] = {
        "input_reference": reference,
        "resolution_status": RESOLVED,
        "failure_reason": None,
        "canonical_id": record["canonical_id"],
        "canonical_title": canonical_title,
        "match_kind": match_kind,
        "registry_kind": registry_kind,
        "identity_authority": record.get("identity_authority", identity_authority),
        "final_disposition": record["final_disposition"],
        "claim_ceiling": record["claim_ceiling"],
        "record_sha256": record["record_sha256"],
        "authority_sources": list(dict.fromkeys(authority_sources)),
        "memory_or_fuzzy_resolution_used": False,
        "historical_file_used_as_identity": False,
        "resolution_establishes_external_truth": False,
    }
    if "primary_identity" in record:
        result["primary_identity"] = record["primary_identity"]
    if "claim_class" in record:
        result["claim_class"] = record["claim_class"]
    if alias is not None:
        result["alias_resolution"] = {
            "alias_id": alias["alias_id"],
            "status": alias["status"],
            "lineage_key": alias["lineage_key"],
            "replacement": alias["replacement"],
        }
    if corrections:
        result["corrections"] = [
            {
                "correction_id": row["correction_id"],
                "disposition": row["disposition"],
                "corrected_claim": row["corrected_claim"],
                "claim_ceiling": row["claim_ceiling"],
            }
            for row in corrections
        ]
    return result


def _corrected_alias_target(
    alias: dict[str, Any],
    cards_by_id: dict[str, dict[str, Any]],
    corrections_by_id: dict[str, dict[str, Any]],
) -> tuple[str | None, list[dict[str, Any]], str | None]:
    lineage = alias.get("lineage_key")
    if not isinstance(lineage, str) or not lineage.startswith("FUNCTION_IDENTITY_"):
        return None, [], "CORRECTED_ALIAS_LINEAGE_INVALID"
    lineage_ids = [part for part in lineage.removeprefix("FUNCTION_IDENTITY_").split("_") if part]
    if not lineage_ids:
        return None, [], "CORRECTED_ALIAS_LINEAGE_INVALID"
    target = lineage_ids[-1]
    if target not in cards_by_id:
        return None, [], "CORRECTED_ALIAS_TARGET_NOT_CURRENT"
    replacement = alias.get("replacement")
    if not isinstance(replacement, str) or not _exact_token(replacement, target):
        return None, [], "CORRECTED_ALIAS_REPLACEMENT_TARGET_MISMATCH"
    destination = alias.get("destination")
    if destination != "RESULTS/CORRECTIONS.md":
        return None, [], "CORRECTED_ALIAS_AUTHORITY_DESTINATION_INVALID"
    relevant = [corrections_by_id[item] for item in lineage_ids if item in corrections_by_id]
    if not relevant:
        return None, [], "CORRECTED_ALIAS_WITHOUT_CURRENT_CORRECTION"
    return target, relevant, None


def resolve_reference_from_rows(
    reference: str,
    cards: list[dict[str, Any]],
    aliases: list[dict[str, Any]],
    corrections: list[dict[str, Any]],
    legacy_mappings: list[dict[str, Any]],
    claims: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resolve one exact reference against supplied Current authority rows."""
    normalized = reference.strip() if isinstance(reference, str) else ""
    if not normalized:
        return _unresolved("", "BLANK_REFERENCE")
    if _looks_like_historical_path(normalized):
        return _unresolved(
            normalized,
            "NO_EXACT_CURRENT_CANONICAL_MAPPING",
            [IDENTITY_AUTHORITY, NONFUNCTION_CLAIMS_AUTHORITY],
        )

    claims = claims or []
    cards_by_id = _index_unique(cards, "canonical_id", IDENTITY_AUTHORITY)
    claims_by_id = _index_unique(claims, "canonical_id", NONFUNCTION_CLAIMS_AUTHORITY)
    duplicate_ids = sorted(set(cards_by_id) & set(claims_by_id))
    if duplicate_ids:
        raise CanonicalAuthorityError(
            "function and non-function authorities contain duplicate canonical IDs: "
            + ", ".join(duplicate_ids)
        )
    records_by_id = {
        **{
            key: (value, "FUNCTION_ASSET", IDENTITY_AUTHORITY)
            for key, value in cards_by_id.items()
        },
        **{
            key: (value, "NONFUNCTION_CLAIM", NONFUNCTION_CLAIMS_AUTHORITY)
            for key, value in claims_by_id.items()
        },
    }
    corrections_by_id: dict[str, dict[str, Any]] = {}
    for row in corrections:
        stable_id = _stable_correction_id(row)
        if stable_id:
            if stable_id in corrections_by_id:
                raise CanonicalAuthorityError(f"duplicate correction authority for {stable_id}")
            corrections_by_id[stable_id] = row

    titles: dict[str, list[tuple[dict[str, Any], str, str]]] = defaultdict(list)
    historical_ids: dict[str, list[tuple[dict[str, Any], str, str]]] = defaultdict(list)
    aliases_by_text: dict[str, list[dict[str, Any]]] = defaultdict(list)
    mappings_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        titles[_canonical_title(card, IDENTITY_AUTHORITY)].append(
            (card, "FUNCTION_ASSET", IDENTITY_AUTHORITY)
        )
        for historical_id in card.get("historical_ids", []):
            if isinstance(historical_id, str):
                historical_ids[historical_id].append(
                    (card, "FUNCTION_ASSET", IDENTITY_AUTHORITY)
                )
    for claim in claims:
        titles[_canonical_title(claim, NONFUNCTION_CLAIMS_AUTHORITY)].append(
            (claim, "NONFUNCTION_CLAIM", NONFUNCTION_CLAIMS_AUTHORITY)
        )
        for historical_id in claim.get("historical_ids", []):
            if isinstance(historical_id, str):
                historical_ids[historical_id].append(
                    (claim, "NONFUNCTION_CLAIM", NONFUNCTION_CLAIMS_AUTHORITY)
                )
    for row in aliases:
        alias_text = row.get("alias")
        if isinstance(alias_text, str):
            aliases_by_text[alias_text].append(row)
    for row in legacy_mappings:
        mapping_id = row.get("id")
        if isinstance(mapping_id, str):
            mappings_by_id[mapping_id].append(row)

    # A Current canonical ID always wins over memory, titles and old combined labels.
    if normalized in records_by_id:
        record, registry_kind, identity_authority = records_by_id[normalized]
        sources = [identity_authority]
        mappings = mappings_by_id.get(normalized, [])
        if mappings:
            valid = [
                row for row in mappings
                if row.get("relation") == "COMPATIBILITY_VIEW_OF"
                and row.get("target_ref") == f"formal-object:{normalized}"
            ]
            if valid:
                sources.append(LEGACY_MAPPING_AUTHORITY)
        return _resolved(
            normalized,
            record,
            "CANONICAL_ID",
            sources,
            registry_kind=registry_kind,
            identity_authority=identity_authority,
        )

    exact_aliases = aliases_by_text.get(normalized, [])
    if len(exact_aliases) > 1:
        return _ambiguous(normalized, "MULTIPLE_EXACT_ALIAS_ROWS", [])
    if exact_aliases:
        alias = exact_aliases[0]
        if alias.get("status") == "IDENTITY_CORRECTED":
            target, relevant_corrections, error = _corrected_alias_target(
                alias, cards_by_id, corrections_by_id
            )
            if error or target is None:
                return _unresolved(
                    normalized,
                    error or "CORRECTED_ALIAS_UNRESOLVED",
                    [IDENTITY_AUTHORITY, ALIAS_AUTHORITY, CORRECTION_AUTHORITY],
                )
            return _resolved(
                normalized,
                cards_by_id[target],
                "IDENTITY_CORRECTED_ALIAS",
                [IDENTITY_AUTHORITY, ALIAS_AUTHORITY, CORRECTION_AUTHORITY],
                alias=alias,
                corrections=relevant_corrections,
                registry_kind="FUNCTION_ASSET",
                identity_authority=IDENTITY_AUTHORITY,
            )
        if alias.get("status") == "CURRENT_SEARCH_ALIAS":
            target = alias.get("lineage_key")
            if isinstance(target, str) and target in records_by_id:
                record, registry_kind, identity_authority = records_by_id[target]
                return _resolved(
                    normalized,
                    record,
                    "CURRENT_SEARCH_ALIAS",
                    [identity_authority, ALIAS_AUTHORITY],
                    alias=alias,
                    registry_kind=registry_kind,
                    identity_authority=identity_authority,
                )
            return _unresolved(
                normalized,
                "CURRENT_ALIAS_TARGET_NOT_CURRENT",
                [IDENTITY_AUTHORITY, NONFUNCTION_CLAIMS_AUTHORITY, ALIAS_AUTHORITY],
            )
        return _unresolved(normalized, "ALIAS_STATUS_NOT_CURRENT")

    title_matches = titles.get(normalized, [])
    if len(title_matches) == 1:
        record, registry_kind, identity_authority = title_matches[0]
        return _resolved(
            normalized,
            record,
            "CANONICAL_TITLE",
            [identity_authority],
            registry_kind=registry_kind,
            identity_authority=identity_authority,
        )
    if len(title_matches) > 1:
        return _ambiguous(
            normalized,
            "NON_UNIQUE_CANONICAL_TITLE",
            [record["canonical_id"] for record, _, _ in title_matches],
        )

    historical_matches = historical_ids.get(normalized, [])
    if historical_matches:
        mapping_targets = {
            row.get("target_ref", "").removeprefix("formal-object:")
            for row in mappings_by_id.get(normalized, [])
            if row.get("relation") == "COMPATIBILITY_VIEW_OF"
            and isinstance(row.get("target_ref"), str)
            and row["target_ref"].startswith("formal-object:")
        }
        candidates = [
            item for item in historical_matches if item[0]["canonical_id"] in mapping_targets
        ]
        if len(candidates) == 1:
            record, registry_kind, identity_authority = candidates[0]
            return _resolved(
                normalized,
                record,
                "MIGRATED_HISTORICAL_ID",
                [identity_authority, LEGACY_MAPPING_AUTHORITY],
                registry_kind=registry_kind,
                identity_authority=identity_authority,
            )
        if len(candidates) > 1:
            return _ambiguous(
                normalized,
                "HISTORICAL_ID_MAPS_TO_MULTIPLE_CURRENT_IDENTITIES",
                [record["canonical_id"] for record, _, _ in candidates],
            )
        return _unresolved(
            normalized,
            "HISTORICAL_ID_WITHOUT_CURRENT_MAPPING",
            [IDENTITY_AUTHORITY, NONFUNCTION_CLAIMS_AUTHORITY, LEGACY_MAPPING_AUTHORITY],
        )

    # Paths and near matches intentionally do not resolve: historical files are evidence, not identity.
    return _unresolved(normalized, "NO_EXACT_CURRENT_CANONICAL_MAPPING")


def resolve_reference(reference: str) -> dict[str, Any]:
    return resolve_reference_from_rows(
        reference,
        load_jsonl(IDENTITY_CARDS_PATH),
        load_jsonl(ALIAS_INDEX_PATH),
        load_jsonl(CORRECTIONS_PATH),
        load_jsonl(LEGACY_MAPPINGS_PATH),
        load_jsonl(NONFUNCTION_CLAIMS_PATH),
    )


def validate_fixtures(document: dict[str, Any] | None = None) -> list[str]:
    fixtures = document if document is not None else json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    cases = fixtures.get("cases", []) if isinstance(fixtures, dict) else []
    if not isinstance(cases, list) or not cases:
        return ["canonical resolution fixture cases must be a nonempty array"]
    errors: list[str] = []
    case_ids: list[str] = []
    for case in cases:
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            errors.append("every canonical resolution fixture must have a nonblank case_id")
            continue
        case_ids.append(case_id)
        actual = resolve_reference(case.get("reference", ""))
        for key, expected in case.get("expected", {}).items():
            if actual.get(key) != expected:
                errors.append(f"{case_id}: {key} expected {expected!r}, got {actual.get(key)!r}")
        if actual["memory_or_fuzzy_resolution_used"]:
            errors.append(f"{case_id}: memory or fuzzy resolution was used")
        if actual["historical_file_used_as_identity"]:
            errors.append(f"{case_id}: historical file was used as identity")
        if actual["resolution_establishes_external_truth"]:
            errors.append(f"{case_id}: identity resolution was promoted to external truth")
    if len(case_ids) != len(set(case_ids)):
        errors.append("canonical resolution fixture case ids must be unique")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--reference")
    group.add_argument("--check-fixtures", action="store_true")
    args = parser.parse_args()
    if args.check_fixtures:
        errors = validate_fixtures()
        if errors:
            print("IGNITION_CANONICAL_RESOLUTION_FIXTURES_INVALID")
            for error in errors:
                print(f"- {error}")
            return 1
        cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]
        print(f"IGNITION_CANONICAL_RESOLUTION_FIXTURES_OK cases={len(cases)}")
        return 0
    print(json.dumps(resolve_reference(args.reference), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
