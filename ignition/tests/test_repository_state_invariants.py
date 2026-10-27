"""Tests for the Line D whole-repository state reconstruction and invariant engine.

Self-contained runner:

    python3 tests/test_repository_state_invariants.py

Runs the deterministic ledger builder, verifies its outputs, runs the global
invariant engine end-to-end against the committed inputs, and exercises the
engine's negative fixtures.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "data" / "operations"

_FAILS = []


def check(name, cond, detail=""):
    if cond:
        print(f"PASS  {name}")
    else:
        print(f"FAIL  {name}  {detail}")
        _FAILS.append(name)


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / script), *args], cwd=ROOT, capture_output=True, text=True)


def main():
    b = run("tools/operations/build_repository_state_ledger.py")
    check("ledger builder exits 0", b.returncode == 0, b.stderr[-300:])
    ledger = json.loads((OPS / "repository-state-ledger.json").read_text(encoding="utf-8"))
    lineage = json.loads((OPS / "candidate-lineage-registry.json").read_text(encoding="utf-8"))
    check("ledger covers 81 open PRs", ledger["counts"]["open_prs"] == 81)
    check("exactly one ACCEPTED_CURRENT iteration", sum(1 for it in ledger["accepted_iterations"] if it["state_category"] == "ACCEPTED_CURRENT") == 1)
    check("accepted iteration chain 104..114 reconstructed", [it["iteration"] for it in ledger["accepted_iterations"]] == list(range(104, 115)))
    check("research branches stay candidate-only", all(r["state_category"] == "RESEARCH_CANDIDATE_NOT_FORMAL_KNOWLEDGE" for r in ledger["research_candidate_not_formal_knowledge"]))
    check("lineage has campaign lines A-D", {c["line"] for c in lineage["campaign_lines"]} == {"A", "B", "C", "D"})
    check("every PR family recommends no-merge", all(f["disposition"].startswith("REMAIN_DRAFT_NO_MERGE") for f in lineage["families"]))

    v = run("tools/operations/validate_global_invariants.py", "--run")
    check("invariant engine exits 0 (closed)", v.returncode == 0, v.stdout[-400:])
    results = json.loads((OPS / "global-invariant-results.json").read_text(encoding="utf-8"))
    check("verdict GLOBAL_INVARIANTS_CLOSED", results["verdict"] == "GLOBAL_INVARIANTS_CLOSED", str(results["failed"]))
    check("11 invariant checks recorded", results["total"] == 11)

    st = run("tools/operations/validate_global_invariants.py", "--self-test")
    check("invariant negative-fixture self-test passes", st.returncode == 0 and "SELF_TEST_OK" in st.stdout, st.stdout[-300:])

    if _FAILS:
        print(f"\n{len(_FAILS)} LINE D TEST(S) FAILED")
        sys.exit(1)
    print("\nALL LINE D STATE-RECONSTRUCTION TESTS PASSED")


if __name__ == "__main__":
    main()
