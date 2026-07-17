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
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / ".github" / "workflows" / "pages.yml"
TEXT = PAGES.read_text(encoding="utf-8")


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


if __name__ == "__main__":
    unittest.main()
