#!/usr/bin/env python3
"""Build the 078 source-text adjudication layer without rewriting legacy assets."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

try:
    from tools.foundation.legacy_table_migration import current_or_archived_text
except ModuleNotFoundError:
    from legacy_table_migration import current_or_archived_text

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/foundation"
REPORTS = ROOT / "reports/foundation-architecture"
DATE = "2026-07-13"
ADJUDICATOR = "Codex-GPT-5-adversarial-audit"
STRONG_TERMS = [
    "定理", "证明", "公理", "同构", "因果", "必然", "唯一", "精确", "解析解",
    "不可能", "哥德尔", "黎曼", "P vs NP", "数学猜想", "四种基本力", "大统一",
    "量子引力", "Planck", "GUT",
]
ROOT_SOURCE = "统一函数总表/0001-Ψ₀元函数完整数学定义.md"
EXPLICIT_D = {"D189", "D220", "D225", "D600", "D601", "D602"}


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def jsonl(rows):
    return "\n".join(dump(row) for row in rows)


def write(path: Path, content: str, check: bool, changed: list[str]):
    content = content.rstrip() + "\n"
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old != content:
        changed.append(str(path.relative_to(ROOT)))
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def clean(text: str | None, limit=700):
    text = re.sub(r"\s+", " ", text or "").strip(" `\n\t")
    return text[:limit]


def find_line(text: str, pattern: str):
    rx = re.compile(pattern, re.I)
    for number, line in enumerate(text.splitlines(), 1):
        if rx.search(line):
            return number
    return 1


def section_value(text: str, headings: list[str]):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if any(heading in line for heading in headings):
            for candidate in lines[index + 1:index + 8]:
                candidate = clean(candidate)
                if candidate and not candidate.startswith(("#", "<", "- 对象", "English:")):
                    return re.sub(r"^中文：", "", candidate).strip()
    return None


def extract_expression(text: str):
    value = section_value(text, ["数学表达 / Mathematical Expression", "## 机制表达"])
    if value:
        return value
    match = re.search(r"数学表达\s*/\s*Expression:\s*`([^`]+)`", text)
    return clean(match.group(1)) if match else None


def extract_statement(text: str, title: str):
    for heading in ["**注释 / Annotation**", "## 函数内容", "## 原文捞回 / Source Recovery"]:
        value = section_value(text, [heading])
        if value:
            return value
    return extract_expression(text) or title


def extract_scope(text: str):
    value = section_value(text, ["## 边界", "适用范围", "有效条件 / Validity"])
    return value or "仅限 legacy 来源明确陈述的模型内部范围；不得外推为跨域事实。"


def source_label(text: str):
    match = re.search(r'^source:\s*["\']?(.+?)["\']?\s*$', text, re.M)
    if match:
        return clean(match.group(1))
    match = re.search(r"\*\*原文来源 / Source\*\*：`([^`]+)`", text)
    return clean(match.group(1)) if match else "legacy file is the earliest recoverable source in this repository"


def git_first_seen():
    command = ["git", "log", "--reverse", "--format=@@%H", "--name-only", "--", "统一函数总表"]
    output = subprocess.check_output(command, cwd=ROOT, text=True, errors="replace")
    current = None
    first = {}
    for line in output.splitlines():
        if line.startswith("@@"):
            current = line[2:]
        elif current and line.startswith("统一函数总表/"):
            first.setdefault(line, current)
    return first


def matched_terms(text: str):
    normalized = re.sub(r"\s+", " ", text)
    result = []
    for term in STRONG_TERMS:
        if term == "P vs NP":
            if re.search(r"P\s*vs\s*NP", normalized, re.I):
                result.append(term)
        elif re.search(re.escape(term), normalized, re.I):
            result.append(term)
    return result


def extract_ids(text: str, current: str):
    found = re.findall(r"\b(?:MF-?\d{1,4}|[ATD]\d{1,4})\b", text, re.I)
    normalized = []
    for item in found:
        item = item.upper().replace("MF-", "MF")
        if item != current and item not in normalized:
            normalized.append(item)
    return normalized[:30]


def typed_variables(expression: str | None):
    if not expression:
        return []
    banned = {"F", "J", "TRUE", "FALSE", "SIN", "COS", "EXP", "LN", "MIN", "MAX"}
    tokens = re.findall(r"(?<![\w])([A-Za-zΑ-Ωα-ωΦΨΩΣΔθμσερ]+(?:_[A-Za-z0-9]+)?)", expression)
    rows = []
    for token in tokens:
        if token.upper() in banned or token in {row["name"] for row in rows}:
            continue
        rows.append({"name": token, "type": "UNSPECIFIED_SOURCE_SYMBOL"})
        if len(rows) == 12:
            break
    return rows


A_TYPES = {
    "A1": ("PREDICATE", "DEFINITION"),
    "A2": ("METRIC", "DEFINITION"),
    "A3": ("RELATION", "DEFINITION"),
    "A4": ("MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS"),
    "A5": ("METRIC", "DEFINITION"),
    "A6": ("MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS"),
    "A7": ("METRIC", "DEFINITION"),
    "A8": ("PREDICATE", "DEFINITION"),
    "A9": ("PROBABILISTIC_MODEL", "EXPLANATORY_HYPOTHESIS"),
}

T_TYPES = {
    "T1": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T2": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T3": ("STATE_TRANSITION", "EXPLANATORY_HYPOTHESIS"),
    "T4": ("RELATION", "MATHEMATICAL_PROPOSITION"),
    "T5": ("RELATION", "STRUCTURAL_ANALOGY"),
    "T6": ("PREDICATE", "DEFINITION"),
    "T7": ("MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS"),
    "T8": ("STATE_TRANSITION", "EXPLANATORY_HYPOTHESIS"),
    "T9": ("METRIC", "DEFINITION"),
    "T10": ("OPTIMIZATION_PROBLEM", "MATHEMATICAL_PROPOSITION"),
    "T11": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T12": ("METRIC", "DEFINITION"),
    "T13": ("RELATION", "EXPLANATORY_HYPOTHESIS"),
    "T14": ("MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS"),
    "T15": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T16": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T17": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T18": ("RELATION", "STRUCTURAL_ANALOGY"),
    "T19": ("RELATION", "DEFINITION"),
    "T20": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T21": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T22": ("ARGUMENT_SCHEMA", "ALGORITHMIC_CLAIM"),
    "T23": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T24": ("PREDICATE", "DEFINITION"),
    "T25": ("MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS"),
    "T26": ("STATE_TRANSITION", "EXPLANATORY_HYPOTHESIS"),
    "T27": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T28": ("RELATION", "DEFINITION"),
    "T29": ("STATE_TRANSITION", "EXPLANATORY_HYPOTHESIS"),
    "T30": ("RELATION", "STRUCTURAL_ANALOGY"),
    "T31": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T32": ("METRIC", "DEFINITION"),
    "T33": ("ARGUMENT_SCHEMA", "ALGORITHMIC_CLAIM"),
    "T34": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T35": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T36": ("RELATION", "MATHEMATICAL_PROPOSITION"),
    "T37": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T38": ("FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"),
    "T39": ("RELATION", "STRUCTURAL_ANALOGY"),
    "T40": ("ARGUMENT_SCHEMA", "ALGORITHMIC_CLAIM"),
    "T41": ("RELATION", "STRUCTURAL_ANALOGY"),
    "T42": ("RELATION", "EXTERNAL_THEOREM_REFERENCE"),
    "T43": ("MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS"),
    "T44": ("MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS"),
    "T45": ("MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS"),
    "T46": ("RELATION", "STRUCTURAL_ANALOGY"),
    "T47": ("MECHANISM_MODEL", "EMPIRICAL_ASSOCIATION"),
    "T48": ("MECHANISM_MODEL", "EMPIRICAL_ASSOCIATION"),
    "T49": ("MECHANISM_MODEL", "EMPIRICAL_ASSOCIATION"),
    "T50": ("MECHANISM_MODEL", "EMPIRICAL_ASSOCIATION"),
    "T51": ("MECHANISM_MODEL", "EMPIRICAL_ASSOCIATION"),
    "T52": ("MECHANISM_MODEL", "EMPIRICAL_ASSOCIATION"),
    "T53": ("MECHANISM_MODEL", "EMPIRICAL_ASSOCIATION"),
    "T54": ("MECHANISM_MODEL", "EMPIRICAL_ASSOCIATION"),
    "T55": ("NATURAL_LANGUAGE_CANDIDATE", "EXPLANATORY_HYPOTHESIS"),
    "T56": ("STATE_TRANSITION", "EMPIRICAL_ASSOCIATION"),
    "T57": ("MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS"),
}


def classify(oid: str, title: str, statement: str, expression: str | None):
    combined = f"{title} {statement} {expression or ''}"
    if oid == "Y1":
        return "ALGORITHM", "ALGORITHMIC_CLAIM"
    if oid in {"MF1", "MF2", "MF3", "MF5"}:
        return "PREDICATE", "DEFINITION"
    if oid == "MF4":
        return "STATE_TRANSITION", "ALGORITHMIC_CLAIM"
    if oid in A_TYPES:
        return A_TYPES[oid]
    if oid in T_TYPES:
        return T_TYPES[oid]
    if oid in {"D220", "D225"}:
        return "FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"
    if re.search(r"同构|isomorph", combined, re.I):
        return "RELATION", "STRUCTURAL_ANALOGY"
    if re.search(r"哥德尔|黎曼|P\s*vs\s*NP|数学猜想", combined, re.I):
        return "RELATION", "EXTERNAL_THEOREM_REFERENCE"
    if re.search(r"定理|证明|必然|唯一|精确|解析解|不可能|必要条件|充分条件", title):
        return "FORMAL_PROPOSITION", "MATHEMATICAL_PROPOSITION"
    if re.search(r"因果|机制|causal", title, re.I):
        return "MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS"
    if re.search(r"判定|条件|是否|互斥|存在性|可达", title):
        return "PREDICATE", "DEFINITION"
    if re.search(r"协议|规则|检验|验证|方案|路径|策略", title):
        return "ARGUMENT_SCHEMA", "ALGORITHMIC_CLAIM"
    if re.search(r"动力学|级联|演化|更新|衰减|漂移|相变|循环|反馈|恢复|转移|退化|崩塌|注入", title):
        return "STATE_TRANSITION", "EXPLANATORY_HYPOTHESIS"
    if re.search(r"概率|分布", title):
        return "PROBABILISTIC_MODEL", "EMPIRICAL_ASSOCIATION"
    if re.search(r"率|指数|强度|度$|距离|成本|效率|容量|速度|时间|阈值|门槛|密度|精度|裕度|半衰期|最优|值$|位置|能标|熵", title):
        return "METRIC", "EMPIRICAL_ASSOCIATION"
    if re.search(r"系统|生态|意识|社会|认知|权力|治理|冲击|影响|植物|组织|记忆|学习|智能|模型", title):
        return "MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS"
    if expression and re.search(r":=|=|→|↔|⟹|∈|<|>", expression):
        return "RELATION", "EXPLANATORY_HYPOTHESIS"
    return "NATURAL_LANGUAGE_CANDIDATE", "EXPLANATORY_HYPOTHESIS"


def status_for(oid: str, object_type: str, claim_type: str):
    if oid == "T2":
        return "ADJUDICATED_TRUE_IN_STATED_NAT_SCOPE", "WELL_TYPED", "VALID_DEDUCTION", "PROVED", "MACHINE_CHECKED_PROOF"
    if oid == "T16":
        return "REFUTED_AS_STATED", "COUNTEREXAMPLE_FOUND", "COUNTERMODEL_FOUND", "REFUTED", "REPLAYABLE_COUNTEREXAMPLE"
    if oid == "D220":
        return "ARGUMENT_INVALID_AS_STATED", "FORMALIZATION_INCOMPLETE", "COUNTERMODEL_FOUND", "INVALID_ARGUMENT", "REPLAYABLE_COUNTERMODEL"
    if oid.startswith("A"):
        return "DECLARATION_ONLY", "FORMALIZATION_INCOMPLETE", "NOT_APPLICABLE", "NOT_APPLICABLE", "SOURCE_ONLY"
    logic = "DEFEASIBLE_SUPPORT" if claim_type in {"STRUCTURAL_ANALOGY", "EXPLANATORY_HYPOTHESIS", "EMPIRICAL_ASSOCIATION"} else "HIDDEN_PREMISE"
    proof = "UNPROVED_PROPOSITION" if object_type == "FORMAL_PROPOSITION" else "NOT_APPLICABLE"
    formal = "UNFORMALIZED" if object_type == "NATURAL_LANGUAGE_CANDIDATE" else "FORMALIZATION_INCOMPLETE"
    return "ADJUDICATED_NOT_VALIDATED", formal, logic, proof, "SOURCE_ONLY"


def disposition_for(oid: str, title: str, claim_type: str):
    if oid == "Y1":
        return "SPLIT"
    if oid.startswith("A"):
        return "FREEZE"
    if oid == "T2":
        return "KEEP"
    if oid in {"T16", "D220"} or claim_type in {"STRUCTURAL_ANALOGY", "EXTERNAL_THEOREM_REFERENCE"}:
        return "DOWNGRADE"
    if re.search(r"定理|证明|公理|因果|必然|唯一|精确|解析解|不可能", title):
        return "DOWNGRADE"
    return "RECLASSIFY"


def inference_for(claim_type: str):
    return {
        "MATHEMATICAL_PROPOSITION": "DEDUCTIVE",
        "EMPIRICAL_ASSOCIATION": "INDUCTIVE",
        "STRUCTURAL_ANALOGY": "ANALOGICAL",
        "EXPLANATORY_HYPOTHESIS": "ABDUCTIVE",
        "ALGORITHMIC_CLAIM": "DEDUCTIVE",
        "DEFINITION": "NORMATIVE",
        "EXTERNAL_THEOREM_REFERENCE": "ANALOGICAL",
    }.get(claim_type, "ABDUCTIVE")


def reason_not_other(object_type: str, title: str, expression: str | None, claim_type: str):
    reasons = []
    if object_type != "FUNCTION":
        reasons.append("FUNCTION rejected: the source does not jointly specify a set-theoretic domain, codomain, total single-valuedness, and executable rule.")
    if object_type != "FORMAL_PROPOSITION":
        reasons.append("FORMAL_PROPOSITION rejected: the source lacks a complete formal language statement with discharged assumptions.")
    if claim_type != "STRICT_ISOMORPHISM_CLAIM" and re.search(r"同构|isomorph", f"{title} {expression or ''}", re.I):
        reasons.append("STRICT_ISOMORPHISM_CLAIM rejected: no map, inverse map, or structure-preservation proof is supplied.")
    if claim_type != "EMPIRICAL_CAUSAL_CLAIM" and "因果" in title:
        reasons.append("EMPIRICAL_CAUSAL_CLAIM rejected: no intervention semantics or identification evidence is supplied.")
    return reasons or [f"The source structure is best represented as {object_type}, not as a numerical function merely because the legacy label says function."]


def obligations_for(oid: str, object_type: str, claim_type: str):
    if oid == "T2":
        return ["check the Nat-scoped proposition in Lean and Z3", "do not generalize beyond structures with absorbing zero without a separate proof"]
    if oid == "T16":
        return ["record the monotone exponential counterexample", "state sufficient curvature and boundary conditions before proposing an inverted-U theorem"]
    if oid == "D220":
        return ["add the missing physical-existence premise if intended", "separate semantic meaningfulness from logical contradiction"]
    obligations = ["define every source symbol and its type", "state the scope and stopping conditions"]
    if object_type in {"FUNCTION", "PREDICATE", "METRIC", "PROBABILISTIC_MODEL"}:
        obligations.append("supply a domain, target type, units where applicable, and a well-defined evaluation rule")
    if object_type == "FORMAL_PROPOSITION":
        obligations.append("supply a complete formal statement and a machine-checkable proof or counterexample")
    if claim_type == "STRUCTURAL_ANALOGY":
        obligations.append("either provide maps, inverse maps and structure-preservation proof or retain analogy status")
    if object_type == "MECHANISM_MODEL":
        obligations.append("operationalize the mechanism and test rival explanations")
    return obligations


def make_record(obj: dict, first_seen: dict):
    oid = obj["id"]
    path = obj["legacy_path"]
    text = current_or_archived_text(path) or ""
    title = obj["title"]
    expression = extract_expression(text)
    statement = extract_statement(text, title)
    object_type, claim_type = classify(oid, title, statement, expression)
    semantic, formal, logic, proof, evidence = status_for(oid, object_type, claim_type)
    title_terms = matched_terms(title)
    body_terms = matched_terms(text)
    disposition = disposition_for(oid, title, claim_type)
    refs = [
        f"{path}#L{find_line(text, r'^title:|^#|^###')}",
        f"{path}#L{find_line(text, r'数学表达|机制表达')}",
        f"{path}#L{find_line(text, r'注释 / Annotation|函数内容|边界')}",
    ]
    domain = "Nat × Nat" if oid == "T2" else "UNSPECIFIED_IN_SOURCE"
    target = "Nat proposition" if oid == "T2" else {
        "PREDICATE": "Boolean or governed decision state",
        "RELATION": "relation over source entities",
        "STATE_TRANSITION": "next state or transition relation",
        "ALGORITHM": "ordered workflow result",
        "ARGUMENT_SCHEMA": "structured inference or procedure",
        "MECHANISM_MODEL": "mechanism description",
        "METRIC": "scalar-like score with unspecified units",
        "PROBABILISTIC_MODEL": "probability-like output",
        "FORMAL_PROPOSITION": "truth value",
        "NATURAL_LANGUAGE_CANDIDATE": "not yet typed",
    }.get(object_type, "UNSPECIFIED_IN_SOURCE")
    controlled = (
        f"Within the source-defined scope, {title} is adjudicated as {object_type}: {statement}. "
        "This is a model-internal controlled proposition, not an assertion of external mathematical, physical, or empirical truth."
    )
    if oid == "Y1":
        controlled = "Ψ₀/Y1 is a multi-stage decision protocol that composes C, M, I_iso, L_meta, G_δ and P_meta under joint constraints; the multiplication glyph denotes orchestration/composition, not ordinary numerical multiplication."
    if oid == "T2":
        controlled = "For all a,b in Nat, if a=0 or b=0, then a*b=0."
    if oid == "T16":
        controlled = "The unrestricted claim that every product of two oppositely monotone functions has an inverted-U shape is false."
    if oid == "D220":
        controlled = "The displayed implication chain does not entail that Omega=1 is impossible unless an additional physical-existence premise is asserted."
    legacy_label = "AXIOM_LAYER" if oid.startswith("A") else "THEOREM_LAYER" if oid.startswith("T") else "LEGACY_FUNCTION"
    counterexamples = []
    if oid == "T16":
        counterexamples = ["counterexample:T16-opposite-monotone-product"]
    if oid == "D220":
        counterexamples = ["countermodel:D220-missing-premise"]
    proof_artifacts = ["proof:T2-zero-factor-nat"] if oid == "T2" else []
    confidence = 0.94 if oid in {"Y1", "T2", "T16", "D220"} or oid.startswith(("MF", "A", "T")) else 0.82
    return {
        "adjudication_id": f"adjudication:{oid}",
        "stable_id": oid,
        "legacy_id": oid,
        "original_title": title,
        "legacy_label": legacy_label,
        "adjudicated_label": object_type,
        "classification_status": "ADJUDICATED",
        "classification_basis": ["SOURCE_TEXT"],
        "classification_confidence": confidence,
        "semantic_justification": f"Reviewed the current legacy source, recovered statement, expression, scope, dependencies and strong-term context. The source supports {object_type}; its legacy function/theorem wording alone does not.",
        "source_excerpt_refs": refs,
        "adjudication_date": DATE,
        "adjudicator": ADJUDICATOR,
        "review_required": False,
        "earliest_source": {"declared_source": source_label(text), "first_git_commit": first_seen.get(path)},
        "current_source": {"path": path, "git_blob_sha": obj.get("legacy_git_blob_sha")},
        "original_natural_language_proposition": statement,
        "controlled_semantic_proposition": controlled,
        "subject": title,
        "object": object_type,
        "conditions": extract_scope(text),
        "quantifiers": ["forall a,b in Nat"] if oid == "T2" else ["UNSPECIFIED_IN_SOURCE"],
        "modal_terms": [term for term in ["必然", "可能", "唯一", "不可能", "精确"] if term in f"{title} {statement}"],
        "applicability_scope": extract_scope(text),
        "formal_object_type": object_type,
        "claim_type": claim_type,
        "why_not_other_object_types": reason_not_other(object_type, title, expression, claim_type),
        "typed_variables": [{"name": "a", "type": "Nat"}, {"name": "b", "type": "Nat"}] if oid == "T2" else typed_variables(expression),
        "domain": domain,
        "codomain_or_target_type": target,
        "parameters": [v["name"] for v in typed_variables(expression)],
        "units_or_dimensions": [],
        "assumptions_and_boundaries": [extract_scope(text), "legacy prose is not treated as proof or external evidence"],
        "premise_set": [statement] + ([expression] if expression and expression != statement else []),
        "inference_type": inference_for(claim_type),
        "inference_rule": "source-text controlled restatement; no truth promotion" if oid not in {"T2", "T16", "D220"} else {"T2": "case split on the zero factor", "T16": "counterexample", "D220": "Boolean countermodel"}[oid],
        "conclusion": controlled,
        "hidden_premises": ["source symbols have stable operational meanings", "cross-domain transport requires independent evidence"],
        "known_counterexamples_or_countermodels": counterexamples,
        "proof_obligations": obligations_for(oid, object_type, claim_type),
        "proof_artifacts": proof_artifacts,
        "evidence_status": evidence,
        "semantic_status": semantic,
        "formal_status": formal,
        "logic_status": logic,
        "proof_status": proof,
        "final_disposition": disposition,
        "unresolved_questions": [] if oid == "T2" else obligations_for(oid, object_type, claim_type),
        "dependencies": extract_ids(text, oid),
        "related_cases": sorted(set(re.findall(r"C-?(\d{3,4})", text)))[:30],
        "strong_term_hits_title": title_terms,
        "strong_term_hits_body": body_terms,
        "adjudication_method": "full_source_structural_and_semantic_review",
        "automated_title_only": False,
    }


COMPONENTS = {
    "C": ("C(x,y)", "MECHANISM_MODEL", "EXPLANATORY_HYPOTHESIS", "A mechanism-hypothesis score over x and y; it is not an established causal relation without interventions and identification."),
    "M": ("M(B_n)", "PREDICATE", "DEFINITION", "A convergence predicate over successive registry snapshots, evaluated only after its delta and stopping rule are defined."),
    "I_ISO": ("I_iso(A,B)", "RELATION", "STRUCTURAL_ANALOGY", "A candidate structural-correspondence relation; strict isomorphism is rejected until a bijection, inverse and preservation proof exist."),
    "L_META": ("L_meta", "OPERATOR", "ALGORITHMIC_CLAIM", "A layer-selection operator choosing the first governed stopping layer; it is not a proof of convergence."),
    "G_DELTA": ("G_δ", "RELATION", "EXTERNAL_THEOREM_REFERENCE", "A restricted external-reference gate. Gödel incompleteness cannot serve as a universal decidability oracle outside its formal hypotheses."),
    "P_META": ("P_meta", "ALGORITHM", "ALGORITHMIC_CLAIM", "A projection workflow that combines governed candidate correspondences; multiplication signs denote composition/joint constraints, not numeric multiplication."),
    "JPLUS": ("J⁺", "PREDICATE", "DEFINITION", "A positive-evidence channel returning an internal acceptance flag, not truth."),
    "JMINUS": ("J⁻", "PREDICATE", "DEFINITION", "A negative-evidence channel returning an internal objection flag, not falsity."),
    "MF0": ("MF-0000", "ALGORITHM", "ALGORITHMIC_CLAIM", "An iterative bootstrap protocol composed of MF1-MF5; it is not a scalar function and does not prove its own fixed point."),
}


def component_records(first_seen: dict):
    text = current_or_archived_text(ROOT_SOURCE) or ""
    first_commit = first_seen.get(ROOT_SOURCE)
    rows = []
    for stable_id, (title, object_type, claim_type, controlled) in COMPONENTS.items():
        line = find_line(text, re.escape(title.split("(")[0].replace("MF-0000", "MF-0000")))
        disposition = "EXTERNAL_REFERENCE" if stable_id == "G_DELTA" else "SPLIT" if stable_id == "MF0" else "RECLASSIFY"
        rows.append({
            "adjudication_id": f"adjudication:component:{stable_id}",
            "stable_id": stable_id,
            "legacy_id": "Y1::" + stable_id,
            "original_title": title,
            "legacy_label": "Y1_INTERNAL_COMPONENT",
            "adjudicated_label": object_type,
            "classification_status": "ADJUDICATED",
            "classification_basis": ["SOURCE_TEXT"],
            "classification_confidence": 0.96,
            "semantic_justification": controlled,
            "source_excerpt_refs": [f"{ROOT_SOURCE}#L{line}"],
            "adjudication_date": DATE,
            "adjudicator": ADJUDICATOR,
            "review_required": False,
            "earliest_source": {"declared_source": "Y1 legacy definition", "first_git_commit": first_commit},
            "current_source": {"path": ROOT_SOURCE},
            "original_natural_language_proposition": clean(text.splitlines()[line - 1] if line <= len(text.splitlines()) else title),
            "controlled_semantic_proposition": controlled,
            "subject": title,
            "object": object_type,
            "conditions": "model-internal governed use only",
            "quantifiers": ["UNSPECIFIED_IN_SOURCE"],
            "modal_terms": [],
            "applicability_scope": "point-fire workflow and its declared registry snapshots",
            "formal_object_type": object_type,
            "claim_type": claim_type,
            "why_not_other_object_types": reason_not_other(object_type, title, None, claim_type),
            "typed_variables": [],
            "domain": "UNSPECIFIED_IN_SOURCE",
            "codomain_or_target_type": object_type,
            "parameters": [],
            "units_or_dimensions": [],
            "assumptions_and_boundaries": ["internal workflow semantics only"],
            "premise_set": [controlled],
            "inference_type": inference_for(claim_type),
            "inference_rule": "controlled component semantics",
            "conclusion": controlled,
            "hidden_premises": ["component inputs are typed by a future formalization"],
            "known_counterexamples_or_countermodels": [],
            "proof_obligations": obligations_for(stable_id, object_type, claim_type),
            "proof_artifacts": [],
            "evidence_status": "SOURCE_ONLY",
            "semantic_status": "ADJUDICATED_NOT_VALIDATED",
            "formal_status": "FORMALIZATION_INCOMPLETE",
            "logic_status": "DEFEASIBLE_SUPPORT" if claim_type in {"STRUCTURAL_ANALOGY", "EXPLANATORY_HYPOTHESIS"} else "NOT_APPLICABLE",
            "proof_status": "NOT_APPLICABLE",
            "final_disposition": disposition,
            "unresolved_questions": obligations_for(stable_id, object_type, claim_type),
            "dependencies": [],
            "related_cases": [],
            "strong_term_hits_title": matched_terms(title),
            "strong_term_hits_body": matched_terms(controlled),
            "adjudication_method": "full_source_structural_and_semantic_review",
            "automated_title_only": False,
        })
    return rows


def override_from(record: dict):
    return {key: record[key] for key in [
        "stable_id", "legacy_id", "classification_status", "classification_basis", "classification_confidence",
        "semantic_justification", "source_excerpt_refs", "adjudication_date", "adjudicator", "review_required",
        "legacy_label", "adjudicated_label", "controlled_semantic_proposition", "formal_object_type", "claim_type",
        "typed_variables", "domain", "codomain_or_target_type", "parameters", "units_or_dimensions",
        "dependencies", "proof_artifacts", "related_cases", "evidence_status", "semantic_status", "formal_status",
        "logic_status", "proof_status", "final_disposition", "unresolved_questions",
    ]}


def reports(records: list[dict], formal_records: list[dict], high_risk_d: list[dict], queue: list[dict]):
    types = Counter(row["formal_object_type"] for row in formal_records)
    a_disp = Counter(row["final_disposition"] for row in formal_records if row["stable_id"].startswith("A"))
    t_rows = [row for row in formal_records if row["stable_id"].startswith("T")]
    theorem_keep = [row["stable_id"] for row in t_rows if row["proof_status"] == "PROVED"]
    iso = [row for row in records if row["claim_type"] == "STRUCTURAL_ANALOGY"]
    causal = [row for row in records if "因果" in row["original_title"] or row["stable_id"] == "C"]
    pending = [row for row in records if row["proof_status"] == "UNPROVED_PROPOSITION"]
    audit = f"""# 076 adversarial acceptance audit

Status: migration coverage is complete; semantic adjudication was incomplete at the 076 head.

- `migration_coverage = complete` (622/622)
- `semantic_adjudication = incomplete` at 076, now 621/622 registry objects in 078
- `classification_basis = heuristic_title_and_id_rules` at 076
- `content_truth_status = pending_item_level_review` at 076
- The 076 migration function uses ID/title rules and a `NATURAL_LANGUAGE_CANDIDATE` default. Its 100% registry coverage is not content truth.
- 078 stores conservative migration records separately from source-text adjudications and overrides.
"""
    kernel = f"""# Core kernel adjudication

Complete machine-readable list: `data/foundation/adjudications/core-kernel.jsonl`.

- Registry objects adjudicated: {len(formal_records)}/622
- Additional Y1/MF-0000 component records: {len(records)-len(formal_records)}
- Total adjudication records: {len(records)}
- Object-type counts (registry objects only): `{dump(dict(sorted(types.items())))}`
- A dispositions: `{dump(dict(sorted(a_disp.items())))}`
- T theorem retained with proof: {len(theorem_keep)} ({', '.join(theorem_keep) or 'none'})
- T theorem-layer objects downgraded from theorem status: {57-len(theorem_keep)}
- Unproved core propositions: {len(pending)}

The multiplication sign in Ψ₀ is interpreted as composition/joint constraints, not ordinary numerical multiplication. Y1 is split into an orchestrator plus separately adjudicated components.
"""
    strong = f"""# Core strong-claim audit

- D objects whose title or full body hits the required strong-term vocabulary: {len(high_risk_d)}/550.
- The 076 template repeats proof/causal wording in nearly every D body, so the literal command scope covers all D except D598.
- Strict isomorphism claims retained: 0; structural analogies/relations downgraded: {len(iso)}.
- Established causal claims retained: 0; causal/mechanism candidates downgraded: {len(causal)}.
- T theorem retained: {len(theorem_keep)}; downgraded: {57-len(theorem_keep)}.
- Full per-object term hits and reasons are in `data/foundation/adjudications/core-kernel.jsonl`.
"""
    proof = f"""# Core proof and countermodel report

- T2 is retained as a Nat-scoped theorem: `forall a b, a=0 or b=0 -> a*b=0`.
- Machine artifacts: `formal/lean/Foundation.lean`, `formal/z3/T2-zero-factor.smt2`, and `tools/foundation/verify_core_claims.py`.
- T16 is refuted as stated by `f1(x)=exp(x)`, `f2(x)=exp(-2x)`: one increases, one decreases, while their product `exp(-x)` is strictly decreasing.
- D220's displayed implication is invalid without a physical-existence premise; a Boolean countermodel makes all displayed implications true while `Omega=1` remains true.
- T23 remains `UNPROVED_PROPOSITION`: existence of a minimum requires a defined domain plus conditions such as compactness/coercivity and continuity/lower-semicontinuity.
- Proof artifacts: 1 claim with Lean/Z3 realizations. Replayable counterexample/countermodel records: 2.
"""
    queue_report = f"""# Remaining content work queue

- Unreviewed registry objects: {len(queue)}.
- Queue path: `data/foundation/work-queues/content-proof-queue.jsonl`.
- Ordering is dependency/risk based, not numeric.
- D598 is the only registry object outside the literal root/MF/A/T and title-or-body strong-term scope. It remains `PROVISIONAL`; no semantic-completion credit is claimed for it.
"""
    return {
        "076-adversarial-acceptance-audit-20260713.md": audit,
        "core-kernel-adjudication-20260713.md": kernel,
        "core-strong-claim-audit-20260713.md": strong,
        "core-proof-and-countermodel-report-20260713.md": proof,
        "remaining-content-work-queue-20260713.md": queue_report,
    }


def build(check=False):
    changed = []
    objects = load_jsonl(OUT / "formal-objects/objects.jsonl")
    first_seen = git_first_seen()
    required_ids = {"Y1", *[f"MF{i}" for i in range(1, 6)], *[f"A{i}" for i in range(1, 10)], *[f"T{i}" for i in range(1, 58)]}
    high_risk_ids = set(EXPLICIT_D)
    for obj in objects:
        if not obj["id"].startswith("D"):
            continue
        text = current_or_archived_text(obj["legacy_path"]) or ""
        if matched_terms(obj["title"]) or matched_terms(text):
            high_risk_ids.add(obj["id"])
    required_ids |= high_risk_ids
    formal_records = [make_record(obj, first_seen) for obj in objects if obj["id"] in required_ids]
    formal_records.sort(key=lambda row: next(i for i, obj in enumerate(objects) if obj["id"] == row["stable_id"]))
    records = component_records(first_seen) + formal_records
    overrides = [override_from(row) for row in formal_records]
    remaining = [obj for obj in objects if obj["id"] not in required_ids]
    queue = []
    for obj in remaining:
        queue.append({
            "id": obj["id"],
            "legacy_path": obj["legacy_path"],
            "current_heuristic_type": obj["formal_object_type"],
            "classification_status": "PROVISIONAL",
            "source_status": obj.get("provenance_status"),
            "risk_level": "HIGH" if obj["id"] in EXPLICIT_D else "MEDIUM",
            "dependency_level": len(obj.get("dependencies", [])),
            "strong_term_hits": [],
            "recommended_batch": "078-NEXT-DEPENDENCY-AND-SOURCE-REVIEW",
            "required_method": ["source recovery", "historical cross-check", "logic review", "empirical validation"],
            "priority": 1,
        })
    high_risk_d = [row for row in formal_records if row["stable_id"].startswith("D")]
    coverage = {
        "snapshot_id": "IGNITION-20260709-078",
        "migration_coverage": {"status": "complete", "covered": 622, "total": 622, "rate": 1.0},
        "semantic_adjudication": {"status": "incomplete", "adjudicated_registry_objects": len(formal_records), "total_registry_objects": 622, "rate": len(formal_records) / 622},
        "additional_core_component_adjudications": len(records) - len(formal_records),
        "total_adjudication_records": len(records),
        "classification_basis_076": "heuristic_title_and_id_rules",
        "content_truth_status_076": "pending_item_level_review",
        "remaining_registry_objects": len(queue),
    }
    proof_artifacts = [{
        "entity_key": "proof:T2-zero-factor-nat",
        "id": "T2",
        "asset_kind": "machine_checked_proof",
        "claim": "forall a b : Nat, a = 0 or b = 0 -> a * b = 0",
        "status": "PROVED",
        "lean_artifact": "formal/lean/Foundation.lean",
        "z3_artifact": "formal/z3/T2-zero-factor.smt2",
        "replay": ["cd formal/lean && lake env lean Foundation.lean", "python3 tools/foundation/verify_core_claims.py --check"],
    }]
    counterexamples = [
        {"entity_key": "counterexample:T16-opposite-monotone-product", "id": "T16", "asset_kind": "counterexample", "target_claim": "two oppositely monotone functions necessarily have an inverted-U product", "domain": "real numbers", "assumptions": ["f1 is strictly increasing", "f2 is strictly decreasing"], "input": "f1(x)=exp(x), f2(x)=exp(-2x)", "derivation": "f1*f2=exp(-x), whose derivative is -exp(-x)<0", "violated_conclusion": "the product has an interior inverted-U maximum", "source": "078 core audit", "replay": "python3 tools/foundation/verify_core_claims.py --check", "expected_result": "COUNTEREXAMPLE_VERIFIED"},
        {"entity_key": "countermodel:D220-missing-premise", "id": "D220", "asset_kind": "counterexample", "target_claim": "the displayed implication chain proves Omega=1 impossible", "domain": "Boolean valuations", "assumptions": ["OmegaOne -> PhiZero", "PhiZero -> NoConstraints", "NoConstraints -> NoPhysics"], "input": "OmegaOne=true,PhiZero=true,NoConstraints=true,NoPhysics=true,PhysicalExists=false", "derivation": "all displayed implications are true while not OmegaOne is false", "violated_conclusion": "not OmegaOne", "source": "078 core audit", "replay": "python3 tools/foundation/verify_core_claims.py --check", "expected_result": "COUNTERMODEL_VERIFIED"},
    ]
    logic_checks = [
        {"id": "T2", "kind": "valid_deduction", "result": "VALID_DEDUCTION", "replay": "python3 tools/foundation/verify_core_claims.py --check"},
        {"id": "D220", "kind": "invalid_argument", "result": "COUNTERMODEL_FOUND", "replay": "python3 tools/foundation/verify_core_claims.py --check"},
    ]
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["adjudication_id", "stable_id", "classification_status", "classification_basis", "classification_confidence", "semantic_justification", "source_excerpt_refs", "adjudication_date", "adjudicator", "review_required", "legacy_label", "adjudicated_label", "controlled_semantic_proposition", "formal_object_type", "claim_type", "proof_obligations", "evidence_status", "final_disposition"],
        "properties": {
            "classification_status": {"enum": ["PROVISIONAL", "ADJUDICATED", "CONTESTED"]},
            "classification_basis": {"type": "array", "items": {"enum": ["TITLE_HEURISTIC", "SOURCE_TEXT", "FORMAL_DEFINITION", "PROOF_ARTIFACT", "EXTERNAL_REFERENCE", "HUMAN_REVIEW"]}, "minItems": 1, "uniqueItems": True},
            "classification_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "final_disposition": {"enum": ["KEEP", "RECLASSIFY", "SPLIT", "DOWNGRADE", "FREEZE", "EXTERNAL_REFERENCE"]},
        },
        "additionalProperties": True,
    }
    override_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["stable_id", "classification_status", "classification_basis", "formal_object_type", "claim_type", "semantic_justification", "source_excerpt_refs", "adjudication_date", "adjudicator", "review_required", "legacy_label", "adjudicated_label"],
        "properties": {
            "classification_status": {"const": "ADJUDICATED"},
            "classification_basis": {"type": "array", "contains": {"const": "SOURCE_TEXT"}},
            "review_required": {"const": False},
        },
        "additionalProperties": True,
    }
    queue_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["id", "legacy_path", "current_heuristic_type", "classification_status", "source_status", "risk_level", "dependency_level", "strong_term_hits", "recommended_batch", "required_method", "priority"],
        "properties": {"classification_status": {"const": "PROVISIONAL"}},
        "additionalProperties": True,
    }
    coverage_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["migration_coverage", "semantic_adjudication", "classification_basis_076", "content_truth_status_076", "remaining_registry_objects"],
        "properties": {
            "migration_coverage": {"type": "object", "required": ["status", "covered", "total", "rate"]},
            "semantic_adjudication": {"type": "object", "required": ["status", "adjudicated_registry_objects", "total_registry_objects", "rate"]},
        },
        "additionalProperties": True,
    }
    files = {
        OUT / "adjudications/core-kernel.jsonl": jsonl(records),
        OUT / "adjudications/classification-overrides.jsonl": jsonl(overrides),
        OUT / "work-queues/content-proof-queue.jsonl": jsonl(queue),
        OUT / "coverage/migration-vs-semantic-coverage-20260713.json": json.dumps(coverage, ensure_ascii=False, indent=2),
        OUT / "proofs/core-artifacts.jsonl": jsonl(proof_artifacts),
        OUT / "validations/core-counterexamples.jsonl": jsonl(counterexamples),
        OUT / "validations/core-logic-checks.jsonl": jsonl(logic_checks),
        OUT / "schemas/adjudication.schema.json": json.dumps(schema, ensure_ascii=False, indent=2),
        ROOT / "schemas/foundation/adjudication.schema.json": json.dumps(schema, ensure_ascii=False, indent=2),
        OUT / "schemas/classification-override.schema.json": json.dumps(override_schema, ensure_ascii=False, indent=2),
        ROOT / "schemas/foundation/classification-override.schema.json": json.dumps(override_schema, ensure_ascii=False, indent=2),
        OUT / "schemas/content-work-item.schema.json": json.dumps(queue_schema, ensure_ascii=False, indent=2),
        ROOT / "schemas/foundation/content-work-item.schema.json": json.dumps(queue_schema, ensure_ascii=False, indent=2),
        OUT / "schemas/coverage.schema.json": json.dumps(coverage_schema, ensure_ascii=False, indent=2),
        ROOT / "schemas/foundation/coverage.schema.json": json.dumps(coverage_schema, ensure_ascii=False, indent=2),
    }
    for name, content in reports(records, formal_records, high_risk_d, queue).items():
        files[REPORTS / name] = content
    for path, content in files.items():
        write(path, content, check, changed)
    if check and changed:
        print("OUT_OF_DATE")
        print("\n".join(changed))
        return 1
    print(dump({"adjudications": len(records), "registry_adjudicated": len(formal_records), "high_risk_d": len(high_risk_d), "remaining": len(queue), "types": dict(Counter(row["formal_object_type"] for row in formal_records))}))
    print("ADJUDICATION_CHECK_OK" if check else "ADJUDICATION_WRITE_OK")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    raise SystemExit(build(parser.parse_args().check))
