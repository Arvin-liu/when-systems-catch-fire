#!/usr/bin/env python3
"""R2 regression gate for DECISION-INTEGRITY-I1 repair-r1.

Runs this capability's gate tests and the SYMBOLIC-SPHERE predecessor repair
regression. Fail-closed: any failure propagates as a non-zero exit so the
repair train stops rather than publishing a regressed checkpoint.
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULES = [
    "tests.decision.test_decision_integrity_gate",
    "tests.symbolic.test_symbolic_power_perspective_gate",
]


def run(mod):
    r = subprocess.run(
        [sys.executable, "-m", "unittest", mod],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    return r.returncode


def main():
    rc = 0
    for mod in MODULES:
        print(f"\n=== R2 regression: {mod} ===")
        rc |= run(mod)
    if rc != 0:
        print("\nR2 regression FAILED (non-zero exit); repair train must stop.")
    else:
        print("\nR2 regression PASSED: decision capability + SYMBOLIC-SPHERE predecessor green.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
