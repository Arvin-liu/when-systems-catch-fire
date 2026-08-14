#!/usr/bin/env python3
"""Regression check (task 102): full clone and shallow clone must not produce
different formal knowledge-experience results.

Root cause fixed here: ``build_knowledge_experience.py::source_date`` used to shell
out to ``git log`` for each result source's first-appearance date and fell back to
the snapshot date on a shallow clone. That made a shallow clone emit different
(``snapshot``) dates than a full clone, which broke CI drift checks.

The fix bakes ``first_seen_date`` into the governed
``data/governance/knowledge-experience/source-first-seen.json`` and makes
``source_date`` read it (no git, fail-hard if unregistered). This check enforces
that guarantee so it cannot regress:

  1. The governed map exists and covers every ``source`` in the result ledger, so the
     runtime git fallback path can never be taken (clone-depth independent by construction).
  2. ``build_knowledge_experience.py`` no longer contains a ``git log`` call for dates.
  3. Running the generator twice consecutively yields byte-identical output (two-pass
     determinism), and ``--check`` confirms it matches the committed output.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BKE_PATH = ROOT / "tools/governance/build_knowledge_experience.py"
LEDGER = ROOT / "data/governance/human-results/result-ledger.jsonl"
FIRST_SEEN_PATH = ROOT / "data/governance/knowledge-experience/source-first-seen.json"


def fail(msg: str) -> int:
    print("REGRESSION_FAIL: " + msg, file=sys.stderr)
    return 1


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hash_outputs(paths: list[Path]) -> dict[str, str]:
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def main() -> int:
    # --- 1. governed map covers every ledger source -------------------------------
    if not FIRST_SEEN_PATH.is_file():
        return fail(f"missing governed map: {FIRST_SEEN_PATH.relative_to(ROOT)}")
    map_data = json.loads(FIRST_SEEN_PATH.read_text(encoding="utf-8"))
    entries = map_data.get("entries", {})
    ledger = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    sources = sorted({row["source"] for row in ledger})
    missing = [s for s in sources if s not in entries]
    if missing:
        return fail("source-first-seen.json does not cover all ledger sources: " + ", ".join(missing[:20]))
    if map_data.get("history_requirement") != "FULL":
        return fail("source-first-seen.json must be computed from FULL history")

    # --- 2. generator no longer shells out to git for dates -----------------------
    src = BKE_PATH.read_text(encoding="utf-8")
    if "git log" in src:
        return fail("build_knowledge_experience.py still contains a `git log` call (clone dependence)")
    if "source-first-seen.json" not in src:
        return fail("build_knowledge_experience.py does not reference the governed first-seen map")

    # --- 3. two-pass determinism + match to committed ----------------------------
    bke = load_module("bke_check", BKE_PATH)
    config = json.loads(bke.CONFIG_PATH.read_text(encoding="utf-8"))
    data = bke.build(config)
    bke.validate_data(data, config)
    products = bke.output_map(data, config)
    paths = sorted(products.keys(), key=lambda p: str(p))

    def run_generator() -> int:
        proc = subprocess.run([sys.executable, str(BKE_PATH)], cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            print(proc.stdout, file=sys.stderr)
            print(proc.stderr, file=sys.stderr)
        return proc.returncode

    if run_generator() != 0:
        return fail("generator failed on first pass")
    hashes_a = hash_outputs(paths)
    if run_generator() != 0:
        return fail("generator failed on second pass")
    hashes_b = hash_outputs(paths)
    if hashes_a != hashes_b:
        diffs = [str(p) for p in paths if hashes_a.get(str(p)) != hashes_b.get(str(p))]
        return fail("two-pass non-determinism: " + ", ".join(diffs[:20]))

    # confirm regenerated output matches the committed output
    check = subprocess.run([sys.executable, str(BKE_PATH), "--check"], cwd=ROOT, capture_output=True, text=True)
    if check.returncode != 0:
        print(check.stdout, file=sys.stderr)
        print(check.stderr, file=sys.stderr)
        return fail("regenerated output drifts from committed (--check failed)")

    print(
        f"KNOWLEDGE_EXPERIENCE_DETERMINISM_OK sources={len(sources)} "
        f"map_entries={len(entries)} outputs={len(paths)} two_pass=identical"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
