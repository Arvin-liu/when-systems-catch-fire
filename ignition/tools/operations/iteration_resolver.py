#!/usr/bin/env python3
"""Task 109 resolver — Layer B verification (contract §12).

Run inside a clean checkout (CI provides a fresh clone). Verifies:
  1. Planner determinism: two independent runs produce byte-identical ranked_queue.json.
  2. Adversarial test suite passes (Layer A re-run here for a single gate).
  3. If a FINAL_STATE.json is present, its success token matches the contract and
     resolved_109 == TERMINAL_SUCCESS.

Exits 0 on success, 1 on any failure.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "data/operations/iterations/109"
EXPECTED_TOKEN = "IGNITION_AUTONOMOUS_ITERATION_PLANNER_ESTABLISHED_EVIDENCE_DRIVEN_BACKLOG_GOVERNED_NEXT_SUBSTANTIVE_ITERATION_PROPOSED_109_TERMINALIZED"


def run_planner():
    r = subprocess.run([sys.executable, str(REPO / "tools/iteration_planner/planner.py")],
                       cwd=str(REPO), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"planner failed: {r.stderr}")
    return json.load(open(OUT / "ranked_queue.json"))


def main():
    # 1. determinism: run twice, compare
    a = run_planner()
    b = run_planner()
    if a != b:
        print("FAIL determinism: two planner runs differ")
        return 1
    print("PASS determinism: planner output is reproducible")

    # 2. adversarial suite (Layer A) — run via the test module
    t = subprocess.run([sys.executable, str(REPO / "tests/iteration_planner/test_planner.py")],
                       cwd=str(REPO), capture_output=True, text=True)
    if t.returncode != 0:
        print("FAIL adversarial suite:\n" + t.stdout)
        return 1
    print("PASS adversarial suite (Layer A)")

    # 3. FINAL_STATE presence + token (only meaningful after terminalization artifacts exist)
    fs = OUT / "FINAL_STATE.json"
    if fs.exists():
        d = json.load(open(fs))
        rv = d.get("resolver_verification", {})
        if rv.get("resolved_109") != "TERMINAL_SUCCESS":
            print("FAIL FINAL_STATE resolved_109 != TERMINAL_SUCCESS")
            return 1
        if d.get("success_token") != EXPECTED_TOKEN:
            print("FAIL FINAL_STATE success_token mismatch")
            return 1
        print("PASS FINAL_STATE token + resolved_109")
    else:
        print("NOTE FINAL_STATE.json not yet present (pre-terminalization); determinism + tests passed")

    print("\nresolved_109 = TERMINAL_SUCCESS (layer verification)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
