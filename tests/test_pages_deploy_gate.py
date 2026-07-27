"""Q32F4 — structural gate tests for the Pages deploy provenance.

These tests assert the ACTUAL conditions in .github/workflows/pages.yml and
evaluate them across an event matrix, rather than trusting a fixed string.
They run WITHOUT PyYAML (raw-text extraction) so they always execute in CI.

Enforced guarantees:
  * production deploy requires a REAL `push` to `main`
    (github.event_name == 'push' && github.ref == 'refs/heads/main');
  * workflow_dispatch (from main, a candidate branch, a tag, or with a
    candidate ref) can only build a candidate artifact and can NEVER deploy;
  * the build job records an auditable built_sha provenance step;
  * the deploy condition cannot silently regress to only checking github.ref;
  * workflow_dispatch declares a controlled candidate `ref` input.
"""
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / ".github" / "workflows" / "pages.yml"
TEXT = PAGES.read_text(encoding="utf-8")


# --- F5-B1 publish assertions (IGNITION-PAGES-PUBLIC-DOCUMENT-LINK-F5-B1-FIX-R1-20260728) ---
# Exact, deduplicated target set from the audit receipt (1111 Draft PR #75,
# RESULT.json -> recommended_single_batch). Source = repo path; Target = site/ path.
# This is the AUTHORITATIVE 13-file set, NOT the audit's prose summary figure
# ("14 cp / 4 P0 + 7 P1 + 1 template = 12"), which double-counted the 2 P2
# foundation JSONs as P1. See the F5-B1 fix receipt for the discrepancy analysis.
F5_B1_PUBLISH = [
    ("docs/project-current-state.md", "site/docs/project-current-state.md"),
    ("ITERATION.md", "site/ITERATION.md"),
    ("docs/ai-assistant-usage-reference.md", "site/docs/ai-assistant-usage-reference.md"),
    ("SUMMARY.md", "site/SUMMARY.md"),
    ("ARCHITECTURE.md", "site/ARCHITECTURE.md"),
    ("FOUNDATION.md", "site/FOUNDATION.md"),
    ("docs/foundation/README.md", "site/docs/foundation/README.md"),
    ("data/foundation/project-state.json", "site/data/foundation/project-state.json"),
    ("data/foundation/registry-manifest.json", "site/data/foundation/registry-manifest.json"),
    ("data/foundation/migration-summary.json", "site/data/foundation/migration-summary.json"),
    ("function-os-candidate/v0.2/README.md", "site/function-os-candidate/v0.2/README.md"),
    ("docs/participate.md", "site/docs/participate.md"),
    ("templates/publication/zhiyuan-writing-spec.md", "site/templates/publication/zhiyuan-writing-spec.md"),
]
F5_B1_SRC_TO_TARGET = dict(F5_B1_PUBLISH)


def _extract_cp_lines(text: str):
    """Return list of (src, target) tuples from `cp <src> site/<target>` lines."""
    out = []
    for m in re.finditer(r"^\s*cp\s+(\S+)\s+site/(\S+)\s*$", text, flags=re.M):
        out.append((m.group(1), "site/" + m.group(2)))
    return out


def _extract_md_links(md_text: str):
    out = []
    for m in re.finditer(r"\]\(\s*([^)\s]+)", md_text):
        out.append(m.group(1))
    return out


def _normalize_link(link: str, from_dir: str):
    """Resolve a markdown link to a repo-relative POSIX path, or None if external."""
    link = link.split("#")[0].strip()
    if not link or link.startswith(("http://", "https://", "mailto:", "data:")):
        return None
    if link.startswith("/"):
        return link.lstrip("/")
    base = ROOT / from_dir
    try:
        resolved = (base / link).resolve()
        rel = resolved.relative_to(ROOT)
    except Exception:
        return None
    return str(rel).replace(os.sep, "/")


def _extract_deploy_if(text: str) -> str:
    """Extract the deploy job's `if:` expression from the raw workflow text."""
    # Find the deploy job block
    m = re.search(r"^\s{2}deploy:\s*$", text, flags=re.M)
    if not m:
        raise AssertionError("deploy job not found in pages.yml")
    block = text[m.end():]
    # First `if:` line inside the deploy block (before the next top-level job at 2-space indent)
    for line in block.splitlines():
        stripped = line.strip()
        if re.match(r"^[a-zA-Z_]+:\s*$", line[:2] + stripped) and line[:3] == "  " and stripped.endswith(":") and not stripped.startswith("if"):
            # a sibling job started; stop
            if re.match(r"^\s{2}\w+:\s*$", line) and not line.strip().startswith("if"):
                break
        if stripped.startswith("if:"):
            return stripped[len("if:"):].strip()
    raise AssertionError("deploy `if:` condition not found")


def _eval_condition(expr: str, ctx: dict) -> bool:
    """Emulator for the subset of GitHub Actions expression syntax used by the
    deploy `if:` condition: string equality (== / !=), && and ||, parentheses,
    and github.* context refs."""
    e = expr.strip()
    m = re.match(r"^\$\{\{(.*)\}\}$", e, flags=re.S)
    if m:
        e = m.group(1).strip()

    def resolve(token: str):
        token = token.strip()
        if (token.startswith("'") and token.endswith("'")) or (token.startswith('"') and token.endswith('"')):
            return token[1:-1]
        if token.startswith("github."):
            key = token[len("github."):]
            if key not in ctx:
                raise KeyError(f"unknown github context key: {key}")
            return ctx[key]
        raise ValueError(f"unsupported token: {token!r}")

    def split_top(s: str, op: str):
        parts, depth, buf, i = [], 0, "", 0
        while i < len(s):
            ch = s[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if depth == 0 and s[i:i + len(op)] == op:
                parts.append(buf)
                buf = ""
                i += len(op)
                continue
            buf += ch
            i += 1
        parts.append(buf)
        return parts

    def eval_or(s: str) -> bool:
        return any(eval_and(p) for p in split_top(s, "||"))

    def eval_and(s: str) -> bool:
        return all(eval_cmp(p) for p in split_top(s, "&&"))

    def eval_cmp(s: str) -> bool:
        s = s.strip()
        if s.startswith("(") and s.endswith(")"):
            return eval_or(s[1:-1])
        if "==" in s:
            a, b = s.split("==", 1)
            return resolve(a) == resolve(b)
        if "!=" in s:
            a, b = s.split("!=", 1)
            return resolve(a) != resolve(b)
        return bool(resolve(s))

    return eval_or(e)


class PagesDeployGateTests(unittest.TestCase):
    def setUp(self):
        self.deploy_if = _extract_deploy_if(TEXT)

    def test_deploy_condition_requires_push_event(self):
        self.assertIn("github.event_name", self.deploy_if)
        self.assertIn("'push'", self.deploy_if)
        self.assertIn("github.ref", self.deploy_if)
        self.assertIn("refs/heads/main", self.deploy_if)

    def test_deploy_gate_not_ref_only(self):
        """Guard against regressing back to `github.ref == 'refs/heads/main'` only."""
        normalized = re.sub(r"\s+", "", self.deploy_if)
        self.assertNotEqual(normalized, "github.ref=='refs/heads/main'")

    def test_event_matrix(self):
        cases = [
            ("push to main", {"event_name": "push", "ref": "refs/heads/main"}, True),
            ("dispatch on main, empty ref",
             {"event_name": "workflow_dispatch", "ref": "refs/heads/main"}, False),
            ("dispatch on main + candidate SHA (ref still main)",
             {"event_name": "workflow_dispatch", "ref": "refs/heads/main"}, False),
            ("dispatch on candidate branch",
             {"event_name": "workflow_dispatch", "ref": "refs/heads/agent/121q32-typed-change-propagation"}, False),
            ("dispatch on tag",
             {"event_name": "workflow_dispatch", "ref": "refs/tags/v1"}, False),
            ("push to non-main branch",
             {"event_name": "push", "ref": "refs/heads/agent/121q32-typed-change-propagation"}, False),
        ]
        for desc, ctx, expect in cases:
            with self.subTest(desc):
                self.assertEqual(_eval_condition(self.deploy_if, ctx), expect,
                                 f"deploy gate mismatch for: {desc}")

    def test_build_records_provenance(self):
        self.assertIn("built_sha", TEXT)
        self.assertIn("git rev-parse HEAD", TEXT)

    def test_workflow_dispatch_ref_input_declared(self):
        # workflow_dispatch present with a `ref` input
        self.assertIn("workflow_dispatch:", TEXT)
        wd_idx = TEXT.index("workflow_dispatch:")
        wd_block = TEXT[wd_idx:wd_idx + 400]
        self.assertIn("inputs:", wd_block)
        self.assertIn("ref:", wd_block)

    def test_emulator_detects_ref_only_regression(self):
        """Sanity: a ref-only gate WOULD wrongly deploy on dispatch-from-main;
        prove the emulator catches that so the matrix test is meaningful."""
        ref_only = "github.ref == 'refs/heads/main'"
        self.assertTrue(_eval_condition(
            ref_only, {"event_name": "workflow_dispatch", "ref": "refs/heads/main"}))
        # And the real gate must NOT deploy in that same scenario:
        self.assertFalse(_eval_condition(
            self.deploy_if, {"event_name": "workflow_dispatch", "ref": "refs/heads/main"}))


class PagesF5B1PublishTests(unittest.TestCase):
    """F5-B1 fix verification (IGNITION-PAGES-PUBLIC-DOCUMENT-LINK-F5-B1-FIX-R1-20260728).

    Asserts the Pages build now publishes the authoritative 13-file F5-B1 set
    that the homepage README and published docs/USAGE.md link to (systemic 404
    fixed). See the audit receipt (1111 Draft PR #75) and the F5-B1 fix receipt.
    """

    def setUp(self):
        self.cp_pairs = _extract_cp_lines(TEXT)
        self.published_targets = {t for _, t in self.cp_pairs}
        self.published_srcs = {s for s, _ in self.cp_pairs}

    def test_f5b1_exact_target_count(self):
        """Authoritative F5-B1 set is exactly 13 cp lines (NOT the audit's prose
        '14 cp / 12 files' summary, which double-counted 2 P2 foundation JSONs)."""
        published_f5 = [(s, t) for s, t in self.cp_pairs if (s, t) in F5_B1_PUBLISH]
        self.assertEqual(len(published_f5), 13,
                         f"expected 13 F5-B1 cp lines, found {len(published_f5)}")

    def test_f5b1_source_files_exist(self):
        """(a) every F5-B1 source file exists in the repo."""
        missing = [s for s, _ in F5_B1_PUBLISH if not (ROOT / s).is_file()]
        self.assertEqual(missing, [],
                         f"F5-B1 source files missing from repo: {missing}")

    def test_f5b1_build_script_publishes_each_target(self):
        """(b) the build script publishes every F5-B1 target, including the
        corrected `mkdir -p site/data/foundation` the audit's cp block omitted."""
        for src, target in F5_B1_PUBLISH:
            with self.subTest(src):
                self.assertIn((src, target), self.cp_pairs,
                              f"pages.yml missing cp line for {src} -> {target}")
        self.assertIn("mkdir -p site/data/foundation", TEXT,
                      "pages.yml must create site/data/foundation before copying into it")

    def test_f5b1_candidate_artifact_contains_targets(self):
        """(c) if a built candidate artifact directory is supplied via
        PAGES_CANDIDATE_ARTIFACT_DIR, every F5-B1 target must be present.
        Skipped in normal pytest runs; the real artifact is verified by the
        Pages candidate-build step (req #8) and the CI download check."""
        art = os.environ.get("PAGES_CANDIDATE_ARTIFACT_DIR")
        if not art:
            self.skipTest("PAGES_CANDIDATE_ARTIFACT_DIR not set")
        missing = [t for _, t in F5_B1_PUBLISH if not (Path(art) / t).is_file()]
        self.assertEqual(missing, [],
                         f"F5-B1 targets missing from candidate artifact: {missing}")

    def test_f5b1_homepage_and_usage_links_resolve(self):
        """(d) every F5-B1 link referenced by the homepage README or the
        published docs/USAGE.md resolves to a target the build publishes."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        usage = (ROOT / "docs" / "USAGE.md").read_text(encoding="utf-8")
        referenced = set()
        for lnk in _extract_md_links(readme):
            norm = _normalize_link(lnk, "")
            if norm in F5_B1_SRC_TO_TARGET:
                referenced.add(norm)
        for lnk in _extract_md_links(usage):
            norm = _normalize_link(lnk, "docs")
            if norm in F5_B1_SRC_TO_TARGET:
                referenced.add(norm)
        self.assertGreater(len(referenced), 0,
                           "no F5-B1 links found in homepage README or docs/USAGE.md")
        for src in referenced:
            with self.subTest(src):
                self.assertIn(F5_B1_SRC_TO_TARGET[src], self.published_targets,
                              f"F5-B1 link target not published: {src}")


if __name__ == "__main__":
    unittest.main()
