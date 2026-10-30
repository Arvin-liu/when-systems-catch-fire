#!/usr/bin/env python3
"""Validate the append-only state log with explicit current and historical profiles."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
PATH = ROOT / "STATE-CHANGELOG.md"
PROFILE_PATH_R1 = ROOT / "data" / "operations" / "state-changelog-profile-r1.json"
PROFILE_PATH = ROOT / "data" / "operations" / "state-changelog-profile-r2.json"
PROFILE_PATH_R3 = ROOT / "data" / "operations" / "state-changelog-profile-r3.json"
PROFILE_PATH_R4 = ROOT / "data" / "operations" / "state-changelog-profile-r4.json"
R1_PROFILE_SHA256 = "8a431819d3ad59702cd0cf24e324f9082400c3b84828cbf3c06fe9fb0ce5c96c"
R2_PROFILE_SHA256 = "5b866d55e04ffc0fae8e89b19552084f04846df96b310eccbc24ffe7a2acd235"
R3_PROFILE_SHA256 = "b52f2c3886f09b91fcf677c18ca1d9dc8ae658e2d233bcad357965cb649e4d2d"
R4_PROFILE_SHA256 = "32097d8a25ad66d6089bdb8e7c1898237152d189df8792f79505fc08ba047993"
R1_SCHEMA_VERSION = "state-changelog-profile-r1"
R2_SCHEMA_VERSION = "state-changelog-profile-r2"
R3_SCHEMA_VERSION = "state-changelog-profile-r3"
R4_SCHEMA_VERSION = "state-changelog-profile-r4"
R1_PROFILE_CONTRACT = "CURRENT_STRICT_HISTORICAL_VERSIONED"
R2_PROFILE_CONTRACT = "CURRENT_STRICT_HISTORICAL_VERSIONED_APPEND_ONLY_SUCCESSOR"
R3_PROFILE_CONTRACT = "CURRENT_STRICT_HISTORICAL_VERSIONED_APPEND_ONLY_SUCCESSOR_CHAIN"
R4_PROFILE_CONTRACT = "CURRENT_STRICT_HISTORICAL_VERSIONED_APPEND_ONLY_OWNER_AUTHORIZED_SUCCESSOR_CHAIN"
R2_APPEND_PROFILE = "current-governance-self-repair-r1"
R3_APPEND_PROFILE = "task20-current-lineage-r1"
R4_APPEND_PROFILE = "task20-v1-homepage-r1"
R2_AUTHORIZATION = {
    "owner": "Arvin-liu",
    "repository": "Arvin-liu/1111",
    "commit": "bd5ec8280a8b5a2a682c7fd97f3cec6c1eec3527",
    "path": "instructions/goal-mode/IGNITION-2026-10-12-governance-self-repair-r1.md",
    "blob_sha1": "ec3c1d9781ead374679e334680a4f969f210a46e",
    "append_profile": R2_APPEND_PROFILE,
}
R3_AUTHORIZATION = {
    "owner": "Arvin-liu",
    "repository": "Arvin-liu/1111",
    "commit": "44de013f09b63535fe16b1e38cab7eff4d68ae66",
    "path": "instructions/goal-mode/IGNITION-2026-10-24-SIGNED-OWNER-WEB-MERGE-REGISTRATION-COMPATIBILITY-R0.md",
    "blob_sha1": "6a5d36cb6c40170c1b85440047eaceda097cee8b",
    "append_profile": R3_APPEND_PROFILE,
}
R4_AUTHORIZATION = {
    "owner": "Arvin-liu",
    "repository": "Arvin-liu/1111",
    "commit": "ea631933be075684ef8de663e202db2ea9523221",
    "path": "instructions/goal-mode/IGNITION-2026-10-30-ONE-TIME-R3-V1-CLOSEOUT-EXECUTION-DELEGATION-R0.json",
    "blob_sha1": "e93a53eabe7007a2447c9677f9a8d7b7f2428646",
    "append_profile": R4_APPEND_PROFILE,
}
STRICT_FIELDS = [
    "main_state",
    "delta",
    "authority_changes",
    "epistemic_state",
    "obligations",
    "stale_knowledge",
    "next_read",
]
ENTRY_RE = re.compile(r"^## (?P<date>\d{4}-\d{2}-\d{2}) — (?P<label>.+)$", re.MULTILINE)
SHA_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _section(text: str, start: int, end: int) -> str:
    return text[start:end]


def _r1_profile_definitions() -> dict[str, tuple[str, list[str], bool]]:
    return {
        "current-r1": ("current", STRICT_FIELDS, True),
        "current-human-front-door-r1": (
            "current",
            ["main_state", "delta", "architecture_language", "phase_boundary", "production_handoff", "task_lineage", "obligation", "regression", "authority_and_automation", "next_read", "claim_ceiling"],
            False,
        ),
        "current-homepage-simplification-r1": (
            "current",
            ["main_state", "delta", "homepage_boundary", "architecture_language", "task_lineage", "obligations", "epistemic_state", "claim_ceiling"],
            False,
        ),
        "current-project-identity-r1": (
            "current",
            ["main_state", "architecture_boundary", "task_lineage", "current_boundary", "claim_ceiling"],
            False,
        ),
        "historical-current-r0": ("historical", STRICT_FIELDS, True),
        "historical-legacy-r0": ("historical", [], False),
    }


def _profile_definitions() -> dict[str, dict]:
    return {
        name: {"kind": kind, "required_fields": required_fields, "base_sha_required": base_sha_required}
        for name, (kind, required_fields, base_sha_required) in _r1_profile_definitions().items()
    }


def _validate_profile_counts(profile: dict, errors: list[str]) -> None:
    profiles = profile.get("profiles")
    entries = profile.get("entries")
    if not isinstance(profiles, dict) or not isinstance(entries, list):
        return
    if profile.get("entry_count") != len(entries):
        errors.append("validation profile entry_count does not match its sealed entry set")
    ordinals = [item.get("ordinal") for item in entries if isinstance(item, dict)]
    if ordinals != list(range(1, len(entries) + 1)):
        errors.append("validation profile ordinals are not a complete ordered seal")
    current = [
        item.get("ordinal")
        for item in entries
        if isinstance(item, dict)
        and isinstance(profiles.get(item.get("profile")), dict)
        and profiles[item["profile"]].get("kind") == "current"
    ]
    historical = [item for item in entries if isinstance(item, dict) and str(item.get("profile", "")).startswith("historical-")]
    legacy = [item for item in entries if isinstance(item, dict) and item.get("profile") == "historical-legacy-r0"]
    if profile.get("active_current_ordinals") != current:
        errors.append("validation profile current ordinals do not match its entry definitions")
    if profile.get("historical_entry_count") != len(historical):
        errors.append("validation profile historical entry count does not match its entry set")
    if profile.get("legacy_profile_count") != len(legacy):
        errors.append("validation profile legacy entry count does not match its entry set")


def _validate_profile_contract(profile: dict, errors: list[str], schema_version: str) -> None:
    expected_profiles = _profile_definitions()
    if schema_version == R1_SCHEMA_VERSION:
        if profile.get("profile_contract") != R1_PROFILE_CONTRACT:
            errors.append("R1 validation profile contract is unknown")
        if profile.get("profiles") != expected_profiles:
            errors.append("R1 validation profile definitions differ from the sealed contract")
    elif schema_version == R2_SCHEMA_VERSION:
        if profile.get("profile_contract") != R2_PROFILE_CONTRACT:
            errors.append("R2 validation profile contract is unknown")
        parent = profile.get("parent_profile")
        expected_parent = {
            "path": "data/operations/state-changelog-profile-r1.json",
            "schema_version": R1_SCHEMA_VERSION,
            "sha256": R1_PROFILE_SHA256,
        }
        if parent != expected_parent:
            errors.append("R2 validation profile does not bind the exact sealed R1 parent")
        if profile.get("authorization") != R2_AUTHORIZATION:
            errors.append("R2 validation profile lacks the exact authorized append source")
        parent_bytes: bytes | None = None
        try:
            parent_bytes = PROFILE_PATH_R1.read_bytes()
            parent_profile = json.loads(parent_bytes)
        except (OSError, json.JSONDecodeError) as exc:
            parent_profile = {}
            errors.append(f"cannot load sealed R1 parent profile: {exc}")
        if parent_bytes is None or hashlib.sha256(parent_bytes).hexdigest() != R1_PROFILE_SHA256:
            errors.append("R1 parent profile bytes differ from their sealed digest")
        parent_entries = parent_profile.get("entries", [])
        r2_profile_definition = {
            "kind": "current",
            "required_fields": STRICT_FIELDS + ["claim_ceiling"],
            "base_sha_required": True,
        }
        expected_profiles.update({R2_APPEND_PROFILE: r2_profile_definition})
        entries = profile.get("entries")
        if profile.get("profiles") != expected_profiles:
            errors.append("R2 profile definitions are not exactly R1 plus its authorized append profile")
        if not isinstance(entries, list) or not isinstance(parent_entries, list):
            errors.append("R2 profile entries or R1 parent entries are malformed")
        else:
            if len(entries) != len(parent_entries) + 1:
                errors.append("R2 profile must append exactly one record to its R1 parent")
            if entries[:len(parent_entries)] != parent_entries:
                errors.append("R2 profile rewrites or reorders the sealed R1 entry prefix")
            if len(entries) > len(parent_entries):
                added = entries[len(parent_entries)]
                if not isinstance(added, dict) or added.get("ordinal") != len(parent_entries) + 1 or added.get("profile") != R2_APPEND_PROFILE:
                    errors.append("R2 appended entry is not the authorized next current profile")
        if profile.get("historical_entry_count") != parent_profile.get("historical_entry_count"):
            errors.append("R2 profile changes the R1 historical entry count")
        if profile.get("legacy_profile_count") != parent_profile.get("legacy_profile_count"):
            errors.append("R2 profile changes the R1 legacy profile count")
    elif schema_version == R3_SCHEMA_VERSION:
        if profile.get("profile_contract") != R3_PROFILE_CONTRACT:
            errors.append("R3 validation profile contract is unknown")
        parent = profile.get("parent_profile")
        expected_parent = {
            "path": "data/operations/state-changelog-profile-r2.json",
            "schema_version": R2_SCHEMA_VERSION,
            "sha256": R2_PROFILE_SHA256,
        }
        if parent != expected_parent:
            errors.append("R3 validation profile does not bind the exact sealed R2 parent")
        if profile.get("authorization") != R3_AUTHORIZATION:
            errors.append("R3 validation profile lacks the exact Task20 Owner authorization")
        parent_bytes: bytes | None = None
        try:
            parent_bytes = PROFILE_PATH.read_bytes()
            parent_profile = json.loads(parent_bytes)
        except (OSError, json.JSONDecodeError) as exc:
            parent_profile = {}
            errors.append(f"cannot load sealed R2 parent profile: {exc}")
        if parent_bytes is None or hashlib.sha256(parent_bytes).hexdigest() != R2_PROFILE_SHA256:
            errors.append("R2 parent profile bytes differ from their sealed digest")
        expected_profiles = parent_profile.get("profiles", {})
        expected_profiles = json.loads(json.dumps(expected_profiles))
        expected_profiles[R3_APPEND_PROFILE] = {
            "kind": "current",
            "required_fields": STRICT_FIELDS + ["claim_ceiling"],
            "base_sha_required": True,
        }
        if profile.get("profiles") != expected_profiles:
            errors.append("R3 profile definitions are not exactly R2 plus its authorized Task20 append profile")
        entries = profile.get("entries")
        parent_entries = parent_profile.get("entries", [])
        if not isinstance(entries, list) or not isinstance(parent_entries, list):
            errors.append("R3 profile entries or R2 parent entries are malformed")
        else:
            if len(entries) != len(parent_entries) + 1:
                errors.append("R3 profile must append exactly one record to its sealed R2 parent")
            if entries[:len(parent_entries)] != parent_entries:
                errors.append("R3 profile rewrites or reorders the sealed R2 entry prefix")
            if len(entries) > len(parent_entries):
                added = entries[len(parent_entries)]
                if not isinstance(added, dict) or added.get("ordinal") != len(parent_entries) + 1 or added.get("profile") != R3_APPEND_PROFILE:
                    errors.append("R3 appended entry is not the authorized next Task20 current profile")
        if profile.get("historical_entry_count") != parent_profile.get("historical_entry_count"):
            errors.append("R3 profile changes the R2 historical entry count")
        if profile.get("legacy_profile_count") != parent_profile.get("legacy_profile_count"):
            errors.append("R3 profile changes the R2 legacy profile count")
    elif schema_version == R4_SCHEMA_VERSION:
        if profile.get("profile_contract") != R4_PROFILE_CONTRACT:
            errors.append("R4 validation profile contract is unknown")
        parent = profile.get("parent_profile")
        expected_parent = {
            "path": "data/operations/state-changelog-profile-r3.json",
            "schema_version": R3_SCHEMA_VERSION,
            "sha256": R3_PROFILE_SHA256,
        }
        if parent != expected_parent:
            errors.append("R4 validation profile does not bind the exact sealed R3 parent")
        if profile.get("authorization") != R4_AUTHORIZATION:
            errors.append("R4 validation profile lacks the exact signed V1 closeout delegation")
        parent_bytes: bytes | None = None
        try:
            parent_bytes = PROFILE_PATH_R3.read_bytes()
            parent_profile = json.loads(parent_bytes)
        except (OSError, json.JSONDecodeError) as exc:
            parent_profile = {}
            errors.append(f"cannot load sealed R3 parent profile: {exc}")
        if parent_bytes is None or hashlib.sha256(parent_bytes).hexdigest() != R3_PROFILE_SHA256:
            errors.append("R3 parent profile bytes differ from their sealed digest")
        expected_profiles = parent_profile.get("profiles", {})
        expected_profiles = json.loads(json.dumps(expected_profiles))
        expected_profiles[R4_APPEND_PROFILE] = {
            "kind": "current",
            "required_fields": [
                "main_state",
                "delta",
                "homepage_boundary",
                "architecture_language",
                "task_lineage",
                "obligations",
                "epistemic_state",
                "claim_ceiling",
            ],
            "base_sha_required": True,
        }
        if profile.get("profiles") != expected_profiles:
            errors.append("R4 profile definitions are not exactly R3 plus its Owner-authorized V1 homepage profile")
        entries = profile.get("entries")
        parent_entries = parent_profile.get("entries", [])
        if not isinstance(entries, list) or not isinstance(parent_entries, list):
            errors.append("R4 profile entries or R3 parent entries are malformed")
        else:
            if len(entries) != len(parent_entries) + 1:
                errors.append("R4 profile must append exactly one record to its sealed R3 parent")
            if entries[:len(parent_entries)] != parent_entries:
                errors.append("R4 profile rewrites or reorders the sealed R3 entry prefix")
            if len(entries) > len(parent_entries):
                added = entries[len(parent_entries)]
                if not isinstance(added, dict) or added.get("ordinal") != len(parent_entries) + 1 or added.get("profile") != R4_APPEND_PROFILE:
                    errors.append("R4 appended entry is not the authorized next V1 homepage profile")
        if profile.get("historical_entry_count") != parent_profile.get("historical_entry_count"):
            errors.append("R4 profile changes the R3 historical entry count")
        if profile.get("legacy_profile_count") != parent_profile.get("legacy_profile_count"):
            errors.append("R4 profile changes the R3 legacy profile count")
    else:
        errors.append(f"unsupported validation profile schema: {schema_version}")
    _validate_profile_counts(profile, errors)


def _load_profile(profile_path: Path) -> tuple[dict, list[str]]:
    try:
        raw = profile_path.read_bytes()
        profile = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"cannot load validation profile: {exc}"]
    if not isinstance(profile, dict):
        return {}, ["validation profile must be a JSON object"]
    errors: list[str] = []
    resolved_path = profile_path.resolve()
    authorized_profiles = {
        PROFILE_PATH_R1.resolve(): (R1_SCHEMA_VERSION, R1_PROFILE_SHA256),
        PROFILE_PATH.resolve(): (R2_SCHEMA_VERSION, R2_PROFILE_SHA256),
        PROFILE_PATH_R3.resolve(): (R3_SCHEMA_VERSION, R3_PROFILE_SHA256),
        PROFILE_PATH_R4.resolve(): (R4_SCHEMA_VERSION, R4_PROFILE_SHA256),
    }
    authorized = authorized_profiles.get(resolved_path)
    if authorized is None:
        errors.append("validation profile path is not an authorized versioned profile")
        schema_version = str(profile.get("schema_version", ""))
    else:
        schema_version, expected_sha256 = authorized
        if hashlib.sha256(raw).hexdigest() != expected_sha256:
            errors.append("validation profile bytes differ from the authorized versioned seal")
    if profile.get("schema_version") != schema_version:
        errors.append("validation profile schema_version is unknown for its path")
    if not isinstance(profile.get("profiles"), dict):
        errors.append("validation profile profiles must be an object")
    if not isinstance(profile.get("entries"), list):
        errors.append("validation profile entries must be an array")
    _validate_profile_contract(profile, errors, schema_version)
    return profile, errors


def _profile_entry_map(profile: dict, errors: list[str]) -> dict[int, dict]:
    entries = profile.get("entries", [])
    if not isinstance(entries, list):
        return {}
    mapped: dict[int, dict] = {}
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("ordinal"), int):
            errors.append("validation profile contains an entry without an integer ordinal")
            continue
        ordinal = item["ordinal"]
        if ordinal in mapped:
            errors.append(f"validation profile duplicates ordinal {ordinal}")
        mapped[ordinal] = item
    return mapped


def _validate_entry_profile(
    *,
    entry_number: int,
    section: str,
    profile_entry: dict | None,
    profiles: dict,
    errors: list[str],
) -> None:
    if profile_entry is None:
        errors.append(f"entry {entry_number} has no sealed historical/current profile")
        return
    profile_name = profile_entry.get("profile")
    if not isinstance(profile_name, str) or profile_name not in profiles:
        errors.append(f"entry {entry_number} has unknown profile {profile_name!r}")
        return
    definition = profiles[profile_name]
    if not isinstance(definition, dict):
        errors.append(f"entry {entry_number} profile {profile_name} is not an object")
        return
    required_fields = definition.get("required_fields", [])
    if not isinstance(required_fields, list):
        errors.append(f"entry {entry_number} profile {profile_name} has invalid required_fields")
        required_fields = []
    for field in required_fields:
        if not isinstance(field, str):
            errors.append(f"entry {entry_number} profile {profile_name} has a non-string field")
            continue
        if not re.search(rf"^- {re.escape(field)}:\s*\S", section, re.MULTILINE):
            errors.append(f"entry {entry_number} missing nonblank field {field}")
    if definition.get("base_sha_required") and not SHA_RE.search(section):
        errors.append(f"entry {entry_number} must bind an exact base main tip")
    expected_sha = profile_entry.get("section_sha256")
    actual_sha = hashlib.sha256(section.encode("utf-8")).hexdigest()
    if expected_sha != actual_sha:
        errors.append(f"entry {entry_number} historical/current fingerprint mismatch")


def _validate_links(text: str, path: Path, errors: list[str]) -> None:
    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        resolved = (path.parent / target_path).resolve()
        try:
            resolved.relative_to(REPO_ROOT.resolve())
        except ValueError:
            errors.append(f"link escapes repository: {target}")
            continue
        if not resolved.exists():
            errors.append(f"broken repository link: {target}")


def validate(path: Path = PATH, profile_path: Path = PROFILE_PATH_R4) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing {path.relative_to(ROOT)}"]
    profile, profile_errors = _load_profile(profile_path)
    errors.extend(profile_errors)
    profile_entries = _profile_entry_map(profile, errors)
    profiles = profile.get("profiles", {})
    if not isinstance(profiles, dict):
        profiles = {}
    text = path.read_text(encoding="utf-8")
    if not text.startswith("# STATE-CHANGELOG\n"):
        errors.append("title must be exactly # STATE-CHANGELOG")
    if "append-only" not in text:
        errors.append("append-only protocol is missing")
    entries = list(ENTRY_RE.finditer(text))
    if len(entries) < 2:
        errors.append("baseline and at least one formal delta are required")
        return errors
    if "BASELINE-CURRENT" not in entries[0].group("label"):
        errors.append("first entry must be BASELINE-CURRENT")
    if not any("BASELINE-CURRENT" not in entry.group("label") for entry in entries):
        errors.append("at least one non-baseline formal delta is required")

    expected_count = profile.get("entry_count")
    if isinstance(expected_count, int) and expected_count != len(entries):
        errors.append(f"profile expects {expected_count} entries, found {len(entries)}")
    if profile_entries and len(profile_entries) != len(entries):
        errors.append("profile entry set does not exactly cover the changelog")

    previous_date: date | None = None
    for index, entry in enumerate(entries):
        ordinal = index + 1
        end = entries[index + 1].start() if index + 1 < len(entries) else len(text)
        section = _section(text, entry.start(), end)
        entry_date_text = entry.group("date")
        try:
            entry_date = date.fromisoformat(entry_date_text)
        except ValueError:
            entry_date = None
            errors.append(f"entry {ordinal} has invalid ISO date")
        if previous_date is not None and entry_date is not None and entry_date < previous_date:
            errors.append(f"entry {ordinal} breaks append-only date order")
        if entry_date is not None:
            previous_date = entry_date
        profile_entry = profile_entries.get(ordinal)
        if profile_entry is None:
            errors.append(f"entry {ordinal} is not sealed in the validation profile")
        else:
            if profile_entry.get("ordinal") != ordinal:
                errors.append(f"entry {ordinal} profile ordinal mismatch")
            if profile_entry.get("date") != entry_date_text:
                errors.append(f"entry {ordinal} profile date mismatch")
            if profile_entry.get("label") != entry.group("label"):
                errors.append(f"entry {ordinal} profile label mismatch")
        _validate_entry_profile(
            entry_number=ordinal,
            section=section,
            profile_entry=profile_entry,
            profiles=profiles,
            errors=errors,
        )

    _validate_links(text, path, errors)
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    profile, _ = _load_profile(PROFILE_PATH_R4)
    entries = profile.get("entries", [])
    definitions = profile.get("profiles", {})
    current = sum(
        1
        for item in entries
        if isinstance(definitions.get(item.get("profile")), dict)
        and definitions[item["profile"]].get("kind") == "current"
    )
    historical = sum(1 for item in entries if item.get("profile", "").startswith("historical-"))
    legacy = sum(1 for item in entries if item.get("profile") == "historical-legacy-r0")
    print(
        "PASS: STATE_CHANGELOG_VERSIONED_VALID "
        f"current={current} historical={historical} legacy_profiles={legacy}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
