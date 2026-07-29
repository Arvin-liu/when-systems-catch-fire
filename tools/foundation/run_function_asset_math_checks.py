#!/usr/bin/env python3
"""Scoped SymPy/Python checks for task-99 corrected mathematical assets."""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

import sympy as sp

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data/foundation/function-assets/math-checks.json"
SEED = 990729


def build() -> dict:
    r = sp.symbols("r", positive=True)
    p = sp.symbols("p", real=True)
    g = 1 / sp.log(r)
    derivative = sp.simplify(sp.diff(g, r))
    score = p / (1 - p)
    score_derivative = sp.simplify(sp.diff(score, p))

    mu, lambda_a, lambda_b, lambda_ab = 10.0, 1.0, 1.0, 9.0
    phi_before = 1 / math.log(mu / lambda_a) + 1 / math.log(mu / lambda_b)
    phi_after = 1 / math.log(mu / lambda_ab)

    rng = random.Random(SEED)
    monotone_samples = []
    for _ in range(200):
        left = rng.random() * 0.98
        right = left + rng.random() * (0.99 - left)
        monotone_samples.append((left / (1 - left)) < (right / (1 - right)))

    checks = [
        {"check": "D182 derivative", "pass": derivative == -1 / (r * sp.log(r) ** 2), "result": str(derivative)},
        {"check": "D182 infinity limit", "pass": sp.limit(g, r, sp.oo) == 0, "result": str(sp.limit(g, r, sp.oo))},
        {"check": "D182 pole at one", "pass": sp.denom(g).subs(r, 1) == 0, "result": str(sp.denom(g).subs(r, 1))},
        {"check": "D183 merge-order counterexample", "pass": phi_after > phi_before and math.exp(-phi_after) < math.exp(-phi_before), "phi_before": phi_before, "phi_after": phi_after},
        {"check": "D260 derivative", "pass": score_derivative == 1 / (p - 1) ** 2, "result": str(score_derivative)},
        {"check": "D260 fixed-seed monotonic property", "pass": all(monotone_samples), "sample_count": len(monotone_samples)},
        {"check": "T2 converse zero-divisor counterexample", "pass": (2 * 3) % 6 == 0 and 2 % 6 != 0 and 3 % 6 != 0, "carrier": "Z/6Z"},
    ]
    return {
        "tool": "SymPy and Python standard library",
        "python": sys.version.split()[0],
        "sympy": sp.__version__,
        "random_seed": SEED,
        "scope": "Scoped mathematical properties and counterexamples only; no external physics claim is tested.",
        "checks": checks,
        "checks_total": len(checks),
        "checks_passed": sum(item["pass"] for item in checks),
        "status": "PASS" if all(item["pass"] for item in checks) else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != payload:
            print("FUNCTION_ASSET_MATH_CHECKS_OUT_OF_DATE")
            return 1
    else:
        OUTPUT.write_text(payload, encoding="utf-8")
    result = json.loads(payload)
    print(json.dumps({"checks_total": result["checks_total"], "checks_passed": result["checks_passed"], "status": result["status"]}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
