#!/usr/bin/env python3
"""P4B negative (attack) tests for registered-generator authority hardening.

Each scenario builds a self-contained temporary git repo, copies the REAL validator +
era_resolver + both schemas into it, then mutates the fixture to prove the validator
FAILS CLOSED on exactly the defect under test:

  - tool_digest_tamper        : live canonical_tool bytes != registry-pinned digest
  - missing_canonical_tool    : registry references a canonical_tool that does not exist
  - registry_missing_digest_pin: registry generator omits canonical_tool_digest_sha256
  - dual_authorization        : same output path claimed by producer_command AND registered_generator
  - self_authorization_cycle  : a generator's output is also listed as its own input
  - indirect_authority_cycle  : two generators form an input/output authority cycle

A positive (clean) scenario is included as the regression anchor.
"""

import hashlib
import json
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
GENREG_SCHEMA = REPO_ROOT / "schemas" / "operations" / "generator-registry.schema.json"


def _git(repo: Path, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _commit_base(tmp: Path) -> str:
    _git(tmp, "add", "-A")
    _git(tmp, "commit", "-q", "-m", "base")
    return subprocess.run(["git", "-C", str(tmp), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


def build_attack(tag: str, scenario: str):
    tmp = Path(tempfile.mkdtemp(prefix=f"att-{tag}-"))
    try:
        _git(tmp, "init", "-q")
        _git(tmp, "config", "user.email", "test@local")
        _git(tmp, "config", "user.name", "test")

        # --- base commit: validator, era_resolver, schemas, input, gitignore ---
        (tmp / "tools" / "operations").mkdir(parents=True)
        shutil.copy(VALIDATOR, tmp / "tools" / "operations" / "validate_generated_output_authority.py")
        shutil.copy(ERA_RESOLVER, tmp / "tools" / "operations" / "era_resolver.py")
        (tmp / "schemas" / "operations").mkdir(parents=True)
        shutil.copy(SCHEMA, tmp / "schemas" / "operations" / "generated-output-authority.schema.json")
        shutil.copy(GENREG_SCHEMA, tmp / "schemas" / "operations" / "generator-registry.schema.json")
        (tmp / ".gitignore").write_text("__pycache__/\n*.pyc\n")
        (tmp / "data" / "operations").mkdir(parents=True)
        (tmp / "data" / "operations" / "project-components.json").write_text(json.dumps({"x": 1}))

        base_sha = _commit_base(tmp)

        # ---- default (positive) fixture contents ----
        tool_a = "tools/operations/synth_tool.py"
        tool_a_content = "print('synth-a')\n"
        out_reg = f"data/synth/{tag}-registered.json"
        out_reg_content = f"registered {tag}\n"
        out_prod = f"data/synth/{tag}-producer.json"
        out_prod_content = f"producer {tag}\n"
        seed1 = f"docs/synth/{tag}.md"
        seed2 = f"data/synth/{tag}-cfg.json"

        registry = {
            "registry_version": "1.0.0",
            "generators": {
                "synth_gen": {
                    "generator_id": "synth_gen",
                    "canonical_tool": tool_a,
                    "canonical_tool_digest_sha256": _digest(tool_a_content),
                    "allowed_output_paths": [out_reg],
                    "required_input_authorities": ["data/operations/project-components.json"],
                    "freshness_mode": "byte_level_recompute",
                    "lifecycle_status": "active",
                    "authority_schema_version": "1.0.0",
                }
            },
        }
        authority_outputs = [
            {
                "path": out_prod,
                "producer_command": f"python {tool_a}",
                "producer_id": "synth_tool",
                "input_authorities": ["data/operations/project-components.json"],
                "output_type": "materialized_projection",
                "freshness_mode": "byte_level_recompute",
                "coverage_class": "generated_output",
                "justification": "synth producer output",
            },
            {
                "path": out_reg,
                "generator_id": "synth_gen",
                "canonical_tool": tool_a,
                "input_authorities": ["data/operations/project-components.json"],
                "output_type": "materialized_projection",
                "freshness_mode": "byte_level_recompute",
                "coverage_class": "generated_output",
                "lifecycle_status": "active",
                "authority_schema_version": "1.0.0",
                "content_digest_sha256": _digest(out_reg_content),
                "justification": "synth registered output",
            },
        ]
        live_tools = {tool_a: tool_a_content}
        live_outputs = {out_reg: out_reg_content, out_prod: out_prod_content}
        seeds = [seed1, seed2]

        # ---- scenario-specific mutations ----
        if scenario == "tool_digest_tamper":
            live_tools[tool_a] = "print('synth-a TAMPERED')\n"  # differs from pinned digest
        elif scenario == "missing_canonical_tool":
            registry["generators"]["synth_gen"]["canonical_tool"] = "tools/operations/does_not_exist.py"
            for o in authority_outputs:
                if o.get("generator_id") == "synth_gen":
                    o["canonical_tool"] = "tools/operations/does_not_exist.py"
        elif scenario == "registry_missing_digest_pin":
            del registry["generators"]["synth_gen"]["canonical_tool_digest_sha256"]
        elif scenario == "dual_authorization":
            # Same path (out_reg) claimed by BOTH producer_command and registered_generator.
            authority_outputs.append({
                "path": out_reg,
                "producer_command": f"python {tool_a}",
                "producer_id": "synth_tool",
                "input_authorities": ["data/operations/project-components.json"],
                "output_type": "materialized_projection",
                "freshness_mode": "byte_level_recompute",
                "coverage_class": "generated_output",
                "justification": "producer output duplicating a registered_generator path",
            })
        elif scenario == "self_authorization_cycle":
            registry["generators"]["synth_gen"]["allowed_output_paths"] = [out_reg]
            registry["generators"]["synth_gen"]["required_input_authorities"] = [out_reg]
            authority_outputs = [{
                "path": out_reg,
                "generator_id": "synth_gen",
                "canonical_tool": tool_a,
                "input_authorities": [out_reg],
                "output_type": "materialized_projection",
                "freshness_mode": "byte_level_recompute",
                "coverage_class": "generated_output",
                "lifecycle_status": "active",
                "authority_schema_version": "1.0.0",
                "content_digest_sha256": _digest(out_reg_content),
                "justification": "self-authorization cycle fixture",
            }]
            live_outputs = {out_reg: out_reg_content}
        elif scenario == "indirect_authority_cycle":
            tool_b = "tools/operations/synth_tool_b.py"
            tool_b_content = "print('synth-b')\n"
            out_b = f"data/synth/{tag}-registered-b.json"
            out_b_content = f"registered-b {tag}\n"
            registry = {
                "registry_version": "1.0.0",
                "generators": {
                    "gen_a": {
                        "generator_id": "gen_a",
                        "canonical_tool": tool_a,
                        "canonical_tool_digest_sha256": _digest(tool_a_content),
                        "allowed_output_paths": [out_reg],
                        "required_input_authorities": [out_b],
                        "freshness_mode": "byte_level_recompute",
                        "lifecycle_status": "active",
                        "authority_schema_version": "1.0.0",
                    },
                    "gen_b": {
                        "generator_id": "gen_b",
                        "canonical_tool": tool_b,
                        "canonical_tool_digest_sha256": _digest(tool_b_content),
                        "allowed_output_paths": [out_b],
                        "required_input_authorities": [out_reg],
                        "freshness_mode": "byte_level_recompute",
                        "lifecycle_status": "active",
                        "authority_schema_version": "1.0.0",
                    },
                },
            }
            authority_outputs = [
                {
                    "path": out_reg,
                    "generator_id": "gen_a",
                    "canonical_tool": tool_a,
                    "input_authorities": [out_b],
                    "output_type": "materialized_projection",
                    "freshness_mode": "byte_level_recompute",
                    "coverage_class": "generated_output",
                    "lifecycle_status": "active",
                    "authority_schema_version": "1.0.0",
                    "content_digest_sha256": _digest(out_reg_content),
                    "justification": "cycle node A",
                },
                {
                    "path": out_b,
                    "generator_id": "gen_b",
                    "canonical_tool": tool_b,
                    "input_authorities": [out_reg],
                    "output_type": "materialized_projection",
                    "freshness_mode": "byte_level_recompute",
                    "coverage_class": "generated_output",
                    "lifecycle_status": "active",
                    "authority_schema_version": "1.0.0",
                    "content_digest_sha256": _digest(out_b_content),
                    "justification": "cycle node B",
                },
            ]
            live_tools = {tool_a: tool_a_content, tool_b: tool_b_content}
            live_outputs = {out_reg: out_reg_content, out_b: out_b_content}
            seeds = [seed1, seed2, tool_b]

        # ---- write live (untracked) fixture files ----
        for rel, content in live_tools.items():
            p = tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        for rel, content in live_outputs.items():
            p = tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        (tmp / seed1).parent.mkdir(parents=True, exist_ok=True)
        (tmp / seed1).write_text(f"# {tag}\n")
        (tmp / seed2).parent.mkdir(parents=True, exist_ok=True)
        (tmp / seed2).write_text(json.dumps({"tag": tag}))

        (tmp / "data" / "operations" / "generator-registry.json").write_text(json.dumps(registry, indent=2))
        authority = {
            "description": f"Synthetic generated-output authority for P4B attack fixture {tag}",
            "schema_version": "1.0.0",
            "task_id": tag,
            "generated_outputs": authority_outputs,
        }
        (tmp / "data" / "operations" / "generated-output-authority.json").write_text(json.dumps(authority, indent=2))

        (tmp / "data" / "operations" / "propagation").mkdir(parents=True, exist_ok=True)
        req_path = tmp / "data" / "operations" / "propagation" / f"{tag}-request.json"
        changed_paths = [
            f"data/operations/propagation/{tag}-request.json",
            "data/operations/generator-registry.json",
            "data/operations/generated-output-authority.json",
        ] + seeds + list(live_tools.keys())
        req_path.write_text(json.dumps({
            "task_id": tag,
            "base_identity": base_sha,
            "changed_paths": changed_paths,
        }, indent=2))

        r = subprocess.run(
            [sys.executable, str(tmp / "tools" / "operations" / "validate_generated_output_authority.py"),
             "--request", str(req_path)],
            capture_output=True, text=True, cwd=str(tmp),
        )
        return r.returncode, r.stdout, r.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class TestRegisteredGeneratorAttack(unittest.TestCase):
    def test_positive(self):
        rc, out, err = build_attack("POS", "positive")
        self.assertEqual(rc, 0, f"P4B positive fixture should PASS (rc={rc})\n{out}\n{err}")

    def test_tool_digest_tamper(self):
        rc, out, err = build_attack("TAMPER", "tool_digest_tamper")
        self.assertNotEqual(rc, 0, f"tool digest tamper must FAIL\n{out}\n{err}")
        self.assertIn("canonical_tool digest mismatch", out,
                      f"expected tamper failure message\n{out}")

    def test_missing_canonical_tool(self):
        rc, out, err = build_attack("MISSING", "missing_canonical_tool")
        self.assertNotEqual(rc, 0, f"missing canonical tool must FAIL\n{out}\n{err}")
        self.assertIn("does NOT exist on disk", out,
                      f"expected missing-tool failure message\n{out}")

    def test_registry_missing_digest_pin(self):
        rc, out, err = build_attack("NOPIN", "registry_missing_digest_pin")
        self.assertNotEqual(rc, 0, f"registry missing digest pin must FAIL\n{out}\n{err}")
        self.assertIn("canonical_tool_digest_sha256", out,
                      f"expected digest-pin enforcement message\n{out}")

    def test_dual_authorization(self):
        rc, out, err = build_attack("DUAL", "dual_authorization")
        self.assertNotEqual(rc, 0, f"dual authorization must FAIL\n{out}\n{err}")
        self.assertIn("DUAL-AUTH", out, f"expected dual-auth failure message\n{out}")

    def test_self_authorization_cycle(self):
        rc, out, err = build_attack("SELF", "self_authorization_cycle")
        self.assertNotEqual(rc, 0, f"self-authorization cycle must FAIL\n{out}\n{err}")
        self.assertIn("SELF-AUTH", out, f"expected self-auth failure message\n{out}")

    def test_indirect_authority_cycle(self):
        rc, out, err = build_attack("CYCLE", "indirect_authority_cycle")
        self.assertNotEqual(rc, 0, f"indirect authority cycle must FAIL\n{out}\n{err}")
        self.assertIn("AUTHORITY-CYCLE", out, f"expected cycle failure message\n{out}")


if __name__ == "__main__":
    unittest.main()
