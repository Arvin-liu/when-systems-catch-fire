#!/usr/bin/env python3
"""repair-r3 shared red-team tests for RB09-CALLER-ASSERTED-SEMANTICS.

This is the explicit adversarial suite required at CP1. It drives the shared
engine with a real per-capability-style evaluator and asserts every control:

  positive pilot (exit 0)                                          -- recompute PASS
  semantically-false-but-Git-valid (exit 30)                       -- record contradicts rule
  unrelated-valid-evidence laundering (nonzero)                    -- single-blob defeat
  missing evaluator (exit 1)                                       -- req-7
  missing mandatory Git field (exit 4)                             -- r2 control preserved
  absolute / '..' / backslash path (exit 4)                        -- r2 control preserved
  fabricated exact head (exit 4)                                   -- r2 control preserved
  tampered blob/sha256 (exit 4)                                    -- r2 control preserved
  wrong direct predecessor (exit 3)                                -- parent binding
  external action (exit 21) / claim-ceiling (exit 20)              -- closure controls
"""
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

from tools.governance.semantic_evaluator import semantic_evaluate

REPO_ROOT = Path(__file__).resolve().parent.parent
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
REAL_COMMIT = "4ec769768d31c1fd0d7a6c066d235b4064606652"
REAL_PATH = "tools/governance/structured_capability_gate.py"


def _git(args):
    import subprocess
    return subprocess.run(["git", "-C", str(REPO_ROOT)] + args, capture_output=True, text=True)


def _blob_sha(commit, path):
    return _git(["rev-parse", f"{commit}:{path}"]).stdout.strip()


def _sha256_of_blob(commit, path):
    out = _git(["show", f"{commit}:{path}"]).stdout
    return "sha256:" + hashlib.sha256(out.encode()).hexdigest()


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
        "required": ["task_id", "parent_binding", "evidence_registry", "records", "facts", "rule_assertions", "conclusion"],
        "properties": {
            "evidence_registry": {"type": "array"}, "records": {"type": "array"},
            "facts": {"type": "object"}, "rule_assertions": {"type": "array"},
            "conclusion": {"type": "object"}, "parent_binding": {"type": "object"},
        },
    }


CONFIG = {
    "capability": "structured_capability_gate",
    "parent_id": "SYMBOLIC-SPHERE-I1",
    "parent_head": REAL_COMMIT,
    "schema": "",
    "fields": ["field_a", "field_b"],
    "rules": ["rule_alpha", "rule_beta"],
    "forbidden_claims": ["universal truth", "causal proof established", "ecosystem deployed"],
}


class SemanticEvaluatorRedTeam(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="r3-redteam-")
        sp = Path(cls._tmp) / "mini-schema.json"
        sp.write_text(json.dumps(minimal_schema()))
        cls.schema_path = sp
        cls.blob = _blob_sha(REAL_COMMIT, REAL_PATH)
        cls.sha = _sha256_of_blob(REAL_COMMIT, REAL_PATH)
        cls.content = _git(["show", f"{REAL_COMMIT}:{REAL_PATH}"]).stdout
        assert HEAD_RE.match(cls.blob) and cls.sha.startswith("sha256:")

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
                {"evidence_id": "evidence.1", "artifact": REAL_PATH, "exact_head": REAL_COMMIT,
                 "artifact_digest": self.sha, "rights_status": "REPOSITORY_INTERNAL",
                 "repository_relative_path": REAL_PATH, "commit_sha": REAL_COMMIT,
                 "blob_sha": self.blob, "sha256": self.sha,
                 "record_type": "ENGINE_SOURCE", "declared_role": "authoritative_engine"}
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
            "conclusion": {"statement": "engine hardened", "claim_ceiling": "candidate_only_repository_governance",
                           "history_preserved": True, "external_action_performed": False},
        }

    def _write(self, bundle):
        p = Path(self._tmp) / "bundle.json"
        p.write_text(json.dumps(bundle))
        return p

    def test_positive_pilot_passes(self):
        self.assertEqual(run_engine(self._write(self._valid_bundle()), self._config()), 0)

    def test_semantically_false_but_git_valid(self):
        b = self._valid_bundle()
        b["records"][0]["field_a"]["value"] = "CONTRADICTS_RULE_ALPHA_NOT_IN_EVIDENCE"
        rc = run_engine(self._write(b), self._config())
        self.assertEqual(rc, 30, f"rule_alpha (index 0) should fail with 30, got {rc}")

    def test_unrelated_valid_evidence_laundering(self):
        b = self._valid_bundle()
        for rec in b["records"]:
            rec["field_a"]["evidence_refs"] = ["evidence.1"]
            rec["field_b"]["evidence_refs"] = ["evidence.1"]
        for a in b["rule_assertions"]:
            a["evidence_refs"] = ["evidence.1"]
        b["records"][0]["field_b"]["value"] = "UNRELATED_LAUNDERED_VALUE"
        self.assertNotEqual(run_engine(self._write(b), self._config()), 0)

    def test_missing_evaluator(self):
        self.assertEqual(
            run_engine(self._write(self._valid_bundle()), self._config(), inject_evaluator=False), 1
        )

    def test_missing_mandatory_git_field(self):
        b = self._valid_bundle()
        del b["evidence_registry"][0]["blob_sha"]
        self.assertEqual(run_engine(self._write(b), self._config()), 4)

    def test_absolute_path(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["repository_relative_path"] = "/etc/hosts"
        self.assertEqual(run_engine(self._write(b), self._config()), 4)

    def test_dotdot_traversal(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["repository_relative_path"] = "../etc/passwd"
        self.assertEqual(run_engine(self._write(b), self._config()), 4)

    def test_backslash_path(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["repository_relative_path"] = "tools\\governance\\x.py"
        self.assertEqual(run_engine(self._write(b), self._config()), 4)

    def test_fabricated_exact_head(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["exact_head"] = "0" * 40
        self.assertEqual(run_engine(self._write(b), self._config()), 4)

    def test_tampered_sha256(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["sha256"] = "sha256:" + "0" * 64
        self.assertEqual(run_engine(self._write(b), self._config()), 4)

    def test_tampered_blob_sha(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["blob_sha"] = "0" * 40
        self.assertEqual(run_engine(self._write(b), self._config()), 4)

    def test_wrong_direct_predecessor(self):
        b = self._valid_bundle()
        b["parent_binding"]["exact_head"] = "0" * 40
        self.assertEqual(run_engine(self._write(b), self._config()), 3)

    def test_external_action(self):
        b = self._valid_bundle()
        b["conclusion"]["external_action_performed"] = True
        self.assertEqual(run_engine(self._write(b), self._config()), 21)

    def test_claim_ceiling(self):
        b = self._valid_bundle()
        b["conclusion"]["claim_ceiling"] = "universal truth established"
        self.assertEqual(run_engine(self._write(b), self._config()), 20)


if __name__ == "__main__":
    unittest.main()
