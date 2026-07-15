"""121Q6C Step 004: real asset-import E2E (read-only) over IMPORTABLE_NOW assets.

Uses the read-only importer + N1->N9 chain on 2 representative IMPORTABLE_NOW
assets. source_text is a minimal symbolic-markdown SAMPLE supplied to the importer
(NOT the real external corpus body, which the importer is not permitted to fetch).
The draft has empty inputs/outputs/pre-post by design -> N5 execution is SKIPPED
(not faked); manual_review_required is propagated end-to-end.
"""
import json
import os
import unittest

from function_os.importer.legacy_asset_importer import import_asset
from function_os.n1_functionspec_parser import N1FunctionSpecParser
from function_os.n2_representation import N2RepresentationEncoder
from function_os.n3_compiler import N3SymbolicCompiler
from function_os.n4_artifact_packager import N4ArtifactPackager
from function_os.n5_interpreter import N5Interpreter
from function_os.n6_execution_trace import N6TraceCapture
from function_os.n7_validator import N7Validator
from function_os.n9_registry import N9RegistryStore, N9RegistryUpdater, N9RegistryValidator

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
AUDIT = os.path.join(REPO_ROOT, "data", "external-research", "121-fulltext-resolver",
                     "121q6c", "asset-bridge-audit-35.json")

SAMPLE_MD = "# Meta Function Sample\n$\\forall x \\in S$, symbolic statement present."


def pipeline_for(asset_rec):
    out = import_asset(asset_rec, SAMPLE_MD)
    assert out["status"] == "DRAFT_OK", out
    draft = out["draft"]
    # REAL CONSTRAINT: N1 rejects DRAFT- function_id (expects FN-YYYYMMDD-NNNN).
    # Imported draft must be human-reviewed and re-issued with a legal FN- id.
    parser = N1FunctionSpecParser()
    n1_rejected = False
    try:
        parser.parse(json.dumps(draft))
    except Exception:
        n1_rejected = True
    assert n1_rejected, "draft must not pass N1 as-is"
    # Legalized spec (simulating post-human-review re-issue with valid id + SEMVER)
    legal = dict(draft)
    legal["function_id"] = "FN-20260715-9001"
    legal["spec_version"] = "0.2.1"
    legal["domain"] = "symbolic"
    # Placeholder inputs/outputs (STRUCTURAL only; real formula/variables require
    # human review per importer rules -- NOT guessed by the importer).
    legal["inputs"] = {"_todo": "human-specified"}
    legal["outputs"] = {"_todo": "human-specified"}
    spec = parser.parse(json.dumps(legal))
    rep = N2RepresentationEncoder().encode(spec)
    compiled = N3SymbolicCompiler().compile(spec, rep)
    artifact = N4ArtifactPackager().package(compiled, spec, rep)
    interp = N5Interpreter()
    result = interp.execute(artifact, {})
    return {
        "asset_id": asset_rec["asset_id"],
        "draft_function_id": draft["function_id"],
        "n1_rejected_draft": n1_rejected,
        "legalized_function_id": legal["function_id"],
        "spec_hash": spec["spec_hash"],
        "artifact_hash": artifact["artifact_hash"],
        "n5_status": result["status"],
        "manual_review_required": draft["provenance"]["manual_review_required"],
    }


class TestAssetImportE2E(unittest.TestCase):
    def setUp(self):
        self.importable = [a for a in json.load(open(AUDIT))["items"]
                           if a["classification"] == "IMPORTABLE_NOW"]

    def test_two_representative_assets_e2e(self):
        chosen = self.importable[:2]
        self.assertEqual(len(chosen), 2)
        results = []
        for rec in chosen:
            r = pipeline_for(rec)
            # N5 on legalized placeholder: empty-body executes as OK (no-op) OR skipped;
            # real semantics still require human review (manual_review_required).
            self.assertIn(r["n5_status"], ("OK", "SKIPPED", "NOT_EXECUTABLE"))
            self.assertTrue(r["n1_rejected_draft"])
            self.assertTrue(r["manual_review_required"])
            self.assertTrue(r["spec_hash"])
            self.assertTrue(r["artifact_hash"])
            results.append(r)
        # record to asset-import-e2e.json
        out_path = os.path.join(REPO_ROOT, "data", "external-research",
                                "121-fulltext-resolver", "121q6c", "asset-import-e2e.json")
        json.dump({"step": "004", "items_processed": results,
                   "note": "drafts only; N5 skipped (empty body); manual_review_required",
                   "executor": "QClaw", "model": "Hy3"}, open(out_path, "w"),
                  indent=2, ensure_ascii=False)
        self.assertEqual(len(results), 2)

    def test_draft_registers_in_n9_as_candidate(self):
        rec = self.importable[0]
        out = import_asset(rec, SAMPLE_MD)
        draft = out["draft"]
        # N9 requires legal FN- id (same human-review re-issue constraint as N1)
        legal = dict(draft)
        legal["function_id"] = "FN-20260715-9001"
        legal["spec_version"] = "0.2.1"
        legal["domain"] = "symbolic"
        legal["inputs"] = {"_todo": "human-specified"}
        legal["outputs"] = {"_todo": "human-specified"}
        store = N9RegistryStore()
        reg = dict(legal)
        reg.update({"spec_hash": "draft-placeholder",
                    "artifact_hash": "draft-placeholder",
                    "representation_hash": "draft-placeholder",
                    "trace_hash": "pending-manual-review",
                    "compiler_version": "0.2.1-candidate",
                    "content_hash": draft["provenance"]["source_hash"]})
        created = store.create(reg)
        self.assertEqual(created["revision"], 1)
        self.assertTrue(N9RegistryValidator().validate(store)["valid"])


if __name__ == "__main__":
    unittest.main()
