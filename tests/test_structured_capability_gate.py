#!/usr/bin/env python3
"""Independent fail-closed test for the shared structured-capability engine.

Directly exercises tools/governance/structured_capability_gate.py as a real CLI
with --bundle / --config-json, covering the four repair-r2 root blockers:
  RB09-ENGINE-PATH-CONTAINMENT
  RB09-MANDATORY-GIT-OBJECT-BINDING
  RB09-EXACT-HEAD-NONRESOLUTION
  RB09-CALLER-ASSERTED-SEMANTICS

A valid bundle is built from a REAL Git object in this repository so the engine
has authoritative bytes to recompute; every negative case must exit non-zero.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

def _repo_root():
    d = Path(__file__).resolve().parent
    out = subprocess.run(
        ["git", "-C", str(d), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    ).stdout.strip()
    return Path(out)


REPO_ROOT = _repo_root()
ENGINE = REPO_ROOT / "tools" / "governance" / "structured_capability_gate.py"
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")

# A stable real commit present in this repo (SYMBOLIC-SPHERE repair-r1 head).
REAL_COMMIT = "4ec769768d31c1fd0d7a6c066d235b4064606652"
REAL_PATH = "tools/governance/structured_capability_gate.py"


def _git(args):
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT)] + args, capture_output=True, text=True
    )


def _blob_sha(commit, path):
    return _git(["rev-parse", f"{commit}:{path}"]).stdout.strip()


def _sha256_of_blob(commit, path):
    out = _git(["show", f"{commit}:{path}"]).stdout
    return "sha256:" + hashlib.sha256(out.encode()).hexdigest()


def run_engine(bundle_path, config):
    cfg_path = bundle_path.with_suffix(".config.json")
    cfg_path.write_text(json.dumps(config))
    r = subprocess.run(
        [sys.executable, str(ENGINE), "--bundle", str(bundle_path), "--config-json", str(cfg_path)],
        capture_output=True, text=True,
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


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
                {"record_id": "record.1", "field_a": {"evidence_refs": ["evidence.1"]},
                 "field_b": {"evidence_refs": ["evidence.1"]}}
            ],
            "facts": {"rule_alpha": True, "rule_beta": True},
            "rule_assertions": [
                {"rule_id": "rule_alpha", "status": "PASS", "evidence_refs": ["evidence.1"]},
                {"rule_id": "rule_beta", "status": "PASS", "evidence_refs": ["evidence.1"]},
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

    def test_valid_bundle_passes(self):
        rc, out, err = run_engine(self._write(self._valid_bundle()), self._config())
        self.assertEqual(rc, 0, f"valid bundle should pass: {out} {err}")

    def test_absolute_path_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["repository_relative_path"] = "/etc/hosts"
        rc, out, _ = run_engine(self._write(b), self._config())
        self.assertNotEqual(rc, 0, "absolute path must be rejected")

    def test_dotdot_traversal_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["repository_relative_path"] = "../etc/passwd"
        rc, out, _ = run_engine(self._write(b), self._config())
        self.assertNotEqual(rc, 0, "'..' traversal must be rejected")

    def test_backslash_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["repository_relative_path"] = "tools\\governance\\x.py"
        rc, out, _ = run_engine(self._write(b), self._config())
        self.assertNotEqual(rc, 0, "backslash path must be rejected")

    def test_fabricated_exact_head_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["exact_head"] = "0" * 40
        rc, out, _ = run_engine(self._write(b), self._config())
        self.assertNotEqual(rc, 0, "non-resolving fabricated exact_head must be rejected")

    def test_missing_git_object_field_rejected(self):
        b = self._valid_bundle()
        del b["evidence_registry"][0]["commit_sha"]
        rc, out, _ = run_engine(self._write(b), self._config())
        self.assertNotEqual(rc, 0, "missing commit_sha must be rejected")

    def test_tampered_sha256_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["sha256"] = "sha256:" + "0" * 64
        rc, out, _ = run_engine(self._write(b), self._config())
        self.assertNotEqual(rc, 0, "tampered sha256 must be rejected")

    def test_tampered_blob_sha_rejected(self):
        b = self._valid_bundle()
        b["evidence_registry"][0]["blob_sha"] = "0" * 40
        rc, out, _ = run_engine(self._write(b), self._config())
        self.assertNotEqual(rc, 0, "tampered blob_sha must be rejected")

    def test_caller_asserted_facts_ignored(self):
        # facts=True and status=PASS, but the evidence points at a non-resolving
        # commit, so the engine must recompute and REJECT (not trust the flags).
        b = self._valid_bundle()
        b["evidence_registry"][0]["commit_sha"] = "0" * 40
        b["evidence_registry"][0]["exact_head"] = "0" * 40
        b["evidence_registry"][0]["blob_sha"] = self.blob
        b["evidence_registry"][0]["sha256"] = self.sha
        rc, out, _ = run_engine(self._write(b), self._config())
        self.assertNotEqual(rc, 0, "caller-asserted facts/status must not bypass evidence")

    def test_parent_binding_mismatch_rejected(self):
        b = self._valid_bundle()
        b["parent_binding"]["exact_head"] = "0" * 40
        rc, out, _ = run_engine(self._write(b), self._config())
        self.assertNotEqual(rc, 0, "parent head mismatch must be rejected")


if __name__ == "__main__":
    unittest.main()
