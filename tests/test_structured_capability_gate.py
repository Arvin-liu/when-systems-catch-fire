#!/usr/bin/env python3
"""Independent fail-closed test for the shared structured-capability engine.

Directly exercises tools/governance/structured_capability_gate.py as a real CLI
(with an in-process evaluator) covering the four repair-r2 root blockers AND the
repair-r3 semantic-evaluator layer (RB09-CALLER-ASSERTED-SEMANTICS).

A valid bundle is built from a REAL Git object in this repository so the engine
has authoritative bytes to recompute; every negative case must exit non-zero.
"""
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

from tools.governance.semantic_evaluator import semantic_evaluate

REPO_ROOT = Path(
    __file__
).resolve().parent.parent
ENGINE = REPO_ROOT / "tools" / "governance" / "structured_capability_gate.py"
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")

# A stable real commit present in this repo (SYMBOLIC-SPHERE repair-r1 head).
REAL_COMMIT = "4ec769768d31c1fd0d7a6c066d235b4064606652"
REAL_PATH = "tools/governance/structured_capability_gate.py"


def _git(args):
    return subprocess_run(["git", "-C", str(REPO_ROOT)] + args)


def subprocess_run(args):
    import subprocess
    return subprocess.run(args, capture_output=True, text=True)


def _blob_sha(commit, path):
    return _git(["rev-parse", f"{commit}:{path}"]).stdout.strip()


def _sha256_of_blob(commit, path):
    out = _git(["show", f"{commit}:{path}"]).stdout
    return "sha256:" + hashlib.sha256(out.encode()).hexdigest()


# Shared-engine test config: 2 rules, 2 fields, one real evidence object.
_SHARED_MATRIX = {
    "rule_alpha": {"roles": ["authoritative_engine"], "types": ["ENGINE_SOURCE"]},
    "rule_beta": {"roles": ["authoritative_engine"], "types": ["ENGINE_SOURCE"]},
}
_SHARED_FIELDS = {"rule_alpha": "field_a", "rule_beta": "field_b"}


def _shared_evaluator(bundle, config, evidence):
    return semantic_evaluate(bundle, config, evidence, _SHARED_MATRIX, _SHARED_FIELDS)


def _engine_module():
    import importlib
    return importlib.import_module("tools.governance.structured_capability_gate")


def run_engine(bundle_path, config, inject_evaluator=True):
    """Run the shared engine in-process (so a callable evaluator can be supplied)."""
    m = _engine_module()
    cfg = dict(config)
    if inject_evaluator:
        cfg["evaluator"] = _shared_evaluator
        cfg["evidence_matrix"] = _SHARED_MATRIX
    old = sys.argv
    sys.argv = ["structured_capability_gate.py", "--bundle", str(bundle_path)]
    try:
        return m.run(cfg)
    finally:
        sys.argv = old


def minimal_schema():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": [
            "task_id", "parent_binding", "evidence_registry", "records",
            "facts", "rule_assertions", "conclusion",
        ],
        "properties": {
            "evidence_registry": {"type": "array"},
            "records": {"type": "array"},
            "facts": {"type": "object"},
            "rule_assertions": {"type": "array"},
            "conclusion": {"type": "object"},
            "parent_binding": {"type": "object"},
        },
    }


CONFIG = {
    "capability": "structured_capability_gate",
    "parent_id": "SYMBOLIC-SPHERE-I1",
    "parent_head": REAL_COMMIT,
    "schema": "",  # filled per-test with a temp schema path
    "fields": ["field_a", "field_b"],
    "rules": ["rule_alpha", "rule_beta"],
    "forbidden_claims": ["universal truth", "causal proof established", "ecosystem deployed"],
}


class EngineFailClosedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="engine-test-")
        schema_path = Path(cls._tmp) / "mini-schema.json"
        schema_path.write_text(json.dumps(minimal_schema()))
        cls.schema_path = schema_path
        cls.blob = _blob_sha(REAL_COMMIT, REAL_PATH)
        cls.sha = _sha256_of_blob(REAL_COMMIT, REAL_PATH)
        cls.content = _git(["show", f"{REAL_COMMIT}:{REAL_PATH}"]).stdout
        assert HEAD_RE.match(cls.blob), "blob_sha not 40-hex"
        assert cls.sha.startswith("sha256:"), "sha256 malformed"

    def _config(self):
        c = dict(CONFIG)
        c["schema"] = str(self.schema_path)
        return c

    def _valid_bundle(self):
        return {
            "contract_version": "1.0.0",
            "task_id": "SYMBOLIC-SPHERE-I1",
            "capability_id": "structured_capability_gate",
            "parent_binding": {"task_id": "SYMBOLIC-SPHERE-I1", "exact_head": REAL_COMMIT},
            "evidence_registry": [
                {
                    "evidence_id": "evidence.1",
                    "artifact": REAL_PATH,
                    "exact_head": REAL_COMMIT,
                    "artifact_digest": self.sha,
                    "rights_status": "REPOSITORY_INTERNAL",
                    "repository_relative_path": REAL_PATH,
                    "commit_sha": REAL_COMMIT,
                    "blob_sha": self.blob,
                    "sha256": self.sha,
                    "record_type": "ENGINE_SOURCE",
                    "declared_role": "authoritative_engine",
                }
            ],
            "records": [
                {"record_id": "record.1",
                 "field_a": {"status": "RECORDED", "value": self.content, "evidence_refs": ["evidence.1"]},
                 "field_b": {"status": "RECORDED", "value": self.content, "evidence_refs": ["evidence.1"]}}
            ],
            "facts": {"rule_alpha": True, "rule_beta": True},
            "rule_assertions": [
                {"rule_id": "rule_alpha", "status": "PASS", "evidence_refs": ["evidence.1"], "effect": "ALLOW_WITHIN_CEILING"},
                {"rule_id": "rule_beta", "status": "PASS", "evidence_refs": ["evidence.1"], "effect": "ALLOW_WITHIN_CEILING"},
            ],
            "conclusion": {
                "statement": "engine hardened against path and git-object bypass",
                "claim_ceiling": "candidate_only_repository_governance",
                "history_preserved": True,
                "external_action_performed": False,
            },
        }

    def _write(self, bundle):
        p = Path(self._tmp) / "bundle.json"
        p.write_text(json.dumps(bundle))
        return p

    # ---- positive ----
    def test_valid_bundle_passes(self):
        rc = run_engine(self._write(self._valid_bundle()), self._config())
        self.assertEqual(rc, 0, "valid bundle should pass (exit 0)")

    # ---- evidence-path / git-object blockers (repair-r2 controls) ----
    def test_absolute_path_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["repository_relative_path"] = "/etc/hosts"
        self.assertNotEqual(run_engine(self._write(b), self._config()), 0, "absolute path must be rejected")

    def test_dotdot_traversal_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["repository_relative_path"] = "../etc/passwd"
        self.assertNotEqual(run_engine(self._write(b), self._config()), 0, "'..' traversal must be rejected")

    def test_backslash_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["repository_relative_path"] = "tools\\governance\\x.py"
        self.assertNotEqual(run_engine(self._write(b), self._config()), 0, "backslash path must be rejected")

    def test_fabricated_exact_head_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["exact_head"] = "0" * 40
        self.assertNotEqual(run_engine(self._write(b), self._config()), 0, "non-resolving fabricated exact_head must be rejected")

    def test_missing_git_object_field_rejected(self):
        b = self._valid_bundle()
        del b["evidence_registry"][0]["commit_sha"]
        self.assertNotEqual(run_engine(self._write(b), self._config()), 0, "missing commit_sha must be rejected")

    def test_tampered_sha256_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["sha256"] = "sha256:" + "0" * 64
        self.assertNotEqual(run_engine(self._write(b), self._config()), 0, "tampered sha256 must be rejected")

    def test_tampered_blob_sha_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["blob_sha"] = "0" * 40
        self.assertNotEqual(run_engine(self._write(b), self._config()), 0, "tampered blob_sha must be rejected")

    def test_parent_binding_mismatch_rejected(self):
        b = self._valid_bundle()
        b["parent_binding"]["exact_head"] = "0" * 40
        self.assertNotEqual(run_engine(self._write(b), self._config()), 0, "parent head mismatch must be rejected")

    # ---- repair-r3 semantic-evaluator layer (RB09-CALLER-ASSERTED-SEMANTICS) ----
    def test_missing_evaluator_rejected(self):
        # Evidence is valid, but no evaluator supplied -> req-7 fail-closed.
        rc = run_engine(self._write(self._valid_bundle()), self._config(), inject_evaluator=False)
        self.assertEqual(rc, 1, f"missing evaluator must exit 1, got {rc}")

    def test_semantically_false_but_git_valid_fails(self):
        # All Git refs valid, evidence real, evidence_refs registered, caller
        # facts=true/status=PASS present -- but a record value contradicts the rule.
        b = self._valid_bundle()
        b["records"][0]["field_a"]["value"] = "CONTRADICTS_RULE_ALPHA_NOT_IN_EVIDENCE"
        rc = run_engine(self._write(b), self._config())
        self.assertNotEqual(rc, 0, "caller-asserted facts must not bypass recomputation")
        self.assertEqual(rc, 30, f"first rule (index 0) should fail with 30, got {rc}")

    def test_unrelated_valid_evidence_laundering_fails(self):
        # One unrelated-but-valid blob referenced by every rule.
        b = self._valid_bundle()
        for rec in b["records"]:
            rec["field_a"]["evidence_refs"] = ["evidence.1"]
            rec["field_b"]["evidence_refs"] = ["evidence.1"]
        for a in b["rule_assertions"]:
            a["evidence_refs"] = ["evidence.1"]
        # content still contradicts (field_b value differs from evidence.1 bytes)
        b["records"][0]["field_b"]["value"] = "UNRELATED_LAUNDERED_VALUE"
        rc = run_engine(self._write(b), self._config())
        self.assertNotEqual(rc, 0, "single-blob laundering must be rejected")

    def test_claim_ceiling_overreach(self):
        b = self._valid_bundle()
        b["conclusion"]["claim_ceiling"] = "universal truth established"
        self.assertEqual(run_engine(self._write(b), self._config()), 20, "claim-ceiling overreach must exit 20")

    def test_external_action_forbidden(self):
        b = self._valid_bundle()
        b["conclusion"]["external_action_performed"] = True
        self.assertEqual(run_engine(self._write(b), self._config()), 21, "external action must exit 21")


if __name__ == "__main__":
    unittest.main()
