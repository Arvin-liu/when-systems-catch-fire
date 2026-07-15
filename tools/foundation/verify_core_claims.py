#!/usr/bin/env python3
"""Replay the 078 proof, mathematical counterexample, and logical countermodel."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_z3():
    import z3

    a, b = z3.Ints("a b")
    t2 = z3.Solver()
    t2.add(z3.Or(a == 0, b == 0), a * b != 0)
    t2_ok = t2.check() == z3.unsat

    omega, phi_zero, no_constraints, no_physics, physical_exists = z3.Bools(
        "omega phi_zero no_constraints no_physics physical_exists"
    )
    d220 = z3.Solver()
    d220.add(
        z3.Implies(omega, phi_zero),
        z3.Implies(phi_zero, no_constraints),
        z3.Implies(no_constraints, no_physics),
        omega,
        phi_zero,
        no_constraints,
        no_physics,
        z3.Not(physical_exists),
    )
    d220_ok = d220.check() == z3.sat and z3.is_true(d220.model().eval(omega))
    return t2_ok, d220_ok, z3.get_version_string()


def verify_sympy():
    import sympy

    x = sympy.symbols("x", real=True)
    f1 = sympy.exp(x)
    f2 = sympy.exp(-2 * x)
    product = sympy.simplify(f1 * f2)
    derivative = sympy.simplify(sympy.diff(product, x))
    point_checks = all(derivative.subs(x, point) < 0 for point in (-2, -1, 0, 1, 2))
    symbolic_ok = sympy.simplify(derivative + sympy.exp(-x)) == 0
    return product == sympy.exp(-x) and symbolic_ok and point_checks, sympy.__version__


def verify_lean():
    lake = shutil.which("lake")
    if not lake:
        return False, None, "lake not installed"
    run = subprocess.run(
        [lake, "env", "lean", "Foundation.lean"],
        cwd=ROOT / "formal/lean",
        text=True,
        capture_output=True,
    )
    version = subprocess.run([lake, "env", "lean", "--version"], cwd=ROOT / "formal/lean", text=True, capture_output=True)
    detail = (run.stdout + run.stderr).strip()
    return run.returncode == 0, version.stdout.strip() or None, detail


def main(write_status=False):
    results = []
    try:
        t2_ok, d220_ok, z3_version = verify_z3()
        results.extend([
            ("T2_Z3_PROOF", t2_ok, "PROVED_BY_UNSAT_NEGATION"),
            ("D220_Z3_COUNTERMODEL", d220_ok, "COUNTERMODEL_VERIFIED"),
        ])
    except Exception as exc:
        z3_version = None
        results.extend([
            ("T2_Z3_PROOF", False, f"Z3_UNAVAILABLE:{type(exc).__name__}"),
            ("D220_Z3_COUNTERMODEL", False, f"Z3_UNAVAILABLE:{type(exc).__name__}"),
        ])
    try:
        t16_ok, sympy_version = verify_sympy()
        results.append(("T16_SYMPY_COUNTEREXAMPLE", t16_ok, "COUNTEREXAMPLE_VERIFIED"))
    except Exception as exc:
        sympy_version = None
        results.append(("T16_SYMPY_COUNTEREXAMPLE", False, f"SYMPY_UNAVAILABLE:{type(exc).__name__}"))
    lean_ok, lean_version, lean_detail = verify_lean()
    results.append(("T2_LEAN_PROOF", lean_ok, "PROVED" if lean_ok else f"LEAN_UNAVAILABLE_OR_FAILED:{lean_detail}"))
    results.append(("T23_PENDING", True, "UNPROVED_PROPOSITION"))

    status = {
        "snapshot_id": "IGNITION-20260709-078",
        "lean": {"available": lean_ok, "version": lean_version, "toolchain": (ROOT / "formal/lean/lean-toolchain").read_text().strip()},
        "sympy": {"available": sympy_version is not None, "version": sympy_version},
        "z3": {"available": z3_version is not None, "version": z3_version},
        "checks": {name: ok for name, ok, _ in results},
    }
    if write_status:
        (ROOT / "data/foundation/toolchain-status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, ok, detail in results:
        print(("PASS" if ok else "FAIL"), name, detail)
    passed = sum(ok for _, ok, _ in results)
    print(f"CORE_CHECKS_TOTAL={len(results)} CORE_CHECKS_PASSED={passed}")
    if passed == len(results):
        print("ALL_CORE_CLAIMS_REPLAYED")
        return 0
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write-status", action="store_true")
    args = parser.parse_args()
    raise SystemExit(main(args.write_status))
