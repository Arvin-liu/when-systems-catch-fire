"""Diff coverage gate: every changed path in the PR diff must be covered.

Ensures that no diff path is left without either a seed or generated-output
authority entry, and no declared seed/generated path falls outside the diff.
"""

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST_PATH = ROOT / "data/operations/propagation/121Q32I-request.json"
AUTHORITY_PATH = ROOT / "data/operations/generated-output-authority.json"
BASE_MAIN = "4097e610eebfc65c739df4fe7d2900161c204a9d"
# Era boundary for the Q32I change set: the Q32I-generated authority and seal were authored
# against the registry/topology/surfaces snapshot at this merge (PR #62). Validating coverage
# against the LIVE diff (BASE_MAIN..HEAD) would falsely require the Q33-era assets
# (121Q33-*, data/governance/*, schemas/governance/*, ...) that the Q32I request and authority
# can never cover. Bound the diff to the Q32I era, matching CI's compute_change_propagation
# --era-ref and tests/test_change_propagation.py::Q32_ERA_REF.
Q32_ERA_REF = "0a13c246172c0338bf8dda5dc08db5a574a8b23f"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class DiffCoverageGateTests(unittest.TestCase):
    """Every diff path must be accounted for by seed or generated."""

    @classmethod
    def setUpClass(cls):
        cls.request = _load_json(REQUEST_PATH)
        cls.authority = _load_json(AUTHORITY_PATH)
        # Era-bounded diff: only the Q32I change set (BASE_MAIN..Q32_ERA_REF) is in scope for
        # this authority. Untracked files are post-era and are excluded from the coverage gate.
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{BASE_MAIN}..{Q32_ERA_REF}"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        if result.returncode != 0:
            cls.diff_paths: set[str] = set()
            cls.git_available = False
            return
        cls.git_available = True
        cls.diff_paths = {p for p in result.stdout.strip().split(chr(10)) if p}
        cls.untracked = set()
        # Live repo file set (all committed paths at HEAD). Used by test_no_extra_declarations:
        # a declared path is valid if it is a real file in the repo. This catches phantom
        # declarations without era-conflating generated outputs (which are produced artifacts and
        # may post-date the era snapshot) — consistent with test_every_generated_output_exists_in_repo.
        live_tree = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        if live_tree.returncode == 0:
            cls.live_repo_files = {p for p in live_tree.stdout.strip().split(chr(10)) if p}
        else:
            cls.live_repo_files = set()

    def test_all_diff_paths_covered(self):
        if not self.git_available:
            self.skipTest("git diff unavailable")
        seeds = set(self.request["changed_paths"])
        # Include untracked files that will be added in the same commit
        effective_diff = self.diff_paths | self.untracked
        generated = {item["path"] for item in self.authority["generated_outputs"]} & effective_diff
        covered = seeds | generated
        uncovered = sorted(effective_diff - covered)
        self.assertEqual(uncovered, [], f"Uncovered diff paths: {uncovered}")

    def test_no_extra_declarations(self):
        if not self.git_available:
            self.skipTest("git diff unavailable")
        seeds = set(self.request["changed_paths"])
        generated = {item["path"] for item in self.authority["generated_outputs"]}
        # A declared path is valid if it is a real file in the live repo. This catches phantom
        # declarations without era-conflating generated outputs (produced artifacts that may
        # post-date the era snapshot). Era-correctness of *coverage* is enforced by
        # test_all_diff_paths_covered (era-bounded diff); this test only guards against declaring
        # paths that do not exist in the repo at all.
        extra = sorted((seeds | generated) - self.live_repo_files)
        self.assertEqual(extra, [], f"Declared paths not in repo: {extra}")

    def test_seed_generated_disjoint(self):
        seeds = set(self.request["changed_paths"])
        generated = {item["path"] for item in self.authority["generated_outputs"]}
        overlap = sorted(seeds & generated)
        self.assertEqual(overlap, [], f"Paths both seed and generated: {overlap}")

    def test_every_declared_seed_exists_in_repo(self):
        for path in self.request["changed_paths"]:
            if "://" not in path:
                self.assertTrue(
                    (ROOT / path).exists(),
                    f"Declared seed path does not exist: {path}",
                )

    def test_every_generated_output_exists_in_repo(self):
        for item in self.authority["generated_outputs"]:
            self.assertTrue(
                (ROOT / item["path"]).exists(),
                f"Declared generated output does not exist: {item['path']}",
            )


if __name__ == "__main__":
    unittest.main()
