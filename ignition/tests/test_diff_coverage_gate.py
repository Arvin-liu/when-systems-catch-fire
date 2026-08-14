"""Diff coverage gate: every changed path in the PR diff must be covered.

Ensures that no diff path is left without either a seed or generated-output
authority entry, and no declared seed/generated path falls outside the diff.

The era window (base..era_ref) is derived GENERICALLY from the iteration manifest
via tools/operations/era_resolver.py — no hardcoded task id or commit SHA in the
test or production path. A merged (frozen) iteration is bounded to its merge commit;
an unmerged (live) candidate validates against base..HEAD.
"""

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
# The test's logical application namespace remains ``ignition/`` while Git
# commands must run from the formal repository root after root normalization.
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "tools" / "operations"))
try:
    from era_resolver import resolve_era_for_request
except ImportError:
    _spec = importlib.util.spec_from_file_location(
        "era_resolver", ROOT / "tools" / "operations" / "era_resolver.py"
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    resolve_era_for_request = _mod.resolve_era_for_request

REQUEST_PATH = ROOT / "data/operations/propagation/121Q32I-request.json"
AUTHORITY_PATH = ROOT / "data/operations/generated-output-authority.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class DiffCoverageGateTests(unittest.TestCase):
    """Every diff path must be accounted for by seed or generated."""

    @classmethod
    def setUpClass(cls):
        cls.request = _load_json(REQUEST_PATH)
        cls.authority = _load_json(AUTHORITY_PATH)
        # Derive the era window generically from the iteration manifest (no hardcoded
        # BASE_MAIN / Q32_ERA_REF). For a merged iteration this yields base..merge_commit
        # (frozen era); for a live candidate it yields base..HEAD.
        era = resolve_era_for_request(ROOT, cls.request)
        if era is None:
            cls.git_available = False
            cls.diff_paths: set[str] = set()
            cls.era_ref = None
            return
        cls.base = era["base"]
        cls.era_ref = era["era_ref"]
        diff_spec = f"{cls.base}..{cls.era_ref}" if cls.era_ref else f"{cls.base}..HEAD"
        result = subprocess.run(
            ["git", "diff", "--name-only", diff_spec],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        if result.returncode != 0:
            cls.diff_paths = set()
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
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        if live_tree.returncode == 0:
            cls.live_repo_files = {p for p in live_tree.stdout.strip().split(chr(10)) if p}
        else:
            cls.live_repo_files = set()
        cls.era_repo_files = set()
        if cls.era_ref:
            era_tree = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", cls.era_ref],
                capture_output=True, text=True, cwd=str(REPO_ROOT),
            )
            if era_tree.returncode == 0:
                cls.era_repo_files = {p for p in era_tree.stdout.strip().split(chr(10)) if p}

    def test_all_diff_paths_covered(self):
        if not self.git_available:
            self.skipTest("git diff unavailable")
        seeds = set(self.request["changed_paths"])
        # Untracked files only matter for a LIVE era (base..HEAD). For a frozen (sealed)
        # era they post-date the era boundary and must not be folded into coverage.
        effective_diff = self.diff_paths
        if self.era_ref is None:
            effective_diff = effective_diff | self.untracked
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
        # Frozen requests may legitimately name files later retired from the
        # current tree. They must exist in either the current tree or the sealed
        # era tree; this preserves history without requiring obsolete products
        # such as Pages to remain maintained forever.
        extra = sorted((seeds | generated) - (self.live_repo_files | self.era_repo_files))
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
                    any(candidate.exists() for candidate in self._current_candidates(path)) or path in self.era_repo_files,
                    f"Declared seed path exists neither now nor in its sealed era: {path}",
                )

    def test_every_generated_output_exists_in_repo(self):
        for item in self.authority["generated_outputs"]:
            self.assertTrue(
                any(candidate.exists() for candidate in self._current_candidates(item["path"])),
                f"Declared generated output does not exist: {item['path']}",
            )

    @staticmethod
    def _current_candidates(path: str) -> list[Path]:
        """Resolve a legacy app-root path against the current split layout."""
        candidates = [ROOT / path, REPO_ROOT / path, REPO_ROOT / "ignition" / path]
        if path == "README.md":
            candidates.append(REPO_ROOT / ".github/README.md")
        if path.startswith(".github/"):
            candidates.append(REPO_ROOT / path)
        return list(dict.fromkeys(candidates))


if __name__ == "__main__":
    unittest.main()
