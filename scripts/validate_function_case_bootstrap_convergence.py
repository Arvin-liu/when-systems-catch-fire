#!/usr/bin/env python3
"""Validate per-function/per-case bootstrap convergence and math derivations."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS_JSON = ROOT / "data/functions/unified-functions.json"
CASES_JSON = ROOT / "data/cases/unified-cases.json"
DUAL_FUNCTIONS = ROOT / "data/rebuild/dual-channel-function-verification.jsonl"
DUAL_CASES = ROOT / "data/rebuild/dual-channel-case-verification.jsonl"
REPORT_JSON = ROOT / "data/rebuild/function-case-bootstrap-convergence-audit.json"
REPORT_MD = ROOT / "data/rebuild/function-case-bootstrap-convergence-audit.md"

MATH_TOKEN_RE = re.compile(
    r"[=∈∉⊂⊆∀∃∧∨¬≤≥<>≈∝∑∏∫√ΔΦηεσλμαβγθρπΩΛ]"
    r"|\\b(?:ln|exp|log|min|max|argmin|argmax|iff)\\b"
)
BAD_EXPR_RE = re.compile(r"\b(?:TODO|TBD|NaN|null|undefined|PLACEHOLDER)\b", re.IGNORECASE)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def item_id(item: dict[str, Any]) -> str:
    return str(item.get("normalized_id") or item.get("id") or "")


def object_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return " ".join(object_text(value.get(key)) for key in ("zh", "en", "text", "math"))
    if isinstance(value, list):
        return " ".join(object_text(item) for item in value)
    return str(value).strip()


def balanced(text: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for ch in text:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack


def latest_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in sorted(rows, key=lambda item: (item.get("round", 0), item.get("checked_at", ""))):
        latest[str(row.get("id"))] = row
    return latest


def validate_math(kind: str, item: dict[str, Any], valid_function_ids: set[str], valid_case_ids: set[str]) -> list[str]:
    errors: list[str] = []
    iid = item_id(item)
    formal = item.get("mathematical_formalization") or {}
    derivation = item.get("mathematical_derivation") or {}
    expr = object_text(formal.get("math_expression"))

    for key in ("symbol", "math_expression", "domain", "codomain", "validity_condition"):
        if not object_text(formal.get(key)):
            errors.append(f"{kind}:{iid} missing mathematical_formalization.{key}")
    for key in ("status", "kind", "steps_math", "proof_obligations", "forward_check", "reverse_check", "convergence"):
        if not derivation.get(key):
            errors.append(f"{kind}:{iid} missing mathematical_derivation.{key}")

    if derivation.get("status") != "converged":
        errors.append(f"{kind}:{iid} derivation not converged")
    if len(derivation.get("steps_math") or []) < 4:
        errors.append(f"{kind}:{iid} derivation has fewer than 4 steps")
    if len(derivation.get("proof_obligations") or []) < 3:
        errors.append(f"{kind}:{iid} derivation has fewer than 3 proof obligations")
    if (derivation.get("forward_check") or {}).get("status") != "pass":
        errors.append(f"{kind}:{iid} forward_check is not pass")
    if (derivation.get("reverse_check") or {}).get("status") != "fail":
        errors.append(f"{kind}:{iid} reverse_check is not fail")
    if "Converged(" not in object_text(derivation.get("convergence")):
        errors.append(f"{kind}:{iid} convergence predicate missing")

    if not expr:
        errors.append(f"{kind}:{iid} empty math expression")
    elif not MATH_TOKEN_RE.search(expr):
        errors.append(f"{kind}:{iid} math expression has no math/operator token")
    if BAD_EXPR_RE.search(expr):
        errors.append(f"{kind}:{iid} math expression contains unresolved placeholder")
    if not balanced(expr):
        errors.append(f"{kind}:{iid} math expression has unbalanced brackets")

    symbol = object_text(formal.get("symbol"))
    if iid and iid not in symbol:
        errors.append(f"{kind}:{iid} symbol does not contain object id")

    if kind == "function":
        for rel in item.get("related_cases") or []:
            rid = str(rel.get("normalized_id") or rel.get("id") or "")
            if rel.get("found", True) and rid and rid not in valid_case_ids:
                errors.append(f"function:{iid} related case missing: {rid}")
    else:
        for rel in item.get("related_functions") or []:
            rid = str(rel.get("normalized_id") or rel.get("id") or "")
            if rel.get("found", True) and rid and rid not in valid_function_ids:
                errors.append(f"case:{iid} related function missing: {rid}")

    return errors


def validate_dual(kind: str, item: dict[str, Any], dual: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    iid = item_id(item)
    row = dual.get(iid)
    if not row:
        return [f"{kind}:{iid} missing dual-channel verification row"]
    if row.get("result") != "true":
        errors.append(f"{kind}:{iid} dual-channel result is {row.get('result')}")
    if (row.get("forward") or {}).get("status") != "pass":
        errors.append(f"{kind}:{iid} dual-channel forward is not pass")
    if (row.get("reverse") or {}).get("status") != "fail":
        errors.append(f"{kind}:{iid} dual-channel reverse is not fail")
    return errors


def build_report() -> dict[str, Any]:
    functions = [item for item in read_json(FUNCTIONS_JSON, []) if item.get("id") != "MF-0000"]
    cases = read_json(CASES_JSON, [])
    dual_functions = latest_by_id(read_jsonl(DUAL_FUNCTIONS))
    dual_cases = latest_by_id(read_jsonl(DUAL_CASES))
    valid_function_ids = {item_id(item) for item in functions}
    valid_case_ids = {item_id(item) for item in cases}

    errors: list[str] = []
    per_item: list[dict[str, Any]] = []
    for kind, items, dual in (("function", functions, dual_functions), ("case", cases, dual_cases)):
        for item in items:
            iid = item_id(item)
            item_errors = []
            item_errors.extend(validate_dual(kind, item, dual))
            item_errors.extend(validate_math(kind, item, valid_function_ids, valid_case_ids))
            errors.extend(item_errors)
            derivation = item.get("mathematical_derivation") or {}
            per_item.append(
                {
                    "id": iid,
                    "type": kind,
                    "dual_result": (dual.get(iid) or {}).get("result"),
                    "forward": ((dual.get(iid) or {}).get("forward") or {}).get("status"),
                    "reverse": ((dual.get(iid) or {}).get("reverse") or {}).get("status"),
                    "math_status": derivation.get("status"),
                    "step_count": len(derivation.get("steps_math") or []),
                    "proof_obligation_count": len(derivation.get("proof_obligations") or []),
                    "error_count": len(item_errors),
                }
            )

    type_counts = Counter(row["type"] for row in per_item)
    failed = [row for row in per_item if row["error_count"]]
    return {
        "report_name": "function-case-bootstrap-convergence-audit",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "function_total": type_counts["function"],
        "case_total": type_counts["case"],
        "checked_total": len(per_item),
        "dual_function_rows": len(dual_functions),
        "dual_case_rows": len(dual_cases),
        "error_count": len(errors),
        "failed_item_count": len(failed),
        "converged": not errors,
        "gate": {
            "dual_channel_required": "result=true, forward=pass, reverse=fail",
            "math_required": "non-empty expression, balanced brackets, no unresolved placeholders, converged derivation",
            "derivation_required": ">=4 steps, >=3 proof obligations, forward pass, reverse fail",
            "cross_links_required": "all declared found related functions/cases resolve",
        },
        "errors": errors,
        "items": per_item,
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Function-Case Bootstrap Convergence Audit",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- functions checked: {report['function_total']}",
        f"- cases checked: {report['case_total']}",
        f"- total checked: {report['checked_total']}",
        f"- dual function rows: {report['dual_function_rows']}",
        f"- dual case rows: {report['dual_case_rows']}",
        f"- failed items: {report['failed_item_count']}",
        f"- errors: {report['error_count']}",
        f"- converged: {str(report['converged']).lower()}",
        "",
        "## Gate",
        "",
    ]
    for key, value in report["gate"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Failed Items", ""])
    failed = [item for item in report["items"] if item["error_count"]]
    if not failed:
        lines.append("None.")
    else:
        lines.extend(["| id | type | errors | dual | math |", "|---|---|---:|---|---|"])
        for item in failed[:200]:
            lines.append(
                f"| {item['id']} | {item['type']} | {item['error_count']} | "
                f"{item['dual_result']} / {item['forward']} / {item['reverse']} | {item['math_status']} |"
            )
        if len(failed) > 200:
            lines.append(f"| ... | ... | {len(failed) - 200} more | ... | ... |")
    lines.extend(["", "## Error Details", ""])
    if not report["errors"]:
        lines.append("None.")
    else:
        for err in report["errors"][:500]:
            lines.append(f"- {err}")
        if len(report["errors"]) > 500:
            lines.append(f"- ... {len(report['errors']) - 500} more")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate function/case dual-channel convergence and math derivations.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    report = build_report()
    if args.check and REPORT_JSON.exists():
        existing = read_json(REPORT_JSON, {})
        report["generated_at"] = existing.get("generated_at", report["generated_at"])
    expected_json = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    expected_md = render_md(report)

    if args.check:
        mismatches = []
        if not REPORT_JSON.exists() or REPORT_JSON.read_text(encoding="utf-8") != expected_json:
            mismatches.append(str(REPORT_JSON.relative_to(ROOT)))
        if not REPORT_MD.exists() or REPORT_MD.read_text(encoding="utf-8") != expected_md:
            mismatches.append(str(REPORT_MD.relative_to(ROOT)))
        if mismatches:
            print(json.dumps({"ok": False, "mismatches": mismatches, "report": report}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps({"ok": report["converged"], "report": {k: report[k] for k in ("function_total", "case_total", "checked_total", "error_count", "converged")}}, ensure_ascii=False, indent=2))
        return 0 if report["converged"] else 1

    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, expected_md)
    print(json.dumps({k: report[k] for k in ("function_total", "case_total", "checked_total", "error_count", "converged")}, ensure_ascii=False, indent=2))
    return 0 if report["converged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
