#!/usr/bin/env python3
"""Task-number-free generality test for the generated-output authority validator.

Proves the validator (P5 / N9 fix) is iteration-agnostic: it validates arbitrary
iteration ids (SYNTH-ALPHA, SYNTH-BETA) with no Q32I/Q33 hardcoding. Each case builds
a self-contained temporary git repository, copies the real validator + era_resolver +
schema into it, derives the base commit from the request's base_identity, and runs the
validator as a subprocess exactly as CI would.

Coverage model in each synthetic iteration:
  - base commit carries scripts/schema/inputs/registry/authority (NOT in the diff)
  - request + seed files + generated outputs are the only post-base (untracked) paths,
    so the diff window (base..HEAD + untracked) == seeds u generated.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = REPO_ROOT / "tools" / "operations" / "validate_generated_output_authority.py"
ERA_RESOLVER = REPO_ROOT / "tools" / "operations" / "era_resolver.py"
SCHEMA = REPO_ROOT / "schemas" / "operations" / "generated-output-authority.schema.json"


def _git(repo: Path, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_synth_iteration(tag: str, tamper: bool):
    tmp = Path(tempfile.mkdtemp(prefix=f"synth-{tag}-"))
    try:
        _git(tmp, "init", "-q")
        _git(tmp, "config", "user.email", "test@local")
        _git(tmp, "config", "user.name", "test")

        # --- files that live at the base commit (not part of the diff) ---
        (tmp / "tools" / "operations").mkdir(parents=True)
        shutil.copy(VALIDATOR, tmp / "tools" / "operations" / "validate_generated_output_authority.py")
        shutil.copy(ERA_RESOLVER, tmp / "tools" / "operations" / "era_resolver.py")
        (tmp / "schemas" / "operations").mkdir(parents=True)
        shutil.copy(SCHEMA, tmp / "schemas" / "operations" / "generated-output-authority.schema.json")
        (tmp / ".gitignore").write_text("__pycache__/\n*.pyc\n")

        (tmp / "data" / "operations").mkdir(parents=True)
        (tmp / "data" / "operations" / "project-components.json").write_text(json.dumps({"x": 1}))
        (tmp / "tools" / "operations" / "synth_tool.py").write_text("print('synth')\n")
        (tmp / "data" / "operations" / "generator-registry.json").write_text(json.dumps({
            "generators": {
                "synth_gen": {
                    "canonical_tool": "tools/operations/synth_tool.py",
                    "canonical_tool_digest_sha256": _sha256(tmp / "tools" / "operations" / "synth_tool.py"),
                    "allowed_output_paths": [f"data/synth/{tag}-out2.json"],
                    "required_input_authorities": ["data/operations/project-components.json"],
                }
            }
        }))

        # generated output paths
        gen1 = f"data/synth/{tag}-out.json"
        gen2 = f"data/synth/{tag}-out2.json"

        # Write gen2 (untracked) now so we can pin its digest into the authority before
        # the base commit. The file stays untracked (not added) and therefore appears in
        # the live diff window.
        (tmp / gen2).parent.mkdir(parents=True, exist_ok=True)
        (tmp / gen2).write_text(f"registered output {tag}\n")
        digest = _sha256(tmp / gen2)

        authority = {
            "description": f"Synthetic generated-output authority for iteration {tag} (task-number-free P5 fixture)",
            "schema_version": "1.0.0",
            "task_id": tag,
            "generated_outputs": [
                {
                    "path": gen1,
                    "producer_command": "python tools/operations/synth_tool.py",
                    "producer_id": "synth_tool",
                    "input_authorities": ["data/operations/project-components.json"],
                    "output_type": "materialized_projection",
                    "freshness_mode": "byte_level_recompute",
                    "coverage_class": "generated_output",
                    "justification": "synthetic producer_command output",
                },
                {
                    "path": gen2,
                    "generator_id": "synth_gen",
                    "canonical_tool": "tools/operations/synth_tool.py",
                    "input_authorities": ["data/operations/project-components.json"],
                    "output_type": "materialized_projection",
                    "freshness_mode": "byte_level_recompute",
                    "coverage_class": "generated_output",
                    "lifecycle_status": "active",
                    "authority_schema_version": "1.0.0",
                    "content_digest_sha256": digest,
                    "justification": "synthetic registered_generator output",
                },
            ],
        }
        (tmp / "data" / "operations" / "generated-output-authority.json").write_text(json.dumps(authority, indent=2))

        # commit the base (explicit paths; gen2 intentionally NOT added)
        _git(tmp, "add", ".gitignore", "tools", "schemas", "data/operations/project-components.json",
             "data/operations/generator-registry.json", "data/operations/generated-output-authority.json")
        _git(tmp, "commit", "-q", "-m", "base")
        base_sha = subprocess.run(["git", "-C", str(tmp), "rev-parse", "HEAD"],
                                  capture_output=True, text=True, check=True).stdout.strip()

        # --- post-base (untracked) files: they constitute the diff window ---
        seed1 = f"docs/synth/{tag}-note.md"
        seed2 = f"data/synth/{tag}-config.json"
        (tmp / "data" / "operations" / "propagation").mkdir(parents=True, exist_ok=True)
        req_path = tmp / "data" / "operations" / "propagation" / f"{tag}-request.json"
        req_path.write_text(json.dumps({
            "task_id": tag,
            "base_identity": base_sha,
            "changed_paths": [
                f"data/operations/propagation/{tag}-request.json",
                seed1,
                seed2,
            ],
        }, indent=2))
        (tmp / seed1).parent.mkdir(parents=True, exist_ok=True)
        (tmp / seed1).write_text(f"# {tag} note\n")
        (tmp / seed2).parent.mkdir(parents=True, exist_ok=True)
        (tmp / seed2).write_text(json.dumps({"tag": tag}))
        (tmp / gen1).parent.mkdir(parents=True, exist_ok=True)
        (tmp / gen1).write_text(f"producer output {tag}\n")

        if tamper:
            # tamper gen2 AFTER its digest was pinned -> live digest mismatch
            (tmp / gen2).write_text(f"registered output {tag} TAMPERED\n")

        r = subprocess.run(
            [sys.executable, str(tmp / "tools" / "operations" / "validate_generated_output_authority.py"),
             "--request", str(req_path)],
            capture_output=True, text=True, cwd=str(tmp),
        )
        return r.returncode, r.stdout, r.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class TestGeneratedOutputAuthorityGeneric(unittest.TestCase):
    def test_synth_alpha_positive(self):
        rc, out, err = build_synth_iteration("SYNTH-ALPHA", tamper=False)
        self.assertEqual(rc, 0, f"SYNTH-ALPHA positive failed (rc={rc})\n{out}\n{err}")

    def test_synth_beta_positive(self):
        rc, out, err = build_synth_iteration("SYNTH-BETA", tamper=False)
        self.assertEqual(rc, 0, f"SYNTH-BETA positive failed (rc={rc})\n{out}\n{err}")

    def test_synth_alpha_tamper_negative(self):
        rc, out, err = build_synth_iteration("SYNTH-ALPHA", tamper=True)
        self.assertNotEqual(rc, 0, f"SYNTH-ALPHA tamper should FAIL but passed\n{out}\n{err}")


if __name__ == "__main__":
    unittest.main()
