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


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class DiffCoverageGateTests(unittest.TestCase):
    """Every diff path must be accounted for by seed or generated."""

    @classmethod
    def setUpClass(cls):
        cls.request = _load_json(REQUEST_PATH)
        cls.authority = _load_json(AUTHORITY_PATH)
        result = subprocess.run(
            ["git", "diff", "--name-only", BASE_MAIN],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        if result.returncode != 0:
            cls.diff_paths: set[str] = set()
            cls.git_available = False
            return
        cls.git_available = True
        cls.diff_paths = {p for p in result.stdout.strip().split(chr(10)) if p}
        # Also include untracked new files that will be committed
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        if untracked.returncode == 0:
            cls.untracked = {p for p in untracked.stdout.strip().split(chr(10)) if p}
        else:
            cls.untracked = set()

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
        effective_diff = self.diff_paths | self.untracked
        generated = {item["path"] for item in self.authority["generated_outputs"]} & effective_diff
        extra = sorted((seeds | generated) - effective_diff)
        self.assertEqual(extra, [], f"Declared paths not in diff: {extra}")

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
