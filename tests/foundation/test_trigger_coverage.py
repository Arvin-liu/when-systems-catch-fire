#!/usr/bin/env python3
"""Layer B trigger coverage (Task 107 §4).

Proves the governed classification source is the single source of truth for the
authoritative-input boundary, and that Layer B (heavy Foundation validation)
actually triggers on authoritative-input changes -- the exact gap that let the
drift lie dormant through PR #160/#161.

Scenarios covered here:
  * 5  authoritative input change must trigger (not silently skip) Layer B.
  * the preflight authoritative set == the discovery engine's authoritative boundary
    (single governed source, contract §4 Layer B).
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "foundation"))
import validate_repository_path_classification as preflight  # noqa: E402

CJK = ("统一函数总表/", "统一案例总表/")

# NOTE: this test is intentionally stdlib-only (no import of the discovery engine)
# so it can run in the fast Layer A preflight without pulling heavy dependencies.


def _discovery_nonauthoritative_prefixes() -> tuple[str, ...]:
    """Read the discovery engine's governed input boundary without importing it."""
    src = (ROOT / "tools/foundation/adjudicate_nonfunction_claims.py").read_text(encoding="utf-8")
    m = re.search(r"NON_AUTHORITATIVE_PREFIXES\s*=\s*\(([^)]*)\)", src, re.S)
    if not m:
        raise RuntimeError("could not locate NON_AUTHORITATIVE_PREFIXES in discovery engine")
    items = re.findall(r'"([^"]+)"', m.group(1))
    return tuple(items)


def _discovery_authoritative_prefixes() -> tuple[str, ...]:
    """Read the discovery engine's authoritative (fresh claim) source prefixes.

    These are the two CJK master tables; everything else scanned is either a
    governed/non-authoritative record or historical/audit context.
    """
    src = (ROOT / "tools/foundation/adjudicate_nonfunction_claims.py").read_text(encoding="utf-8")
    # Match the HISTORICAL_OR_AUDIT_RECORD prefix tuple's authoritative (CJK) entries:
    #   path.startswith(("统一函数总表/", "统一案例总表/", "reports/", ...))
    m = re.search(r'path\.startswith\(\(([^)]*)\)', src, re.S)
    if not m:
        raise RuntimeError("could not locate authoritative prefix tuple in discovery engine")
    items = re.findall(r'"([^"]+)"', m.group(1))
    # The authoritative (fresh claim) sources are exactly the two CJK tables.
    return tuple(p for p in items if p in CJK)


class AuthoritativeBoundaryTest(unittest.TestCase):
    def test_authoritative_set_is_two_cjk_tables(self) -> None:
        self.assertEqual(preflight.AUTHORITATIVE_PREFIXES, CJK)

    def test_discovery_nonauthoritative_disjoint_from_authoritative(self) -> None:
        nonauth = _discovery_nonauthoritative_prefixes()
        for p in nonauth:
            self.assertFalse(
                any(p.startswith(c) or c.startswith(p) for c in CJK),
                f"{p!r} overlaps the authoritative allowlist",
            )

    def test_preflight_never_mislabels_nonauthoritative_as_authoritative(self) -> None:
        nonauth = _discovery_nonauthoritative_prefixes()
        for p in nonauth:
            sample = p.rstrip("/") + "/sample.md"
            cat, _ = preflight.classify(sample)
            self.assertNotEqual(
                cat, "AUTHORITATIVE_CLAIM_INPUT",
                f"{sample!r} must not be classified authoritative (anti-backflow)",
            )

    def test_preflight_authoritative_matches_discovery_boundary(self) -> None:
        # The discovery engine scans claim fragments for every path NOT in
        # NON_AUTHORITATIVE_PREFIXES; among those, only the two CJK tables are the
        # fresh authoritative (E-promotable) sources. The preflight must agree exactly.
        self.assertEqual(set(preflight.AUTHORITATIVE_PREFIXES), set(CJK))
        for p in CJK:
            cat, _ = preflight.classify(p + "x.md")
            self.assertEqual(cat, "AUTHORITATIVE_CLAIM_INPUT")

    def test_discovery_authoritative_is_two_cjk_tables(self) -> None:
        self.assertEqual(_discovery_authoritative_prefixes(), CJK)


class LayerBTriggerTest(unittest.TestCase):
    """Scenario 5: an authoritative-input change must reach Layer B.

    Reads .github/workflows/foundation-validation.yml and asserts the heavy
    Foundation validation is not gated behind a narrow `paths:` filter that would
    omit the authoritative CJK-table directories (the PR #160/#161 gap).
    """

    def _on_block(self) -> str:
        path = ROOT / ".github/workflows/foundation-validation.yml"
        return path.read_text(encoding="utf-8")

    def test_layer_b_runs_task106_propagation_proof(self) -> None:
        text = self._on_block()
        self.assertIn("validate_reconciliation.py --check", text,
                      "Layer B must run the task-106 propagation reconciliation step (contract §6)")

    def test_layer_b_triggers_on_authoritative_change(self) -> None:
        text = self._on_block()
        # Within the `on:` trigger, find any `paths:` list and ensure it either
        # is absent (broad trigger) or explicitly includes the authoritative dirs.
        # Match `paths:` only inside a trigger block (heuristic: lines indented under
        # `pull_request:` / `push:`). We scan for a `paths:` whose listed globs omit CJK.
        has_narrow_paths = False
        for m in re.finditer(r"paths:\s*\n((?:\s*-\s*[^\n]+\n)+)", text):
            block = m.group(1)
            listed = re.findall(r"-\s*([^\n#]+)", block)
            listed = [x.strip() for x in listed]
            if listed and not any(lp.startswith(c.rstrip("/")) for lp in listed for c in CJK):
                has_narrow_paths = True
                break
        self.assertFalse(
            has_narrow_paths,
            "foundation-validation.yml must not use a narrow `paths:` filter that "
            "would omit the authoritative CJK-table directories (contract §3.4)",
        )


if __name__ == "__main__":
    unittest.main()
