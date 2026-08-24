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
PROFILE_PATH = ROOT / "data" / "operations" / "state-changelog-profile-r1.json"
PROFILE_SCHEMA_VERSION = "state-changelog-profile-r1"
EXPECTED_ENTRY_COUNT = 30
EXPECTED_CURRENT_ORDINALS = [27, 28, 29, 30]
EXPECTED_HISTORICAL_COUNT = 26
EXPECTED_LEGACY_COUNT = 6
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


def _validate_profile_contract(profile: dict, errors: list[str]) -> None:
    if profile.get("entry_count") != EXPECTED_ENTRY_COUNT:
        errors.append("validation profile entry_count is not the sealed current contract")
    if profile.get("active_current_ordinals") != EXPECTED_CURRENT_ORDINALS:
        errors.append("validation profile current ordinals are not the sealed current contract")
    if profile.get("historical_entry_count") != EXPECTED_HISTORICAL_COUNT:
        errors.append("validation profile historical count is not the sealed current contract")
    if profile.get("legacy_profile_count") != EXPECTED_LEGACY_COUNT:
        errors.append("validation profile legacy count is not the sealed current contract")
    profiles = profile.get("profiles")
    if not isinstance(profiles, dict):
        return
    expected_profiles = {
        "current-r1": ("current", STRICT_FIELDS, True),
        "historical-current-r0": ("historical", STRICT_FIELDS, True),
        "historical-legacy-r0": ("historical", [], False),
    }
    for name, (kind, required_fields, base_sha_required) in expected_profiles.items():
        definition = profiles.get(name)
        if not isinstance(definition, dict):
            errors.append(f"validation profile definition is missing: {name}")
            continue
        if definition.get("kind") != kind:
            errors.append(f"validation profile kind is invalid: {name}")
        if definition.get("required_fields") != required_fields:
            errors.append(f"validation profile required fields are invalid: {name}")
        if definition.get("base_sha_required") is not base_sha_required:
            errors.append(f"validation profile base SHA rule is invalid: {name}")
    entries = profile.get("entries")
    if not isinstance(entries, list):
        return
    ordinals = [item.get("ordinal") for item in entries if isinstance(item, dict)]
    if ordinals != list(range(1, EXPECTED_ENTRY_COUNT + 1)):
        errors.append("validation profile ordinals are not a complete ordered seal")
    current = [item.get("ordinal") for item in entries if isinstance(item, dict) and item.get("profile") == "current-r1"]
    historical = [item for item in entries if isinstance(item, dict) and str(item.get("profile", "")).startswith("historical-")]
    legacy = [item for item in entries if isinstance(item, dict) and item.get("profile") == "historical-legacy-r0"]
    if current != EXPECTED_CURRENT_ORDINALS:
        errors.append("validation profile does not keep the sealed Current entries strict")
    if len(historical) != EXPECTED_HISTORICAL_COUNT:
        errors.append("validation profile historical entry set has drifted")
    if len(legacy) != EXPECTED_LEGACY_COUNT:
        errors.append("validation profile legacy entry set has drifted")


def _load_profile(profile_path: Path) -> tuple[dict, list[str]]:
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"cannot load validation profile: {exc}"]
    if not isinstance(profile, dict):
        return {}, ["validation profile must be a JSON object"]
    errors: list[str] = []
    if profile.get("schema_version") != PROFILE_SCHEMA_VERSION:
        errors.append("validation profile schema_version is unknown")
    if profile.get("profile_contract") != "CURRENT_STRICT_HISTORICAL_VERSIONED":
        errors.append("validation profile contract is unknown")
    if not isinstance(profile.get("profiles"), dict):
        errors.append("validation profile profiles must be an object")
    if not isinstance(profile.get("entries"), list):
        errors.append("validation profile entries must be an array")
    _validate_profile_contract(profile, errors)
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


def validate(path: Path = PATH, profile_path: Path = PROFILE_PATH) -> list[str]:
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
    profile, _ = _load_profile(PROFILE_PATH)
    entries = profile.get("entries", [])
    current = sum(1 for item in entries if item.get("profile") == "current-r1")
    historical = sum(1 for item in entries if item.get("profile", "").startswith("historical-"))
    legacy = sum(1 for item in entries if item.get("profile") == "historical-legacy-r0")
    print(
        "PASS: STATE_CHANGELOG_VERSIONED_VALID "
        f"current={current} historical={historical} legacy_profiles={legacy}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
