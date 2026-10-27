#!/usr/bin/env sage
"""Independent SageMath replay of the scoped task-99 mathematical checks."""
import argparse
import json
from pathlib import Path
from sage.all import RealField, Zmod, diff, infinity, limit, log, var, version

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data/foundation/function-assets/sage-math-checks.json"


def build():
    r = var("r", domain="positive")
    p = var("p", domain="real")
    g = 1 / log(r)
    d_g = diff(g, r)
    score = p / (1 - p)
    d_score = diff(score, p)
    field = RealField(200)
    mu, lambda_a, lambda_b, lambda_ab = map(field, (10, 1, 1, 9))
    phi_before = 1 / log(mu / lambda_a) + 1 / log(mu / lambda_b)
    phi_after = 1 / log(mu / lambda_ab)
    ring = Zmod(6)
    checks = [
        {"check": "D182 derivative", "pass": bool((d_g + 1 / (r * log(r)^2)).simplify_full() == 0), "result": str(d_g)},
        {"check": "D182 infinity limit", "pass": bool(limit(g, r=infinity) == 0), "result": str(limit(g, r=infinity))},
        {"check": "D183 merge-order counterexample", "pass": bool(phi_after > phi_before and (-phi_after).exp() < (-phi_before).exp()), "phi_before": str(phi_before), "phi_after": str(phi_after)},
        {"check": "D260 derivative", "pass": bool((d_score - 1 / (1 - p)^2).simplify_full() == 0), "result": str(d_score)},
        {"check": "T2 converse zero-divisor counterexample", "pass": bool(ring(2) * ring(3) == ring(0) and ring(2) != ring(0) and ring(3) != ring(0)), "carrier": "Z/6Z"},
    ]
    return {
        "tool": "SageMath",
        "sage": version(),
        "scope": "Independent implementation replay of scoped algebra/analysis only; no external physics claim is tested.",
        "checks": checks,
        "checks_total": len(checks),
        "checks_passed": sum(item["pass"] for item in checks),
        "status": "PASS" if all(item["pass"] for item in checks) else "FAIL",
    }


parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
result = build()
payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
if args.check:
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != payload:
        print("SAGE_FUNCTION_ASSET_CHECKS_OUT_OF_DATE")
        raise RuntimeError("SAGE_FUNCTION_ASSET_CHECKS_OUT_OF_DATE")
else:
    OUTPUT.write_text(payload, encoding="utf-8")
print(json.dumps({"checks_total": result["checks_total"], "checks_passed": result["checks_passed"], "status": result["status"]}, sort_keys=True))
if result["status"] != "PASS":
    raise RuntimeError("SAGE_FUNCTION_ASSET_CHECKS_FAILED")
