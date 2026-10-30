import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from tools.validate_state_changelog import (
    PROFILE_PATH,
    PROFILE_PATH_R3,
    PROFILE_PATH_R4,
    PROFILE_PATH_R1,
    R1_PROFILE_SHA256,
    R2_PROFILE_SHA256,
    R3_PROFILE_SHA256,
    R4_PROFILE_SHA256,
    ROOT,
    validate,
)


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "state-changelog-profile-r1.json"


def _replace_in_entry(source: str, ordinal: int, old: str, new: str) -> str:
    headings = list(re.finditer(r"^## \d{4}-\d{2}-\d{2} — .+$", source, re.MULTILINE))
    start = headings[ordinal - 1].start()
    end = headings[ordinal].start() if ordinal < len(headings) else len(source)
    section = source[start:end]
    if old not in section:
        raise AssertionError(f"fixture marker not found in entry {ordinal}: {old}")
    return source[:start] + section.replace(old, new, 1) + source[end:]


class StateChangelogTests(unittest.TestCase):
    def test_current_log_is_valid(self):
        self.assertEqual([], validate())

    def test_missing_required_field_is_rejected(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        source = source.replace("- stale_knowledge:", "- stale_removed:", 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "STATE-CHANGELOG.md"
            path.write_text(source, encoding="utf-8")
            errors = validate(path)
        self.assertTrue(any("stale_knowledge" in error for error in errors), errors)

    def test_broken_repository_link_is_rejected(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        source = source.replace("./AI-START-HERE.md", "./missing-state-entry.md", 1)
        path = ROOT / ".state-changelog-test.md"
        try:
            path.write_text(source, encoding="utf-8")
            errors = validate(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertTrue(any("broken repository link" in error for error in errors), errors)

    def test_latest_current_profile_required_field_is_rejected(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        source = _replace_in_entry(
            source,
            53,
            "- authority_changes:",
            "- authority_removed:",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "STATE-CHANGELOG.md"
            path.write_text(source, encoding="utf-8")
            errors = validate(path)
        self.assertTrue(any("authority_changes" in error for error in errors), errors)

    def test_profile_fixture_cases_preserve_historical_boundary(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual("ignition-135-state-changelog-profile-fixtures-r1", fixture["schema_version"])
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        for case in fixture["cases"]:
            case_id = case["case_id"]
            if case_id == "current_missing_required_field":
                mutated = _replace_in_entry(
                    source,
                    27,
                    "- authority_changes:",
                    "- authority_removed:",
                )
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "STATE-CHANGELOG.md"
                    path.write_text(mutated, encoding="utf-8")
                    errors = validate(path)
                passed = not errors
            elif case_id == "historical_sealed_exact_legacy":
                passed = not validate()
            elif case_id == "historical_sealed_mutation":
                mutated = _replace_in_entry(source, 17, "- main_state:", "- main_state: MUTATED;")
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "STATE-CHANGELOG.md"
                    path.write_text(mutated, encoding="utf-8")
                    errors = validate(path)
                passed = not errors
            elif case_id == "unknown_legacy_version":
                profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
                profile["entries"][16]["profile"] = "historical-legacy-r9"
                with tempfile.TemporaryDirectory() as tmp:
                    profile_path = Path(tmp) / "state-changelog-profile.json"
                    profile_path.write_text(json.dumps(profile), encoding="utf-8")
                    errors = validate(profile_path=profile_path)
                passed = not errors
            elif case_id == "current_profile_downgrade":
                profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
                profile["entries"][26]["profile"] = "historical-legacy-r0"
                with tempfile.TemporaryDirectory() as tmp:
                    profile_path = Path(tmp) / "state-changelog-profile.json"
                    profile_path.write_text(json.dumps(profile), encoding="utf-8")
                    errors = validate(profile_path=profile_path)
                passed = not errors
            else:
                self.fail(f"unhandled fixture case: {case_id}")
            expected = case["expected_status"] == "PASS"
            self.assertEqual(expected, passed, case_id)

    def test_r2_profile_is_exact_additive_successor_of_immutable_r1(self):
        r1_bytes = PROFILE_PATH_R1.read_bytes()
        r1 = json.loads(r1_bytes)
        r2_bytes = PROFILE_PATH.read_bytes()
        r2 = json.loads(r2_bytes)
        self.assertEqual(hashlib.sha256(r1_bytes).hexdigest(), R1_PROFILE_SHA256)
        self.assertEqual(hashlib.sha256(r2_bytes).hexdigest(), R2_PROFILE_SHA256)
        self.assertEqual(r2["parent_profile"]["sha256"], R1_PROFILE_SHA256)
        self.assertEqual(r2["entries"][: len(r1["entries"])], r1["entries"])
        self.assertEqual(r2["entry_count"], len(r2["entries"]))
        self.assertEqual(r2["entry_count"], len(r1["entries"]) + 1)
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        headings = list(re.finditer(r"^## \d{4}-\d{2}-\d{2} — .+$", source, re.MULTILINE))
        source_r2 = source[: headings[57].start()]
        path = ROOT / ".state-changelog-r2-prefix-test.md"
        try:
            path.write_text(source_r2, encoding="utf-8")
            self.assertEqual([], validate(path=path, profile_path=PROFILE_PATH))
        finally:
            path.unlink(missing_ok=True)

    def test_r3_profile_is_exact_additive_successor_of_immutable_r2(self):
        r2_bytes = PROFILE_PATH.read_bytes()
        r2 = json.loads(r2_bytes)
        r3_bytes = PROFILE_PATH_R3.read_bytes()
        r3 = json.loads(r3_bytes)
        self.assertEqual(hashlib.sha256(r2_bytes).hexdigest(), R2_PROFILE_SHA256)
        self.assertEqual(hashlib.sha256(r3_bytes).hexdigest(), R3_PROFILE_SHA256)
        self.assertEqual(r3["parent_profile"]["sha256"], R2_PROFILE_SHA256)
        self.assertEqual(r3["entries"][: len(r2["entries"])], r2["entries"])
        self.assertEqual(r3["entry_count"], len(r3["entries"]))
        self.assertEqual(r3["entry_count"], len(r2["entries"]) + 1)
        self.assertEqual("task20-current-lineage-r1", r3["entries"][-1]["profile"])
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        headings = list(re.finditer(r"^## \d{4}-\d{2}-\d{2} — .+$", source, re.MULTILINE))
        source_r3 = source[: headings[-1].start()]
        path = ROOT / ".state-changelog-r3-prefix-test.md"
        try:
            path.write_text(source_r3, encoding="utf-8")
            self.assertEqual([], validate(path=path, profile_path=PROFILE_PATH_R3))
        finally:
            path.unlink(missing_ok=True)

    def test_r3_profile_rejects_an_unregistered_59th_append(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        headings = list(re.finditer(r"^## \d{4}-\d{2}-\d{2} — .+$", source, re.MULTILINE))
        source_r3 = source[: headings[-1].start()]
        source_r3 += (
            "\n## 2026-10-30 — SYNTHETIC-UNAUTHORIZED-59\n\n"
            "- main_state: synthetic candidate only\n"
            "- delta: no authorized trust root was supplied\n"
            "- authority_changes: none\n"
            "- epistemic_state: unchanged\n"
            "- obligations: remain open\n"
            "- stale_knowledge: none\n"
            "- next_read: Owner must authorize a real successor independently\n"
            "- claim_ceiling: repository-local fixture only\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "STATE-CHANGELOG.md"
            path.write_text(source_r3, encoding="utf-8")
            errors = validate(path=path, profile_path=PROFILE_PATH_R3)
        self.assertTrue(any("expects 58 entries" in error for error in errors), errors)

    def test_r4_profile_is_exact_additive_successor_of_immutable_r3(self):
        r3_bytes = PROFILE_PATH_R3.read_bytes()
        r3 = json.loads(r3_bytes)
        r4_bytes = PROFILE_PATH_R4.read_bytes()
        r4 = json.loads(r4_bytes)
        self.assertEqual(hashlib.sha256(r3_bytes).hexdigest(), R3_PROFILE_SHA256)
        self.assertEqual(hashlib.sha256(r4_bytes).hexdigest(), R4_PROFILE_SHA256)
        self.assertEqual(r4["parent_profile"]["sha256"], R3_PROFILE_SHA256)
        self.assertEqual(r4["authorization"]["commit"], "ea631933be075684ef8de663e202db2ea9523221")
        self.assertEqual(r4["entries"][: len(r3["entries"])], r3["entries"])
        self.assertEqual(r4["entry_count"], len(r4["entries"]))
        self.assertEqual(r4["entry_count"], len(r3["entries"]) + 1)
        self.assertEqual("task20-v1-homepage-r1", r4["entries"][-1]["profile"])
        self.assertEqual([], validate())

    def test_r4_profile_rejects_an_unregistered_60th_append(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        source += (
            "\n## 2026-10-30 — SYNTHETIC-UNAUTHORIZED-60\n\n"
            "- main_state: synthetic candidate only\n"
            "- delta: no authorized trust root was supplied\n"
            "- homepage_boundary: fixture only\n"
            "- architecture_language: unchanged\n"
            "- task_lineage: unchanged\n"
            "- obligations: remain open\n"
            "- epistemic_state: unchanged\n"
            "- claim_ceiling: repository-local fixture only\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "STATE-CHANGELOG.md"
            path.write_text(source, encoding="utf-8")
            errors = validate(path=path)
        self.assertTrue(any("expects 59 entries" in error for error in errors), errors)

    def test_immutable_r1_prefix_validates_with_original_profile(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        headings = list(re.finditer(r"^## \d{4}-\d{2}-\d{2} — .+$", source, re.MULTILINE))
        prefix = source[: headings[56].start()]
        path = ROOT / ".state-changelog-r1-prefix-test.md"
        try:
            path.write_text(prefix, encoding="utf-8")
            self.assertEqual([], validate(path=path, profile_path=PROFILE_PATH_R1))
        finally:
            path.unlink(missing_ok=True)

    def test_r1_profile_rejects_an_unsealed_successor_and_r2_downgrade(self):
        errors = validate(profile_path=PROFILE_PATH_R1)
        self.assertTrue(any("expects" in error or "entry set" in error for error in errors), errors)
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        prefix = source
        path = ROOT / ".state-changelog-r2-downgrade-test.md"
        try:
            path.write_text(prefix, encoding="utf-8")
            errors = validate(path=path, profile_path=PROFILE_PATH)
        finally:
            path.unlink(missing_ok=True)
        self.assertTrue(any("expects" in error or "entry set" in error for error in errors), errors)

    def test_modified_or_untrusted_profile_cannot_reseal_history(self):
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        profile["entries"][55]["section_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            profile_path = Path(tmp) / "state-changelog-profile-r2.json"
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            errors = validate(profile_path=profile_path)
        self.assertTrue(any("not an authorized" in error or "authorized versioned seal" in error for error in errors), errors)


    def test_r2_negative_counterfactuals_preserve_fixed_57_entry_boundary(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        headings = list(re.finditer(r"^## \d{4}-\d{2}-\d{2} — .+$", source, re.MULTILINE))
        source_r2 = source[: headings[57].start()]
        cases = {
            "tampered-historical-56": _replace_in_entry(source_r2, 56, "- main_state:", "- main_state: TAMPERED;"),
            "tampered-current-57": _replace_in_entry(source_r2, 57, "- main_state:", "- main_state: TAMPERED;"),
            "arbitrary-scientific-claim-upgrade": _replace_in_entry(
                source_r2, 57, "- claim_ceiling:", "- claim_ceiling: SCIENTIFICALLY_VALIDATED_WITHOUT_EVIDENCE;"
            ),
            "missing-required-field": _replace_in_entry(
                source_r2, 57, "- claim_ceiling:", "- claim_ceiling_removed:"
            ),
            "duplicate-entry": source_r2 + "\n" + source_r2[source_r2.rfind("\n## ") + 1:],
            "unauthorized-58th-append": source_r2 + (
                "\n## 2026-10-13 — SYNTHETIC-UNAUTHORIZED-58\n\n"
                "- main_state: synthetic candidate only\n"
                "- delta: no authorized trust root was supplied\n"
                "- authority_changes: none\n"
                "- epistemic_state: unchanged\n"
                "- obligations: remain open\n"
                "- stale_knowledge: none\n"
                "- next_read: Owner must authorize a real successor independently\n"
                "- claim_ceiling: repository-local fixture only\n"
            ),
            "invalid-date": re.sub(
                r"(?m)^## 2026-10-12 — IGNITION-GOVERNANCE-SELF-REPAIR-R1-PACKAGE-A",
                "## 2026-99-99 — IGNITION-GOVERNANCE-SELF-REPAIR-R1-PACKAGE-A",
                source_r2,
                count=1,
            ),
        }
        expected_fragments = {
            "tampered-historical-56": "fingerprint mismatch",
            "tampered-current-57": "fingerprint mismatch",
            "arbitrary-scientific-claim-upgrade": "fingerprint mismatch",
            "missing-required-field": "missing nonblank field claim_ceiling",
            "duplicate-entry": "expects 57 entries",
            "unauthorized-58th-append": "expects 57 entries",
            "invalid-date": "invalid ISO date",
        }
        for case_id, mutated in cases.items():
            with self.subTest(case=case_id), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "STATE-CHANGELOG.md"
                path.write_text(mutated, encoding="utf-8")
                errors = validate(path=path, profile_path=PROFILE_PATH)
                self.assertTrue(any(expected_fragments[case_id] in error for error in errors), (case_id, errors))

    def test_r2_profile_authority_counterfactuals_fail_closed(self):
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forged = json.loads(json.dumps(profile))
            forged["entries"].append(dict(forged["entries"][-1], ordinal=58, date="2026-10-13"))
            forged["entry_count"] = 58
            forged_path = root / "forged-successor.json"
            forged_path.write_text(json.dumps(forged), encoding="utf-8")
            errors = validate(profile_path=forged_path)
            self.assertTrue(any("not an authorized versioned profile" in error for error in errors), errors)

            changed_anchor = json.loads(json.dumps(profile))
            changed_anchor["authorization"]["commit"] = "0" * 40
            changed_path = root / "changed-trust-anchor.json"
            changed_path.write_text(json.dumps(changed_anchor), encoding="utf-8")
            errors = validate(profile_path=changed_path)
            self.assertTrue(any("exact authorized append source" in error for error in errors), errors)

            duplicate_ordinal = json.loads(json.dumps(profile))
            duplicate_ordinal["entries"][-1]["ordinal"] = 56
            duplicate_path = root / "duplicate-ordinal.json"
            duplicate_path.write_text(json.dumps(duplicate_ordinal), encoding="utf-8")
            errors = validate(profile_path=duplicate_path)
            self.assertTrue(any("ordinals are not a complete ordered seal" in error for error in errors), errors)

            errors = validate(profile_path=PROFILE_PATH_R1)
            self.assertTrue(any("expects" in error or "entry set" in error for error in errors), errors)

    def test_r2_profile_rollback_and_canonical_bytes_remain_unchanged(self):
        r1_bytes = PROFILE_PATH_R1.read_bytes()
        r2_bytes = PROFILE_PATH.read_bytes()
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        headings = list(re.finditer(r"^## \d{4}-\d{2}-\d{2} — .+$", source, re.MULTILINE))
        prefix_56 = source[: headings[56].start()]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "STATE-CHANGELOG.md"
            path.write_text(prefix_56, encoding="utf-8")
            errors = validate(path=path, profile_path=PROFILE_PATH)
        self.assertTrue(any("expects 57 entries" in error or "entry set" in error for error in errors), errors)
        self.assertEqual(hashlib.sha256(r1_bytes).hexdigest(), R1_PROFILE_SHA256)
        self.assertEqual(hashlib.sha256(r2_bytes).hexdigest(), R2_PROFILE_SHA256)
        self.assertEqual([], validate())
        self.assertEqual(57, json.loads(r2_bytes)["entry_count"])

if __name__ == "__main__":
    unittest.main()
