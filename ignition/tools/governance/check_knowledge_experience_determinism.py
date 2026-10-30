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
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BKE_PATH = ROOT / "tools/governance/build_knowledge_experience.py"
LEDGER = ROOT / "data/governance/human-results/result-ledger.jsonl"
FIRST_SEEN_PATH = ROOT / "data/governance/knowledge-experience/source-first-seen.json"
MANIFEST_PATH = ROOT / "data/governance/knowledge-experience/manifest.json"


def fail(msg: str) -> int:
    print("REGRESSION_FAIL: " + msg, file=sys.stderr)
    return 1


def hash_outputs() -> dict[str, str]:
    """Hash the exact output set declared by the just-completed generator pass.

    The generated manifest enumerates every output except itself. Checking its
    entries against the files on disk preserves complete output coverage while
    avoiding a separate, redundant in-process build just to discover paths.
    """
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    declared = manifest.get("generated_outputs")
    if not isinstance(declared, dict) or not declared:
        raise ValueError("manifest has no generated_outputs mapping")

    hashes: dict[str, str] = {}
    for relative, expected in sorted(declared.items()):
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"manifest contains unsafe output path: {relative}")
        path = ROOT / relative_path
        if not path.is_file():
            raise ValueError(f"generator did not create declared output: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"generated output does not match its manifest digest: {relative}")
        hashes[relative_path.as_posix()] = actual

    manifest_relative = MANIFEST_PATH.relative_to(ROOT).as_posix()
    hashes[manifest_relative] = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    return hashes


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
    # Each generator invocation performs the complete build and schema
    # validation. Use its manifest to enumerate outputs instead of doing an
    # additional in-process build solely to obtain the same output paths.
    def run_generator() -> int:
        proc = subprocess.run([sys.executable, str(BKE_PATH)], cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            print(proc.stdout, file=sys.stderr)
            print(proc.stderr, file=sys.stderr)
        return proc.returncode

    if run_generator() != 0:
        return fail("generator failed on first pass")
    try:
        hashes_a = hash_outputs()
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return fail(f"first-pass output inventory invalid: {exc}")
    if run_generator() != 0:
        return fail("generator failed on second pass")
    try:
        hashes_b = hash_outputs()
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return fail(f"second-pass output inventory invalid: {exc}")
    if hashes_a != hashes_b:
        diffs = sorted(path for path in hashes_a.keys() | hashes_b.keys() if hashes_a.get(path) != hashes_b.get(path))
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
