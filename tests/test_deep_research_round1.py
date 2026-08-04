"""Round 1 — Deep Research Capability contract + machine schemas.

Validates:
  * All 13 generated schemas are themselves valid JSON Schema (Draft 2020-12)
    and reuse the inherited Research OS vocabularies (no duplicate authority).
  * Every positive fixture validates; every negative fixture is rejected
    (fail-closed executor contract, opened-scope, STOP_SUFFICIENT gates, enums).
  * The records.py constructors build all 13 types and the executor-observation
    contract is delegated to the kernel (prohibited keys rejected).
  * The field-origin classification proves the executor can never write an
    owner/GPT-adjudicated field and never smuggles a prohibited key.
  * The generator output is canonical (matches index.json count + version).
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from deep_research import records as R  # noqa: E402
from deep_research.generate_schemas import build_schemas, OUT_VERSION  # noqa: E402

POS_DIR = REPO_ROOT / "tests" / "fixtures" / "deep_research" / "round1" / "positive"
NEG_DIR = REPO_ROOT / "tests" / "fixtures" / "deep_research" / "round1" / "negative"
SCHEMA_DIR = REPO_ROOT / "schemas" / "deep-research"


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


class Round1SchemaStructureTests(unittest.TestCase):
    def test_thirteen_schemas_present(self):
        names = R.list_records()
        self.assertEqual(len(names), 13, f"expected 13 records, got {len(names)}")
        for n in names:
            self.assertTrue((SCHEMA_DIR / f"{n}.schema.json").exists())

    def test_schemas_are_valid_draft202012(self):
        from jsonschema import Draft202012Validator
        for name in R.list_records():
            schema = R.load_schema(name)
            # Draft202012Validator.check_schema validates the document against
            # the 2020-12 meta-schema; raises SchemaError if invalid.
            try:
                Draft202012Validator.check_schema(schema)
            except Exception as e:  # SchemaError or similar
                self.fail(f"schema '{name}' is not valid Draft2020-12: {e}")

    def test_schema_ids_and_version(self):
        for name in R.list_records():
            schema = R.load_schema(name)
            self.assertTrue(
                schema["$id"].startswith(OUT_VERSION + "/"),
                f"{name} $id must start with {OUT_VERSION}/",
            )

    def test_index_matches_generated(self):
        index = _load(SCHEMA_DIR / "index.json")
        self.assertEqual(index["version"], OUT_VERSION)
        self.assertEqual(sorted(index["records"]), sorted(R.list_records()))


class Round1VocabularyReuseTests(unittest.TestCase):
    """Round 1 must reuse the kernel vocabularies, not redefine them."""

    @classmethod
    def setUpClass(cls):
        from research_os import registries as REG
        cls.REG = REG
        cls.schemas = build_schemas()

    def test_obligation_class_enum_matches_kernel(self):
        enum = self.schemas["evidence-obligation"]["properties"]["obligation_class"]["enum"]
        self.assertEqual(set(enum), set(self.REG.OBLIGATION_CLASS_CODES))

    def test_action_code_enum_matches_kernel(self):
        enum = self.schemas["research-action"]["properties"]["action_code"]["enum"]
        self.assertEqual(set(enum), set(self.REG.ACTION_CODES))

    def test_claim_ceiling_enum_matches_kernel(self):
        enum = self.schemas["claim-evidence-record"]["properties"]["claim_ceiling"]["enum"]
        self.assertEqual(set(enum), set(self.REG.CLAIM_CEILING_ENUM))

    def test_episode_state_enum_matches_kernel(self):
        enum = self.schemas["research-episode-result"]["properties"]["final_state"]["enum"]
        self.assertEqual(set(enum), set(self.REG.STATE_CODES))


class Round1PositiveFixtureTests(unittest.TestCase):
    def test_all_positive_fixtures_validate(self):
        self.assertTrue(POS_DIR.exists(), f"positive fixture dir missing: {POS_DIR}")
        files = sorted(POS_DIR.glob("*.json"))
        self.assertGreaterEqual(len(files), 13, "expected >=13 positive fixtures")
        for f in files:
            name = f.name.split("__")[0]
            obj = _load(f)
            try:
                R.validate_record(name, obj)
            except ValueError as e:
                self.fail(f"positive fixture {f.name} unexpectedly rejected: {e}")


class Round1NegativeFixtureTests(unittest.TestCase):
    def test_all_negative_fixtures_rejected(self):
        self.assertTrue(NEG_DIR.exists(), f"negative fixture dir missing: {NEG_DIR}")
        files = sorted(NEG_DIR.glob("*.json"))
        self.assertGreaterEqual(len(files), 10, "expected >=10 negative fixtures")
        for f in files:
            doc = _load(f)
            record = doc.pop("_record")
            expect = doc.pop("_expect")
            with self.assertRaises(ValueError, msg=f"negative fixture {f.name} not rejected ({expect})"):
                if record == "executor-observation":
                    R.validate_executor_observation(doc)
                else:
                    R.validate_record(record, doc)

    def test_executor_observation_prohibited_keys_rejected_by_kernel(self):
        base = {
            "observation_id": "obs-X", "action_id": "act-X", "observations": [],
            "source_identities": [], "access_level": "DISCOVERED",
            "calculation_result": None, "errors": [], "provenance": [], "timestamps": {},
        }
        for banned in ("self_approved", "mark_episode_complete", "claim_ceiling"):
            bad = dict(base)
            bad[banned] = True
            with self.assertRaises(ValueError, msg=f"kernel must reject {banned}"):
                R.validate_executor_observation(bad)


class Round1ConstructorAndOriginTests(unittest.TestCase):
    def test_constructors_build_all_thirteen(self):
        for name in R.list_records():
            obj = R.make_record(name)
            self.assertIsInstance(obj, dict)
            self.assertEqual(obj.get("__invalid__", None), None)

    def test_executor_observation_has_no_owner_adjudicated_field(self):
        origins = R._ORIGIN.get("executor-observation", {})
        for field, cat in origins.items():
            self.assertNotEqual(
                cat, R.OWNER_ADJUDICATED,
                f"executor-observation field {field} must not be owner-adjudicated",
            )

    def test_prohibited_keys_classified_prohibited(self):
        for banned in ("self_approved", "mark_episode_complete", "claim_ceiling"):
            self.assertEqual(
                R.field_origin("executor-observation", banned), R.PROHIBITED,
                f"{banned} must be classified PROHIBITED",
            )

    def test_claim_ceiling_is_owner_adjudicated(self):
        self.assertEqual(
            R.field_origin("claim-evidence-record", "claim_ceiling"), R.OWNER_ADJUDICATED
        )

    def test_unknown_field_rejected_by_constructor(self):
        with self.assertRaises(ValueError):
            R.make_record("research-topic-candidate", bogus_field=1)

    def test_field_origin_unknown_field_raises(self):
        with self.assertRaises(ValueError):
            R.field_origin("research-topic-candidate", "does_not_exist")


class Round1GeneratorIdempotencyTests(unittest.TestCase):
    def test_generate_schemas_is_canonical(self):
        """The on-disk schema files must equal exactly what the generator emits
        (canonical-output principle: never hand-edit, always regenerate)."""
        import importlib
        gen = importlib.import_module("deep_research.generate_schemas")
        S = gen.build_schemas()
        for name, schema in S.items():
            ondisk = _load(SCHEMA_DIR / f"{name}.schema.json")
            self.assertEqual(
                schema, ondisk,
                f"on-disk schema '{name}' differs from generator output",
            )
        index_on_disk = _load(SCHEMA_DIR / "index.json")
        self.assertEqual(
            index_on_disk,
            {"version": OUT_VERSION, "records": sorted(S.keys()),
             "generated_by": "tools/deep_research/generate_schemas.py"},
            "on-disk index.json differs from generator output",
        )

    def test_generator_runs_clean(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools/deep_research/generate_schemas.py")],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
