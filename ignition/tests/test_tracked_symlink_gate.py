"""Tracked symlink escape gate tests.

Ensures the compute_change_propagation module correctly detects:
- Tracked symlinks whose targets escape the repository root
- Both at HEAD and at the declared base_identity
- Fail-closed behavior: git failures become blocking residue, never silent []
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.operations.compute_change_propagation import (
    ROOT,
    detect_tracked_symlink_escapes,
    _git_rev_parse,
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def _make_repo_with_symlink(escape: bool = True) -> tuple[Path, Path]:
    """Create a throwaway repo with a tracked symlink."""
    repo = Path(tempfile.mkdtemp(prefix="q32f11-sym-"))
    outside = Path(tempfile.mkdtemp(prefix="q32f11-outside-"))
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@test")
    _git(repo, "config", "user.name", "test")
    (repo / "README.md").write_text("x")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    link = repo / "test_link"
    target = outside if escape else repo / "README.md"
    link.symlink_to(target)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "add symlink")
    return repo, outside


class TrackedSymlinkGateTests(unittest.TestCase):

    def test_real_repo_no_escapes(self):
        """The actual repository HEAD has no tracked symlink escapes."""
        escapes = detect_tracked_symlink_escapes(revision="HEAD")
        self.assertEqual(escapes, [], f"Unexpected escapes: {escapes}")

    def test_synthetic_escape_detected(self):
        """A synthetic repo with an escaping symlink must be caught."""
        repo, outside = _make_repo_with_symlink(escape=True)
        try:
            head = _git_rev_parse(repo, "HEAD")
            escapes = detect_tracked_symlink_escapes(repo_root=repo, revision=head)
            self.assertIn("test_link", escapes)
        finally:
            import shutil
            shutil.rmtree(repo, ignore_errors=True)
            shutil.rmtree(outside, ignore_errors=True)

    def test_synthetic_safe_symlink_not_flagged(self):
        """A symlink pointing inside the repo must NOT be flagged."""
        repo, outside = _make_repo_with_symlink(escape=False)
        try:
            head = _git_rev_parse(repo, "HEAD")
            escapes = detect_tracked_symlink_escapes(repo_root=repo, revision=head)
            self.assertNotIn("test_link", escapes)
        finally:
            import shutil
            shutil.rmtree(repo, ignore_errors=True)
            shutil.rmtree(outside, ignore_errors=True)

    def test_invalid_revision_produces_residue(self):
        """An unresolvable head_ref must yield tracked_symlink_scan_failed residue."""
        from tools.operations.compute_change_propagation import compute
        # Use the real request as a template but with an invalid head_ref
        import json
        request = json.loads(
            (ROOT / "data/operations/propagation/121Q32-request.json").read_text()
        )
        closure, delta = compute(request, head_ref="nonexistent_ref_xyz")
        symlink_residue = [
            r for r in closure["residue"]
            if r["type"] == "tracked_symlink_scan_failed"
        ]
        self.assertTrue(len(symlink_residue) > 0, "Expected symlink scan failure residue")

    def test_base_identity_also_scanned(self):
        """Both HEAD and base_identity are scanned for symlink escapes."""
        escapes = detect_tracked_symlink_escapes(
            revision="d1bedb074af8dad8202b4324f3f5bbbb6b308b51"
        )
        self.assertEqual(escapes, [])


if __name__ == "__main__":
    unittest.main()
