"""Era generalization (P4 / F6) regression tests.

These guard the fix for V18 finding F6 (era SHA / task special-casing) and the Q33
coverage closure (F5). The diff-coverage / authority-validation era must be derived
GENERICALLY from each iteration manifest — never hardcoded by task id or commit SHA —
and historical (frozen/merged) iterations must not be conflated with the live
(unmerged) candidate.

Tests:
  a. every changed path is uniquely covered (seed XOR generated; no gap, no double count)
  b. a path declared as both seed and generated is rejected (disjointness)
  c. a declared path outside the diff/repo is rejected (no phantom coverage)
  d. a live candidate resolves to era_ref=None while a merged iteration resolves to a
     frozen era_ref (historical vs live not conflated)
  e. no task id / SHA is special-cased: every iteration manifest resolves generically,
     and era_resolver.py contains no hardcoded task id or 40-hex SHA in its production path
  f. the generic resolver reproduces the CI-era boundary exactly (Q32I -> 0a13c246...);
     historical iterations stay frozen and are not mechanically re-derived against live state
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "operations"))
try:
    from era_resolver import resolve_era, resolve_era_for_request
except ImportError:
    _spec = importlib.util.spec_from_file_location(
        "era_resolver", ROOT / "tools" / "operations" / "era_resolver.py"
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    resolve_era = _mod.resolve_era
    resolve_era_for_request = _mod.resolve_era_for_request

ITER_DIR = ROOT / "data" / "operations" / "iterations"
AUTHORITY_PATH = ROOT / "data" / "operations" / "generated-output-authority.json"
VALIDATOR = ROOT / "tools" / "operations" / "validate_generated_output_authority.py"

# Merged (frozen-era) iterations that must resolve to a non-None era_ref.
# 121Q33 is genuinely merged into main (its merge_commit
# cf321f92014268af40cf9aa9231fe8a4f814b031 is an ancestor of origin/main), so its
# era_ref is the sealed merge commit, not None — it belongs in FROZEN_TASKS.
FROZEN_TASKS = ["121Q25", "121Q25C", "121Q25D", "121Q32", "121Q32I", "121Q33"]
# Live (unmerged) candidate iterations — era_ref must be None.
LIVE_TASKS = ["121Q25B"]
# CI's compute_change_propagation --era-ref for the Q32I change set. The generic
# resolver must reproduce this exact boundary (no drift). Only a TEST may name it.
CI_Q32I_ERA_REF = "0a13c246172c0338bf8dda5dc08db5a574a8b23f"


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _run_validator(request_path: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--request", str(request_path)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return result.stdout + result.stderr


class EraResolverGeneralizationTests(unittest.TestCase):
    # ---- (e) no special-casing in the production path ----------------------------
    def test_no_hardcoded_sha_in_resolver(self):
        src = (ROOT / "tools" / "operations" / "era_resolver.py").read_text(encoding="utf-8")
        self.assertNotRegex(
            src, r'["\']?[0-9a-f]{40}["\']?',
            "era_resolver must not hardcode any 40-hex commit SHA in its production path",
        )

    def test_no_hardcoded_task_id_in_resolver(self):
        src = (ROOT / "tools" / "operations" / "era_resolver.py").read_text(encoding="utf-8")
        self.assertNotRegex(
            src, r'121Q\d+',
            "era_resolver must not special-case any task id in its production path",
        )

    def test_all_iterations_resolve_generically(self):
        manifests = sorted(ITER_DIR.glob("121Q*.json"))
        self.assertTrue(manifests, "expected iteration manifests to exist")
        for m in manifests:
            task = m.stem
            era = resolve_era(ROOT, task)
            self.assertIsNotNone(era, f"{task}: must resolve generically from its manifest")
            self.assertEqual(len(era["base"]), 40, f"{task}: base must be a 40-hex SHA")
            self.assertTrue(
                era["era_ref"] is None or len(era["era_ref"]) == 40,
                f"{task}: era_ref must be None (live) or a 40-hex SHA (frozen)",
            )

    # ---- (d) historical vs live era not conflated --------------------------------
    def test_frozen_iterations_resolve_to_era_ref(self):
        for task in FROZEN_TASKS:
            era = resolve_era(ROOT, task)
            self.assertIsNotNone(era, f"{task}: manifest should resolve")
            self.assertIsNotNone(
                era["era_ref"], f"{task}: merged iteration must have a frozen era_ref"
            )

    def test_live_iteration_resolves_to_none_era_ref(self):
        for task in LIVE_TASKS:
            era = resolve_era(ROOT, task)
            self.assertIsNotNone(era)
            self.assertIsNone(
                era["era_ref"], f"{task}: live candidate must use base..HEAD (era_ref=None)"
            )

    def test_resolve_for_request_reads_task_id(self):
        # resolve_era_for_request must read task_id from the request and resolve
        # generically (no special-casing). 121Q25B is a live (unmerged) candidate,
        # so era_ref is None and the diff window is base..HEAD. (121Q33 is merged;
        # its frozen era_ref is covered by test_frozen_iterations_resolve_to_era_ref.)
        req = {"task_id": "121Q25B"}
        era = resolve_era_for_request(ROOT, req)
        self.assertIsNone(era["era_ref"])
        self.assertEqual(
            era["base"], "7fc4b309720ea1b4e9c4b47477c2f423860d53df"
        )

    # ---- (f) generic resolver reproduces CI-era boundary exactly -----------------
    def test_resolver_reproduces_ci_era_ref(self):
        era = resolve_era(ROOT, "121Q32I")
        self.assertIsNotNone(era)
        self.assertEqual(
            era["era_ref"], CI_Q32I_ERA_REF,
            "generic resolver must reproduce the CI-era boundary for Q32I (no drift)",
        )

    # ---- stale request base_identity must not drive the diff window --------------
    def test_stale_request_base_identity_not_used(self):
        # The validator derives the diff base from the manifest, not from a possibly
        # stale request base_identity. A crafted request with a wrong base_identity must
        # still resolve to the manifest-derived base.
        req = {"task_id": "121Q33", "base_identity": "0" * 40}
        era = resolve_era_for_request(ROOT, req)
        self.assertEqual(
            era["base"], "f54577a9084d0ac6e374341d96836c5d52bc3b8c"
        )

    # ---- (a) every changed path uniquely covered (Q33 live candidate) ------------
    def test_q33_changed_paths_uniquely_covered(self):
        req = _load(ROOT / "data/operations/propagation/121Q33-request.json")
        authority = _load(AUTHORITY_PATH)
        era = resolve_era_for_request(ROOT, req)
        self.assertIsNotNone(era)
        diff_spec = f"{era['base']}..{era['era_ref']}" if era["era_ref"] else f"{era['base']}..HEAD"
        result = subprocess.run(
            ["git", "diff", "--name-only", diff_spec],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        self.assertEqual(result.returncode, 0, "git diff must succeed")
        diff_paths = {p for p in result.stdout.strip().splitlines() if p}
        if era["era_ref"] is None:
            untracked = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True, text=True, cwd=str(ROOT),
            )
            if untracked.returncode == 0:
                diff_paths |= {p for p in untracked.stdout.splitlines() if p}

        seeds = set(req["changed_paths"])
        generated = {item["path"] for item in authority["generated_outputs"]} & diff_paths

        # Unique coverage: each diff path is covered exactly once (seed XOR generated).
        overlap = seeds & generated
        self.assertEqual(overlap, set(), f"paths both seed and generated: {sorted(overlap)}")
        covered = seeds | generated
        self.assertEqual(
            covered, diff_paths,
            f"coverage gap/extra: uncovered={sorted(diff_paths - covered)}, "
            f"extra={sorted(covered - diff_paths)}",
        )

    # ---- (b) seed/generated overlap is rejected ----------------------------------
    def test_seed_generated_overlap_rejected(self):
        req = _load(ROOT / "data/operations/propagation/121Q33-request.json")
        authority = _load(AUTHORITY_PATH)
        # Pick a real generated output that exists on disk and is in the Q33 diff.
        gen_path = next(
            item["path"] for item in authority["generated_outputs"]
            if (ROOT / item["path"]).exists()
        )
        req["changed_paths"] = list(req["changed_paths"]) + [gen_path]
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", dir=str(ROOT / "data" / "operations" / "propagation"),
            delete=False, encoding="utf-8",
        ) as tf:
            tf.write(json.dumps(req, ensure_ascii=False))
            tmp_path = Path(tf.name)
        try:
            out = _run_validator(tmp_path)
        finally:
            tmp_path.unlink()
        self.assertIn(
            "both seed and generated", out,
            "validator must reject a path declared as both seed and generated",
        )

    # ---- (c) declared path outside diff/repo is rejected ------------------------
    def test_phantom_declared_path_rejected(self):
        req = _load(ROOT / "data/operations/propagation/121Q33-request.json")
        phantom = "data/operations/propagation/this-path-does-not-exist-anywhere-xyz.json"
        self.assertNotIn(phantom, req["changed_paths"])
        req["changed_paths"] = list(req["changed_paths"]) + [phantom]
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", dir=str(ROOT / "data" / "operations" / "propagation"),
            delete=False, encoding="utf-8",
        ) as tf:
            tf.write(json.dumps(req, ensure_ascii=False))
            tmp_path = Path(tf.name)
        try:
            out = _run_validator(tmp_path)
        finally:
            tmp_path.unlink()
        self.assertIn(
            "Declared but not in diff", out,
            "validator must reject a declared path that is outside the diff",
        )


if __name__ == "__main__":
    unittest.main()
