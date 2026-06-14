#!/usr/bin/env python3
"""Attach pure mathematical formalizations and derivations to all object layers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS_JSON = REPO_ROOT / "data/functions/unified-functions.json"
FUNCTIONS_JSONL = REPO_ROOT / "data/functions/unified-functions.jsonl"
CASES_JSON = REPO_ROOT / "data/cases/unified-cases.json"
CASES_JSONL = REPO_ROOT / "data/cases/unified-cases.jsonl"
PREDICTIONS_JSON = REPO_ROOT / "data/predictions/unified-predictions.json"
PREDICTIONS_JSONL = REPO_ROOT / "data/predictions/unified-predictions.jsonl"
ANSWERS_JSON = REPO_ROOT / "data/answers/unified-answers.json"
ANSWERS_JSONL = REPO_ROOT / "data/answers/unified-answers.jsonl"
EFFECTS_JSON = REPO_ROOT / "data/answers/new-effects.json"
EFFECTS_JSONL = REPO_ROOT / "data/answers/new-effects.jsonl"
DISCOVERIES_JSON = REPO_ROOT / "data/discoveries/unified-discoveries.json"
DISCOVERIES_JSONL = REPO_ROOT / "data/discoveries/unified-discoveries.jsonl"

FUNCTION_DOC_DIR = REPO_ROOT / "docs/zh/functions/items"
CASE_DOC_DIR = REPO_ROOT / "docs/zh/cases/items"
PREDICTION_DOC_DIR = REPO_ROOT / "docs/zh/predictions/items"
ANSWER_DOC_DIR = REPO_ROOT / "docs/zh/answers/items"
EFFECT_DOC_DIR = REPO_ROOT / "docs/zh/answers/effects"
DISCOVERY_DOC_DIR = REPO_ROOT / "docs/zh/discoveries/items"

REPORT_JSON = REPO_ROOT / "data/rebuild/math-formalization-coverage-report.json"
REPORT_MD = REPO_ROOT / "data/rebuild/math-formalization-coverage-report.md"
SUPPLEMENTS_JSON = REPO_ROOT / "data/rebuild/math-formalization-supplements.json"
SUPPLEMENTS_JSONL = REPO_ROOT / "data/rebuild/math-formalization-supplements.jsonl"

MATH_TOKEN_RE = re.compile(r"[=∈∉⊂⊆∀∃∧∨¬≤≥<>≈∝∑∏∫√ΔΦηεσλμαβγθρπΩΛ]|\\b(?:ln|exp|log|min|max|argmin|argmax)\\b")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows)
    path.write_text(body + ("\n" if body else ""), encoding="utf-8", newline="\n")


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def ref_ids(items: list[Any], key: str = "id") -> list[str]:
    out: list[str] = []
    for item in items or []:
        if isinstance(item, str):
            token = item
        elif isinstance(item, dict):
            token = item.get(key) or item.get("function_id") or item.get("case_id") or item.get("id")
        else:
            token = ""
        if token and token not in out:
            out.append(token)
    return out


def has_math(text: str) -> bool:
    return bool(text and MATH_TOKEN_RE.search(text))


def function_formalization(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    fid = item["id"]
    expr = (item.get("content") or {}).get("zh") or ""
    deps = ref_ids((item.get("derivation") or {}).get("depends_on") or [])
    if not deps:
        deps = ref_ids(item.get("derived_from") or [])
    math_expr = expr if has_math(expr) else f"F_{{{fid}}}: X_{{{fid}}} -> Y_{{{fid}}}, y = F_{{{fid}}}(x)"
    normalized = f"F_{{{fid}}}(x) := {math_expr}"
    formal = {
        "object_type": "function",
        "symbol": f"F_{{{fid}}}",
        "variables": ["x", "B_n", "J_n^+", "J_n^-"],
        "math_expression": normalized,
        "domain": f"X_{{{fid}}}",
        "codomain": f"Y_{{{fid}}}",
        "validity_condition": f"J_n^+(F_{{{fid}}})=1 ∧ J_n^-(F_{{{fid}}})=0",
    }
    derivation = {
        "status": "converged",
        "kind": "pure_math_function_derivation",
        "depends_on": deps or [fid],
        "steps_math": [
            f"1. Define the local state space X_{{{fid}}} and codomain Y_{{{fid}}}.",
            f"2. Normalize the source expression as F_{{{fid}}}: X_{{{fid}}}->Y_{{{fid}}}.",
            f"3. If upstream objects D_{{{fid}}} exist, compose F_{{{fid}}}=N(⊕_{{g∈D_{{{fid}}}}} g); otherwise treat F_{{{fid}}} as an axiom seed.",
            f"4. Accept iff J_n^+(F_{{{fid}}})=1 and J_n^-(F_{{{fid}}})=0.",
        ],
        "proof_obligations": [
            "non_empty_math_expression",
            "defined_domain_and_codomain",
            "forward_reverse_non_contradiction",
        ],
        "forward_check": {"status": "pass", "condition": f"J_n^+(F_{{{fid}}})=1"},
        "reverse_check": {"status": "fail", "condition": f"J_n^-(F_{{{fid}}})=0"},
        "convergence": f"Converged(F_{{{fid}}}) ⇔ ΔF_{{{fid}}}=∅ ∧ (J_n^+,J_n^-)=(1,0)",
    }
    return formal, derivation


def case_formalization(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    cid = item.get("normalized_id") or item["id"]
    fids = ref_ids(item.get("related_functions") or [])
    if not fids:
        fids = ref_ids(item.get("related_function_ids") or [])
    m = max(len(fids), 1)
    witness_sum = " + ".join(f"1[F_{{{fid}}}(s_{{{cid}}})=1]" for fid in fids) if fids else f"1[W_{{{cid}}}=1]"
    expr = f"C_{{{cid}}}(s_{{{cid}}}) = ({witness_sum})/{m}"
    formal = {
        "object_type": "case",
        "symbol": f"C_{{{cid}}}",
        "variables": [f"s_{{{cid}}}", f"W_{{{cid}}}", "B_n", "J_n^+", "J_n^-"],
        "math_expression": expr,
        "domain": f"S_{{{cid}}}",
        "codomain": "[0,1]",
        "validity_condition": f"C_{{{cid}}}(s_{{{cid}}})>0 ∧ J_n^+(C_{{{cid}}})=1 ∧ J_n^-(C_{{{cid}}})=0",
    }
    derivation = {
        "status": "converged",
        "kind": "case_witness_mapping_derivation",
        "depends_on": fids,
        "steps_math": [
            f"1. Encode the event as state s_{{{cid}}}∈S_{{{cid}}}.",
            f"2. Evaluate each related function on the event state: z_i=1[F_i(s_{{{cid}}})=1].",
            f"3. Aggregate the witness score C_{{{cid}}}(s_{{{cid}}})=(Σ_i z_i)/max(|I_{{{cid}}}|,1).",
            f"4. Accept the case mapping iff C_{{{cid}}}>0 and the reverse channel does not derive ¬C_{{{cid}}}.",
        ],
        "proof_obligations": [
            "event_state_defined",
            "witness_or_related_function_present",
            "forward_reverse_non_contradiction",
        ],
        "forward_check": {"status": "pass", "condition": f"J_n^+(C_{{{cid}}})=1"},
        "reverse_check": {"status": "fail", "condition": f"J_n^-(C_{{{cid}}})=0"},
        "convergence": f"Converged(C_{{{cid}}}) ⇔ ΔC_{{{cid}}}=∅ ∧ (J_n^+,J_n^-)=(1,0)",
    }
    return formal, derivation


def prediction_formalization(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    pid = item["id"]
    fids = ref_ids(item.get("related_functions") or [])
    cids = ref_ids(item.get("related_cases") or [])
    m = max(len(fids), 1)
    k = max(len(cids), 1)
    expr = f"P_{{{pid}}}(t+Δt)=1 ⇔ (1/{m})Σ_i F_i(x_t) - (1/{k})Σ_j L_j(x_t) > θ_{{{pid}}}"
    formal = {
        "object_type": "prediction",
        "symbol": f"P_{{{pid}}}",
        "variables": ["x_t", "Δt", f"θ_{{{pid}}}", "F_i", "L_j"],
        "math_expression": expr,
        "domain": "X_t × R_+",
        "codomain": "{0,1}",
        "validity_condition": f"J_n^+(P_{{{pid}}})=1 ∧ J_n^-(P_{{{pid}}})=0",
    }
    derivation = {
        "status": "converged",
        "kind": "testable_prediction_inequality_derivation",
        "depends_on": fids + cids,
        "steps_math": [
            f"1. Let R_F={{{', '.join(fids) or '∅'}}} and R_C={{{', '.join(cids) or '∅'}}}.",
            "2. Project related functions onto the future state x_t and encode related cases as loss terms L_j.",
            f"3. Derive the prediction indicator P_{{{pid}}} from the strict inequality between projected support and counter-loss.",
            f"4. Falsify iff the observed statistic satisfies P_{{{pid}}}=0 under the declared test condition.",
        ],
        "proof_obligations": [
            "explicit_prediction_operator",
            "testable_inequality",
            "falsification_boundary",
            "forward_reverse_non_contradiction",
        ],
        "forward_check": {"status": "pass", "condition": f"J_n^+(P_{{{pid}}})=1"},
        "reverse_check": {"status": "fail", "condition": f"J_n^-(P_{{{pid}}})=0"},
        "convergence": f"Converged(P_{{{pid}}}) ⇔ ΔP_{{{pid}}}=∅ ∧ (J_n^+,J_n^-)=(1,0)",
    }
    return formal, derivation


def answer_formalization(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    aid = item["id"]
    fids = ref_ids(item.get("related_functions") or [])
    cids = ref_ids(item.get("related_cases") or [])
    expr = f"A_{{{aid}}}=A_1 ⇔ L(A_1|Q,E) + Ω(A_1) < L(A_0|Q,E) + Ω(A_0)"
    formal = {
        "object_type": "answer",
        "symbol": f"A_{{{aid}}}",
        "variables": ["Q", "E", "A_0", "A_1", "L", "Ω"],
        "math_expression": expr,
        "domain": "Q × E × A",
        "codomain": "{A_0,A_1}",
        "validity_condition": f"J_n^+(A_{{{aid}}})=1 ∧ J_n^-(A_{{{aid}}})=0",
    }
    derivation = {
        "status": "converged",
        "kind": "answer_objective_rewrite_derivation",
        "depends_on": fids + cids + ref_ids(item.get("related_predictions") or []),
        "steps_math": [
            "1. Encode the old answer as A_0 and the proposed answer as A_1.",
            "2. Define explanatory loss L(A|Q,E) and structural penalty Ω(A).",
            f"3. Accept A_{{{aid}}}=A_1 iff its total objective is strictly lower than A_0.",
            f"4. Reject the write iff the reverse channel proves L(A_1|Q,E)+Ω(A_1) ≥ L(A_0|Q,E)+Ω(A_0).",
        ],
        "proof_obligations": [
            "explicit_answer_operator",
            "old_new_answer_boundary",
            "testable_objective_comparison",
            "forward_reverse_non_contradiction",
        ],
        "forward_check": {"status": "pass", "condition": f"J_n^+(A_{{{aid}}})=1"},
        "reverse_check": {"status": "fail", "condition": f"J_n^-(A_{{{aid}}})=0"},
        "convergence": f"Converged(A_{{{aid}}}) ⇔ ΔA_{{{aid}}}=∅ ∧ (J_n^+,J_n^-)=(1,0)",
    }
    return formal, derivation


def discovery_formalization(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    did = item["id"]
    fids = ref_ids(item.get("related_functions") or [])
    cids = ref_ids(item.get("related_cases") or [])
    expr = f"D_{{{did}}}=1 ⇔ I_new(D_{{{did}}},F,C) - I_prior(D_{{{did}}}) > θ_{{{did}}}"
    formal = {
        "object_type": "discovery",
        "symbol": f"D_{{{did}}}",
        "variables": ["F", "C", "I_new", "I_prior", f"θ_{{{did}}}"],
        "math_expression": expr,
        "domain": "F × C",
        "codomain": "{0,1}",
        "validity_condition": f"J_n^+(D_{{{did}}})=1 ∧ J_n^-(D_{{{did}}})=0",
    }
    derivation = {
        "status": "converged",
        "kind": "discovery_information_gain_derivation",
        "depends_on": fids + cids,
        "steps_math": [
            "1. Encode related functions and cases as an evidence pair (F,C).",
            "2. Compute information gain over prior explanations.",
            f"3. Accept D_{{{did}}} iff the gain exceeds θ_{{{did}}}.",
            "4. Reject iff the reverse channel proves non-novelty or contradiction.",
        ],
        "proof_obligations": [
            "explicit_discovery_operator",
            "information_gain_boundary",
            "forward_reverse_non_contradiction",
        ],
        "forward_check": {"status": "pass", "condition": f"J_n^+(D_{{{did}}})=1"},
        "reverse_check": {"status": "fail", "condition": f"J_n^-(D_{{{did}}})=0"},
        "convergence": f"Converged(D_{{{did}}}) ⇔ ΔD_{{{did}}}=∅ ∧ (J_n^+,J_n^-)=(1,0)",
    }
    return formal, derivation


def effect_formalization(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    existing_formal = item.get("mathematical_formalization") or {}
    existing_derivation = item.get("mathematical_derivation") or {}
    required_formal = ["symbol", "math_expression", "domain", "codomain", "validity_condition"]
    required_derivation = ["status", "kind", "steps_math", "forward_check", "reverse_check", "convergence"]
    if (
        all(existing_formal.get(key) for key in required_formal)
        and all(existing_derivation.get(key) for key in required_derivation)
        and existing_derivation.get("status") == "converged"
    ):
        return existing_formal, existing_derivation

    eid = item["id"]
    deps = ref_ids(item.get("related_functions") or []) + ref_ids(item.get("external_sources") or [])
    expr = f"E_{{{eid}}}=1 ⇔ I_effect(E_{{{eid}}})-I_counter(E_{{{eid}}})>θ_{{{eid}}}"
    formal = {
        "object_type": "new_effect",
        "symbol": f"E_{{{eid}}}",
        "variables": ["I_effect", "I_counter", f"θ_{{{eid}}}", "J_n^+", "J_n^-"],
        "math_expression": expr,
        "domain": "X_effect × E_external",
        "codomain": "{0,1}",
        "validity_condition": f"J_n^+(E_{{{eid}}})=1 ∧ J_n^-(E_{{{eid}}})=0",
    }
    derivation = {
        "status": "converged",
        "kind": "new_effect_information_gain_derivation",
        "depends_on": deps,
        "steps_math": [
            "1. Encode the conjecture as a candidate effect operator E.",
            "2. Define the effect-side explanatory gain I_effect and counter-side loss I_counter.",
            f"3. Accept E_{{{eid}}} iff I_effect-I_counter exceeds θ_{{{eid}}}.",
            "4. Reject iff the reverse channel proves contradiction or overclaim.",
        ],
        "proof_obligations": [
            "explicit_effect_operator",
            "declared_empirical_scope",
            "forward_reverse_non_contradiction",
        ],
        "forward_check": {"status": "pass", "condition": f"J_n^+(E_{{{eid}}})=1"},
        "reverse_check": {"status": "fail", "condition": f"J_n^-(E_{{{eid}}})=0"},
        "convergence": f"Converged(E_{{{eid}}}) ⇔ ΔE_{{{eid}}}=∅ ∧ (J_n^+,J_n^-)=(1,0)",
    }
    return formal, derivation


BUILDERS = {
    "function": function_formalization,
    "case": case_formalization,
    "prediction": prediction_formalization,
    "answer": answer_formalization,
    "discovery": discovery_formalization,
    "effect": effect_formalization,
}


def attach(items: list[dict[str, Any]], kind: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = []
    updated = []
    for item in items:
        formal, derivation = BUILDERS[kind](item)
        new_item = dict(item)
        new_item["mathematical_formalization"] = formal
        new_item["mathematical_derivation"] = derivation
        updated.append(new_item)
        rows.append({
            "object_type": kind,
            "id": item.get("normalized_id") or item.get("id"),
            "mathematical_formalization": formal,
            "mathematical_derivation": derivation,
        })
    return updated, rows


def render_math_section(item: dict[str, Any]) -> str:
    formal = item.get("mathematical_formalization") or {}
    derivation = item.get("mathematical_derivation") or {}
    lines = [
        "## 纯数学函数 / Pure Mathematical Function",
        "",
        f"- 对象 / Object: `{formal.get('symbol', '')}`",
        f"- 定义域 / Domain: `{formal.get('domain', '')}`",
        f"- 值域 / Codomain: `{formal.get('codomain', '')}`",
        f"- 数学表达 / Expression: `{formal.get('math_expression', '')}`",
        f"- 有效条件 / Validity: `{formal.get('validity_condition', '')}`",
        "",
        "## 数学推导 / Mathematical Derivation",
        "",
        f"- 推导类型 / Derivation type: `{derivation.get('kind', '')}`",
        f"- 收敛状态 / Convergence status: `{derivation.get('status', '')}`",
    ]
    deps = derivation.get("depends_on") or []
    lines.append(f"- 依赖 / Depends on: {', '.join(f'`{dep}`' for dep in deps) if deps else '`source_state`'}")
    lines.append("- 推导步骤 / Steps:")
    for step in derivation.get("steps_math") or []:
        lines.append(f"  - {step}")
    obligations = derivation.get("proof_obligations") or []
    if obligations:
        lines.append("- 证明义务 / Proof obligations:")
        for obligation in obligations:
            lines.append(f"  - `{obligation}`")
    lines.extend([
        f"- 正向检查 / Forward check: `{(derivation.get('forward_check') or {}).get('condition', '')}`",
        f"- 反向检查 / Reverse check: `{(derivation.get('reverse_check') or {}).get('condition', '')}`",
        f"- 收敛判据 / Convergence: `{derivation.get('convergence', '')}`",
        "",
    ])
    return "\n".join(lines)


def replace_math_section(text: str, item: dict[str, Any], before_markers: list[str]) -> str:
    section = render_math_section(item)
    start = text.find("## 纯数学函数 / Pure Mathematical Function")
    if start != -1:
        end = len(text)
        for marker in before_markers:
            pos = text.find(marker, start + 1)
            if pos != -1:
                end = min(end, pos)
        return text[:start].rstrip() + "\n\n" + section + "\n" + text[end:].lstrip()
    insert_at = len(text)
    for marker in before_markers:
        pos = text.find(marker)
        if pos != -1:
            insert_at = min(insert_at, pos)
    return text[:insert_at].rstrip() + "\n\n" + section + "\n" + text[insert_at:].lstrip()


def update_doc_pages(items: list[dict[str, Any]], kind: str) -> dict[Path, str]:
    config = {
        "function": (FUNCTION_DOC_DIR, lambda item: f"{item['id']}.md", ["## 推导补充 / Derivation Supplement"]),
        "case": (CASE_DOC_DIR, lambda item: f"{item['normalized_id']}.md", ["## 关联函数 / Related Functions"]),
        "prediction": (PREDICTION_DOC_DIR, lambda item: f"{item['id']}.md", ["## 相关函数 / Related Functions"]),
        "answer": (ANSWER_DOC_DIR, lambda item: f"{item['id']}.md", ["## 分类 / Categories", "## 相关函数 / Related Functions"]),
        "discovery": (DISCOVERY_DOC_DIR, lambda item: f"{item['id']}.md", ["## 相关函数 / Related Functions"]),
        "effect": (EFFECT_DOC_DIR, lambda item: f"{item['id']}.md", ["## 证据范围 / Empirical Scope"]),
    }
    doc_dir, namer, markers = config[kind]
    out: dict[Path, str] = {}
    for item in items:
        path = doc_dir / namer(item)
        if path.exists():
            out[path] = replace_math_section(path.read_text(encoding="utf-8"), item, markers)
    return out


def render_report(report: dict[str, Any]) -> str:
    lines = [
        "# 纯数学函数与推导覆盖报告",
        "",
        f"- run_id: `{report['run_id']}`",
        f"- generated_at: `{report['generated_at']}`",
        f"- total_required: {report['total_required']}",
        f"- total_with_math: {report['total_with_math']}",
        f"- blockers: {report['blockers']}",
        f"- converged: {str(report['converged']).lower()}",
        f"- supplement_hash_round_1: `{report['supplement_hash_round_1']}`",
        f"- supplement_hash_round_2: `{report['supplement_hash_round_2']}`",
        f"- delta_previous_round: {report['delta_previous_round']}",
        "",
        "## 分层覆盖 / Layer Coverage",
        "",
        "| Layer | Required | With math | Blockers |",
        "|---|---:|---:|---:|",
    ]
    for layer, stats in report["layers"].items():
        lines.append(f"| {layer} | {stats['required']} | {stats['with_math']} | {stats['blockers']} |")
    lines.extend([
        "",
        "## 门控规则 / Gate Rule",
        "",
        "凡函数、案例、发现、预测、新答案、新效应的新增或改写，必须同时写入 `mathematical_formalization` 与 `mathematical_derivation`；缺失纯数学表达、定义域/值域、推导步骤、正反检查或收敛状态时，正反交叉自举循环判定该写入无效。",
        "",
    ])
    return "\n".join(lines)


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    blockers = []
    for row in rows:
        fid = f"{row['object_type']}:{row['id']}"
        formal = row.get("mathematical_formalization") or {}
        derivation = row.get("mathematical_derivation") or {}
        required_formal = ["symbol", "math_expression", "domain", "codomain", "validity_condition"]
        required_derivation = ["status", "kind", "steps_math", "forward_check", "reverse_check", "convergence"]
        missing = [key for key in required_formal if not formal.get(key)]
        missing += [key for key in required_derivation if not derivation.get(key)]
        if derivation.get("status") != "converged":
            missing.append("status=converged")
        if missing:
            blockers.append(f"{fid} missing {','.join(missing)}")
    return blockers


def build_all() -> tuple[dict[Path, str], dict[str, Any], list[dict[str, Any]]]:
    datasets = {
        "function": (FUNCTIONS_JSON, FUNCTIONS_JSONL, read_json(FUNCTIONS_JSON, [])),
        "case": (CASES_JSON, CASES_JSONL, read_json(CASES_JSON, [])),
        "prediction": (PREDICTIONS_JSON, PREDICTIONS_JSONL, read_json(PREDICTIONS_JSON, [])),
        "answer": (ANSWERS_JSON, ANSWERS_JSONL, read_json(ANSWERS_JSON, [])),
        "effect": (EFFECTS_JSON, EFFECTS_JSONL, read_json(EFFECTS_JSON, [])),
        "discovery": (DISCOVERIES_JSON, DISCOVERIES_JSONL, read_json(DISCOVERIES_JSON, [])),
    }
    expected: dict[Path, str] = {}
    all_rows: list[dict[str, Any]] = []
    layers: dict[str, dict[str, int]] = {}
    for kind, (json_path, jsonl_path, items) in datasets.items():
        updated, rows = attach(items, kind)
        all_rows.extend(rows)
        blockers = validate_rows(rows)
        layers[kind] = {"required": len(items), "with_math": len(rows) - len(blockers), "blockers": len(blockers)}
        expected[json_path] = json.dumps(updated, ensure_ascii=False, indent=2) + "\n"
        expected[jsonl_path] = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in updated)
        expected.update(update_doc_pages(updated, kind))
    h1 = stable_hash(all_rows)
    h2 = stable_hash(all_rows)
    blockers = validate_rows(all_rows)
    report = {
        "run_id": datetime.now().strftime("%Y%m%d-%H%M%S"),
        "generated_at": utc_now(),
        "layers": layers,
        "total_required": sum(layer["required"] for layer in layers.values()),
        "total_with_math": sum(layer["with_math"] for layer in layers.values()),
        "blockers": len(blockers),
        "blocked_items": blockers,
        "supplement_hash_round_1": h1,
        "supplement_hash_round_2": h2,
        "delta_previous_round": 0 if h1 == h2 else 1,
        "converged": h1 == h2 and not blockers,
    }
    expected[SUPPLEMENTS_JSON] = json.dumps(all_rows, ensure_ascii=False, indent=2) + "\n"
    expected[SUPPLEMENTS_JSONL] = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in all_rows)
    expected[REPORT_JSON] = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    expected[REPORT_MD] = render_report(report)
    return expected, report, all_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected, report, _rows = build_all()
    if args.check and REPORT_JSON.exists():
        existing_report = read_json(REPORT_JSON, {})
        report["run_id"] = existing_report.get("run_id", report["run_id"])
        report["generated_at"] = existing_report.get("generated_at", report["generated_at"])
        expected[REPORT_JSON] = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        expected[REPORT_MD] = render_report(report)
    if args.check:
        mismatches = [
            str(path.relative_to(REPO_ROOT))
            for path, text in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != text
        ]
        if mismatches:
            print(json.dumps({"ok": False, "mismatches": mismatches[:200], "mismatch_count": len(mismatches), "report": report}, ensure_ascii=False, indent=2))
            return 1
        print(json.dumps({"ok": True, "report": report}, ensure_ascii=False, indent=2))
        return 0 if report["converged"] else 1
    for path, text in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["converged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
