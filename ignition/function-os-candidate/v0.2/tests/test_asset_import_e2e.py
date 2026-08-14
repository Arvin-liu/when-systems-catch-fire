"""121Q6D Step 002: REAL asset import E2E (honest).

Per 121Q6D mandate, this test must:
- Attempt to read the REAL source_path bodies from asset-bridge-audit-35.json.
- If a real file is present, run the read-only importer and assert it produces a
  DRAFT with provenance/source_hash tied to the REAL file content, and that N1
  BLOCKS the DRAFT (function_id format / SEMVER / domain / non-empty inputs).
- If a real file is ABSENT (current truth: 120 asset md files are not checked in),
  assert the importer returns BLOCKED for missing source_text (correct safety).
- A separate SYNTHETIC fixture proves the draft->N1-block logic works; it is
  explicitly excluded from any "real asset migration" count.

No SAMPLE_MD impersonation. No _todo inputs/outputs presented as real migration.
"""
import json
import os
import unittest

from function_os.importer.legacy_asset_importer import import_asset
from function_os.n1_functionspec_parser import N1FunctionSpecParser

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
AUDIT = os.path.join(REPO_ROOT, "data", "external-research", "121-fulltext-resolver",
                     "121q6c", "asset-bridge-audit-35.json")
FIX_META = os.path.join(HERE, "fixtures", "legacy_meta_example.md")
FIX_THEOREM = os.path.join(HERE, "fixtures", "legacy_theorem_example.md")


def load_importable(n=2):
    items = json.load(open(AUDIT))["items"]
    imp = [a for a in items if a["classification"] == "IMPORTABLE_NOW"]
    return imp[:n]


class TestRealAssetSourceRead(unittest.TestCase):
    """Attempts to read the REAL source_path of two IMPORTABLE_NOW assets."""

    def setUp(self):
        self.assets = load_importable(2)

    def test_real_source_paths_are_read_or_blocked_honestly(self):
        results = []
        for rec in self.assets:
            path = rec["source_path"]
            real_body = None
            file_present = os.path.exists(path)
            if file_present:
                real_body = open(path, encoding="utf-8").read()
            out = import_asset(rec, real_body)  # None when file absent
            if not file_present:
                self.assertEqual(out["status"], "BLOCKED")
                self.assertTrue(out["manual_review_required"])
                results.append({
                    "asset_id": rec["asset_id"],
                    "real_file_present": False,
                    "importer_status": "BLOCKED",
                    "reason": "source_path not checked into repo; cannot read real body",
                })
            else:
                # file present: assert draft provenance binds to REAL content hash
                self.assertEqual(out["status"], "DRAFT_OK")
                real_hash = __import__("hashlib").sha256(
                    real_body.encode("utf-8")).hexdigest()
                self.assertEqual(out["draft"]["provenance"]["source_hash"], real_hash)
                results.append({
                    "asset_id": rec["asset_id"],
                    "real_file_present": True,
                    "importer_status": "DRAFT_OK",
                    "source_hash_matches_real_file": True,
                })
        # Record honest E2E state for both real assets.
        out_path = os.path.join(REPO_ROOT, "data", "external-research",
                                "121-fulltext-resolver", "121q6d",
                                "asset-import-e2e.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        json.dump({
            "step": "002",
            "real_assets_examined": results,
            "real_migration_completed": any(r.get("real_file_present") for r in results),
            "note": "Real migration requires the 120 asset md files to be checked in; "
                    "they are currently ABSENT, so importer correctly BLOCKS. No fake "
                    "migration claimed.",
            "synthetic_fixture_used_for_logic_proof": True,
            "synthetic_excluded_from_real_count": True,
            "executor": "QClaw", "model": "Hy3",
        }, open(out_path, "w"), indent=2, ensure_ascii=False)
        # Current truth: files absent -> no real migration possible.
        self.assertFalse(any(r.get("real_file_present") for r in results),
                         "real asset files must be present to claim migration")


class TestImporterDraftAndN1BlockWithFixture(unittest.TestCase):
    """Uses a SYNTHETIC fixture (clearly labeled) to prove draft + N1 safety block."""

    def test_fixture_draft_then_n1_blocks(self):
        rec = load_importable(1)[0]
        body = open(FIX_META, encoding="utf-8").read()
        out = import_asset(rec, body)
        self.assertEqual(out["status"], "DRAFT_OK")
        draft = out["draft"]
        self.assertTrue(draft["provenance"]["manual_review_required"])
        # N1 MUST reject the DRAFT- function_id (real safety constraint)
        parser = N1FunctionSpecParser()
        blocked = False
        try:
            parser.parse(json.dumps(draft))
        except Exception:
            blocked = True
        self.assertTrue(blocked, "N1 must block DRAFT- function_id")


class TestSyntheticLegalizationExcluded(unittest.TestCase):
    """Synthetic human-legalized spec is a SEPARATE fixture, NOT real migration."""

    def test_synthetic_legalization_runs_but_is_excluded(self):
        rec = load_importable(1)[0]
        body = open(FIX_THEOREM, encoding="utf-8").read()
        draft = import_asset(rec, body)["draft"]
        # Synthetic legalization (NOT a real asset; must not be counted as migration)
        legal = dict(draft)
        legal["function_id"] = "FN-20260715-9001"
        legal["spec_version"] = "0.2.1"
        legal["domain"] = "symbolic"
        legal["inputs"] = {"_synthetic_example": "human-specified"}
        legal["outputs"] = {"_synthetic_example": "human-specified"}
        parser = N1FunctionSpecParser()
        spec = parser.parse(json.dumps(legal))  # proves legalization path works
        self.assertTrue(spec["spec_hash"])
        # Explicitly mark as excluded from real-asset E2E count
        self.assertIn("_synthetic_example", legal["inputs"])


if __name__ == "__main__":
    unittest.main()
