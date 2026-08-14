"""121Q6C Step 003: tests for read-only legacy asset importer."""
import json
import os
import unittest

from function_os.importer.legacy_asset_importer import import_asset, ALLOWED_CLASSES

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
AUDIT = os.path.join(REPO_ROOT, "data", "external-research",
                     "121-fulltext-resolver", "121q6c", "asset-bridge-audit-35.json")


def load_audit():
    return json.load(open(AUDIT))["items"]


class TestImporterPositive(unittest.TestCase):
    def setUp(self):
        self.items = load_audit()
        self.importable = [a for a in self.items if a["classification"] == "IMPORTABLE_NOW"]

    def test_seven_importable_present(self):
        self.assertEqual(len(self.importable), 7)

    def test_importable_yields_draft_with_provenance(self):
        rec = self.importable[0]
        text = "# Example\n$\\forall x$ symbolic content here."
        out = import_asset(rec, text)
        self.assertEqual(out["status"], "DRAFT_OK")
        d = out["draft"]
        self.assertEqual(d["provenance"]["source_asset_id"], rec["asset_id"])
        self.assertEqual(d["provenance"]["source_hash"], __import__("hashlib").sha256(text.encode()).hexdigest())
        self.assertTrue(d["provenance"]["manual_review_required"])
        # never fabricates semantics
        self.assertEqual(d["inputs"], {})
        self.assertEqual(d["preconditions"], [])

    def test_source_hash_deterministic(self):
        rec = self.importable[1]
        t = "same text"
        self.assertEqual(import_asset(rec, t)["draft"]["provenance"]["source_hash"],
                         import_asset(rec, t)["draft"]["provenance"]["source_hash"])


class TestImporterNegative(unittest.TestCase):
    def setUp(self):
        self.items = load_audit()

    def test_non_importable_blocked(self):
        rec = [a for a in self.items if a["classification"] == "NEEDS_MANUAL_SPEC"][0]
        out = import_asset(rec, "text")
        self.assertEqual(out["status"], "BLOCKED")

    def test_unknown_out_of_scope_blocked(self):
        rec = [a for a in self.items if a["classification"] == "OUT_OF_SCOPE"][0]
        out = import_asset(rec, "text")
        self.assertEqual(out["status"], "BLOCKED")

    def test_missing_source_text_blocked(self):
        rec = [a for a in self.items if a["classification"] == "IMPORTABLE_NOW"][0]
        out = import_asset(rec, None)
        self.assertEqual(out["status"], "BLOCKED")
        self.assertTrue(out["manual_review_required"])


if __name__ == "__main__":
    unittest.main()
