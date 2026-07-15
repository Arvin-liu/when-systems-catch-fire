#!/usr/bin/env python3
"""Build the 080 full-source-text semantic adjudication artifacts.

This generator is intentionally conservative:
- it never rewrites legacy source files;
- it keeps the 079 fixed queue order as the resumable backbone;
- it only counts reviewer-authored FULL_SOURCE_TEXT_REVIEW records;
- it emits highest-model escalation packages instead of high-risk rulings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/foundation"
SCHEMAS = ROOT / "schemas/foundation"
REPORTS = ROOT / "reports/foundation-architecture"
DATE = "2026-07-13"
TASK_ID = "IGNITION-20260709-080"
MODEL_CLASS = "GPT-5.4-equivalent"
REVIEW_METHOD = "FULL_SOURCE_TEXT_REVIEW"
STATUS = "PARTIAL_RESUMABLE_SOURCE_TEXT_ADJUDICATION"
BRANCH = "records/ignition-080-full-semantic-adjudication-20260713"
BASE_HEAD = "5d28eb5c5654e9acc78ef206f2923b23db66f28f"
SOURCE_QUEUE = DATA / "work-queues/079-semantic-review-queue.jsonl"
QUEUE_PATH = DATA / "work-queues/080-semantic-review-queue.jsonl"
ADJ_PATH = DATA / "adjudications/080-source-text-adjudications.jsonl"
RUN_STATE_PATH = DATA / "adjudications/080-run-state.json"
QUALITY_PATH = DATA / "adjudications/080-quality-audits.jsonl"
ESCALATION_PATH = DATA / "escalations/080-highest-model-queue.jsonl"


def utc8_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
    if text:
        text += "\n"
    path.write_text(text, encoding="utf-8")


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def excerpt(rel_path: str, ranges: list[tuple[int, int]]) -> str:
    lines = (ROOT / rel_path).read_text(encoding="utf-8").splitlines()
    chunks: list[str] = []
    for start, end in ranges:
        segment = " ".join(line.strip() for line in lines[start - 1:end] if line.strip())
        if segment:
            chunks.append(segment)
    return " ".join(chunks)


def anchor_objects(rel_path: str, ranges: list[tuple[int, int]]) -> list[dict[str, Any]]:
    return [
        {
            "path": rel_path,
            "start_line": start,
            "end_line": end,
            "excerpt_sha256": sha256_bytes(
                "\n".join(
                    (ROOT / rel_path).read_text(encoding="utf-8").splitlines()[start - 1:end]
                ).encode("utf-8")
            ),
        }
        for start, end in ranges
    ]


def parse_embedded_source_reference(rel_path: str) -> str | None:
    text = (ROOT / rel_path).read_text(encoding="utf-8")
    match = re.search(r"\*\*原文来源 / Source\*\*：`([^`]+)`", text)
    return match.group(1) if match else None


def parse_related_cases(rel_path: str) -> list[str]:
    lines = (ROOT / rel_path).read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    capture = False
    for line in lines:
        if line.startswith("**关联案例 / Related Cases**"):
            capture = True
            continue
        if capture:
            if line.startswith("## "):
                break
            match = re.search(r"C-\d{4}", line)
            if match:
                out.append(match.group(0))
    return out


def load_objects() -> dict[str, dict[str, Any]]:
    rows = load_jsonl(DATA / "formal-objects/objects.jsonl")
    return {row["id"]: row for row in rows}


def derive_risk_level(oid: str, rel_path: str, title: str) -> str:
    text = f"{oid} {title} {rel_path}"
    strong = [
        "定理",
        "同构",
        "因果",
        "充要",
        "必然",
        "唯一",
        "精确",
        "不可能",
        "倒U",
        "相变",
        "概率",
    ]
    if oid.startswith(("MF", "A", "T")):
        return "HIGH"
    if any(token in text for token in strong):
        return "HIGH"
    return "NORMAL"


def base_queue() -> list[dict[str, Any]]:
    objects = load_objects()
    prior = load_jsonl(SOURCE_QUEUE)
    existing = {row["stable_id"]: row for row in load_jsonl(QUEUE_PATH)}
    built: list[dict[str, Any]] = []
    for index, row in enumerate(prior, start=1):
        oid = row["id"]
        obj = objects[oid]
        rel_path = obj["legacy_path"]
        legacy_blob_sha = sha256_path(ROOT / rel_path)
        old = existing.get(oid, {})
        keep_old = old.get("legacy_blob_sha") == legacy_blob_sha
        built.append(
            {
                "stable_id": oid,
                "legacy_path": rel_path,
                "legacy_blob_sha": legacy_blob_sha,
                "source_paths": obj.get("source_paths") or [rel_path],
                "dependency_ids": obj.get("dependencies") or [],
                "risk_level": derive_risk_level(oid, rel_path, obj["title"]),
                "priority": row["priority"],
                "status": old.get("status", "PENDING") if keep_old else "PENDING",
                "assigned_batch": (index - 1) // 25 + 1,
                "last_updated_at": old.get("last_updated_at", utc8_now()) if keep_old else utc8_now(),
                "review_record_id": old.get("review_record_id") if keep_old else None,
            }
        )
    return built


def defn_spec(
    *,
    path: str,
    ranges: list[tuple[int, int]],
    original_claim: str,
    controlled: str,
    subject: str,
    predicate: str,
    formal_object_type: str,
    claim_type: str = "DEFINITION",
    premises: list[str] | None = None,
    hidden_premises: list[str] | None = None,
    scope: str,
    boundary: list[str],
    failure: list[str],
    counterexample: list[str],
    allowed: list[str],
    forbidden: list[str],
    open_questions: list[str],
    strong_terms: list[str] | None = None,
    logic_status: str = "SCOPED_DEFINITION",
    formalization_status: str = "PARTIALLY_FORMALIZED",
    proof_status: str = "NOT_APPLICABLE_DEFINITION",
    evidence_status: str = "ILLUSTRATIVE_CASES_ONLY",
    confidence: float = 0.83,
) -> dict[str, Any]:
    return {
        "legacy_path": path,
        "source_ranges": ranges,
        "original_claim": original_claim,
        "controlled": controlled,
        "subject": subject,
        "predicate": predicate,
        "quantifiers": ["local-context only", "no global universality stated beyond source scope"],
        "modality": "definitional",
        "premises": premises or ["source labels are interpreted only inside the point-fire internal framework"],
        "hidden_premises": hidden_premises or ["evaluation rule for assigning concrete values is not fully specified"],
        "scope": scope,
        "boundary": boundary,
        "failure": failure,
        "counterexample": counterexample,
        "formal_object_type": formal_object_type,
        "claim_type": claim_type,
        "logic_form": "framework-scoped definition or scoring rule",
        "logic_status": logic_status,
        "formalization_status": formalization_status,
        "proof_status": proof_status,
        "evidence_status": evidence_status,
        "provenance_status": "LEGACY_SOURCE_RECOVERED_IN_FILE",
        "allowed": allowed,
        "forbidden": forbidden,
        "open_questions": open_questions,
        "strong_terms": strong_terms or [],
        "highest_model_escalation_required": False,
        "escalation_reason": "",
        "confidence": confidence,
    }


def mechanism_spec(**kwargs: Any) -> dict[str, Any]:
    base = defn_spec(
        logic_status="DEFEASIBLE_SUPPORT",
        formalization_status="SEMANTICALLY_SCOPED_UNTYPED",
        proof_status="NOT_APPLICABLE_MECHANISM",
        evidence_status="ILLUSTRATIVE_CASES_ONLY",
        claim_type="EXPLANATORY_HYPOTHESIS",
        **kwargs,
    )
    base["logic_form"] = "directional mechanism claim with source-scoped drivers"
    return base


def proposition_spec(**kwargs: Any) -> dict[str, Any]:
    base = defn_spec(
        logic_status="HIDDEN_PREMISE_PRESENT",
        formalization_status="REQUIRES_TYPED_STATEMENT",
        proof_status="UNPROVED_PROPOSITION",
        evidence_status="ILLUSTRATIVE_CASES_ONLY",
        claim_type="MATHEMATICAL_PROPOSITION",
        **kwargs,
    )
    base["logic_form"] = "source-scoped formal proposition or theorem-style claim"
    return base


def analogy_spec(**kwargs: Any) -> dict[str, Any]:
    base = defn_spec(
        logic_status="ANALOGY_NOT_EQUIVALENCE",
        formalization_status="MISSING_STRUCTURE_PRESERVATION_MAP",
        proof_status="NO_EQUIVALENCE_PROOF",
        evidence_status="ILLUSTRATIVE_CASES_ONLY",
        claim_type="STRUCTURAL_ANALOGY",
        **kwargs,
    )
    base["logic_form"] = "analogy or mapping claim without proven equivalence"
    return base


FIRST_BATCH_SPECS: dict[str, dict[str, Any]] = {
    "MF1": defn_spec(
        path="统一函数总表/0000-MF-0001-正向自举通道.md",
        ranges=[(16, 32)],
        original_claim="正向自举通道负责计算 J⁺，给出对象是否通过正向纳入判定。",
        controlled="Within MF-0000's internal workflow, MF1 defines a Boolean admission predicate J⁺ over the current candidate set X_n, where J⁺(x)=1 marks x as eligible for positive inclusion in ΔB_n.",
        subject="MF1 / J⁺",
        predicate="assigns positive-admission status to a candidate object inside one bootstrap round",
        formal_object_type="PREDICATE",
        scope="MF-0000 internal suboperator only; not an external truth predicate",
        boundary=["does not compute J⁻", "does not resolve conflicts", "does not decide convergence"],
        failure=["the candidate universe X_n is undefined", "no executable admission test is provided"],
        counterexample=["exhibit a case where J⁺ is required to decide more than admission status"],
        allowed=["internal positive-admission predicate", "bootstrap intake gate"],
        forbidden=["proved theorem of truth", "standalone total function over all domains"],
        open_questions=["what concrete observable rule sets J⁺(x)=1 for real objects?"],
        strong_terms=["内部子算子"],
    ),
    "MF2": defn_spec(
        path="统一函数总表/0000-MF-0002-反向自举通道.md",
        ranges=[(16, 32)],
        original_claim="反向自举通道负责计算 J⁻，给出对象是否触发反向排除或反证。",
        controlled="Within MF-0000's internal workflow, MF2 defines a Boolean exclusion predicate J⁻ over the current candidate set X_n, where J⁻(x)=1 marks x for reverse correction, exclusion, or rebuttal handling.",
        subject="MF2 / J⁻",
        predicate="assigns reverse-exclusion status to a candidate object inside one bootstrap round",
        formal_object_type="PREDICATE",
        scope="MF-0000 internal suboperator only; not an external falsity predicate",
        boundary=["does not admit objects", "does not resolve J⁺/J⁻ conflicts", "does not decide convergence"],
        failure=["the candidate universe X_n is undefined", "no executable exclusion rule is provided"],
        counterexample=["show a use where MF2 is required to compute more than exclusion/rebuttal status"],
        allowed=["internal exclusion predicate", "reverse bootstrap gate"],
        forbidden=["global proof of falsity", "standalone total function over all domains"],
        open_questions=["what evidence rule sets J⁻(x)=1 in concrete reviews?"],
        strong_terms=["内部子算子"],
    ),
    "MF3": defn_spec(
        path="统一函数总表/0000-MF-0003-正反互斥判定器.md",
        ranges=[(16, 32)],
        original_claim="正反互斥判定器排除 J⁺=J⁻=1 的双真冲突。",
        controlled="Within MF-0000's internal workflow, MF3 defines a consistency predicate E(x) that blocks simultaneous positive admission and reverse exclusion on the same candidate object.",
        subject="MF3 / E(x)",
        predicate="checks mutual exclusivity of J⁺ and J⁻ on the same object",
        formal_object_type="PREDICATE",
        scope="MF-0000 internal conflict screen only",
        boundary=["does not determine which side should win", "does not repair the conflict by itself"],
        failure=["the meanings of J⁺ and J⁻ are left operationally unspecified", "conflict-resolution procedure after failure is unstated"],
        counterexample=["produce a valid state with J⁺=J⁻=1 that should still count as converged"],
        allowed=["mutual-exclusion predicate", "conflict screen"],
        forbidden=["full contradiction solver", "standalone proof system"],
        open_questions=["what workflow handles pending/contradiction after MF3 detects failure?"],
    ),
    "MF4": defn_spec(
        path="统一函数总表/0000-MF-0004-自举嵌套判定器.md",
        ranges=[(16, 32)],
        original_claim="自举嵌套判定器通过 B_{n+1}=N_n(B_n ⊕ ΔB_n) 将通道与归一化算子连接成迭代结构。",
        controlled="Within MF-0000's internal workflow, MF4 defines the bootstrap state update rule that advances one round when ΔB_n is non-empty and otherwise hands control to a separate convergence check.",
        subject="MF4 / bootstrap update",
        predicate="updates B_n to B_{n+1} under the source-defined iteration template",
        formal_object_type="STATE_TRANSITION",
        claim_type="ALGORITHMIC_CLAIM",
        premises=["N_n is assumed to be a normalization operator over the current bundle state"],
        hidden_premises=["the merge operator ⊕ is not typed", "termination and normalization semantics are not formalized"],
        scope="MF-0000 internal round-to-round update only",
        boundary=["does not prove termination", "does not prove uniqueness of the next state beyond the informal update template"],
        failure=["N_n is undefined", "ΔB_n cannot be represented in a shared state space"],
        counterexample=["show two incompatible next states from the same B_n and ΔB_n under equally plausible normalizations"],
        allowed=["state-transition template", "bootstrap update rule"],
        forbidden=["proved convergent algorithm", "fully typed recurrence theorem"],
        open_questions=["what is the exact state representation for B_n and ΔB_n?"],
        logic_status="SCOPED_UPDATE_RULE",
        formalization_status="REQUIRES_TYPED_STATE_SPACE",
        proof_status="NOT_APPLICABLE_ALGORITHMIC_TEMPLATE",
        evidence_status="SOURCE_INTERNAL_ONLY",
        confidence=0.84,
    ),
    "MF5": defn_spec(
        path="统一函数总表/0000-MF-0005-自举收敛判定器.md",
        ranges=[(16, 32)],
        original_claim="自举收敛判定器在无新增量且无双真冲突时判断自举过程收敛。",
        controlled="Within MF-0000's internal workflow, MF5 defines a convergence predicate over the current bootstrap state by requiring no new increment, state equality across one update, and absence of J⁺/J⁻ double-true conflicts.",
        subject="MF5 / Converged(B_n)",
        predicate="marks a bootstrap state as converged under source-defined internal conditions",
        formal_object_type="PREDICATE",
        scope="MF-0000 internal stopping check only",
        boundary=["does not generate ΔB_n", "does not justify that these conditions are sufficient for semantic completeness"],
        failure=["state equality B_{n+1}=B_n is ill-defined", "candidate set X_n is unspecified"],
        counterexample=["show a workflow satisfying the predicate while still admitting meaningful unresolved increments"],
        allowed=["internal convergence predicate", "stopping gate"],
        forbidden=["proof of global semantic completeness", "external theorem of truth"],
        open_questions=["what prevents spurious fixed points caused by under-observation?"],
    ),
    "A1": defn_spec(
        path="统一函数总表/0002-A1-I(t,L) 提议者意识.md",
        ranges=[(18, 20), (58, 73)],
        original_claim="提议者是否有意识，二值变量，不可推导，作为框架起点。",
        controlled="Within the source framework, A1 introduces a binary awareness predicate for the proposer role; it is treated as an undecomposed starting assumption rather than a derived theorem.",
        subject="A1 / proposer awareness",
        predicate="classifies whether the proposer is counted as aware inside the framework",
        formal_object_type="PREDICATE",
        scope="framework-internal starting assumption about a proposer at time t and layer L",
        boundary=["no causal or measurement procedure is supplied", "historical examples illustrate the distinction but do not prove the predicate"],
        failure=["awareness is not operationalized", "the time/layer parameters are never typed"],
        counterexample=["show two equally source-compatible readings that assign opposite A1 values to the same case"],
        allowed=["binary awareness predicate", "axiom-layer starting condition"],
        forbidden=["empirically verified consciousness detector", "proved universal law of history"],
        open_questions=["what observable criteria distinguish I=1 from I=0 in new cases?"],
    ),
    "A2": defn_spec(
        path="统一函数总表/0003-A2-提议者姿态的激进程度.md",
        ranges=[(18, 20), (56, 71)],
        original_claim="提议者姿态的激进程度以 0 到 1 表示，并附带一个退化免疫乘法式。",
        controlled="Within the source framework, A2 introduces a source-scoped aggressiveness score for proposer posture, where lower values denote egalitarian posture and higher values denote suppressive posture; the attached D_immune expression is illustrative rather than a fully typed evaluable function.",
        subject="A2 / proposer posture aggressiveness",
        predicate="assigns an informal normalized aggressiveness score inside the framework",
        formal_object_type="NATURAL_LANGUAGE_CANDIDATE",
        scope="framework-internal score only; not a rigorously defined metric space object",
        boundary=["the 0-to-1 scoring rule is not operationalized", "D_immune is introduced without typed variables or units"],
        failure=["different reviewers can map the same case to different scores with no tie-break rule", "the attached immune expression lacks executable semantics"],
        counterexample=["produce two incompatible score assignments that both fit the narrative examples"],
        allowed=["score-like source variable", "source-scoped posture index candidate"],
        forbidden=["strict metric", "proved quantitative law"],
        open_questions=["what procedure maps observed posture into a stable 0-to-1 value?"],
        strong_terms=["退化免疫"],
        logic_status="SCORING_RULE_UNDERDEFINED",
        formalization_status="INSUFFICIENTLY_TYPED_SCORE",
        proof_status="NOT_APPLICABLE_SCORE_DEFINITION",
        confidence=0.78,
    ),
    "A3": defn_spec(
        path="统一函数总表/0004-A3-R(t,L,C) 应约者退出权.md",
        ranges=[(18, 20), (58, 73)],
        original_claim="应约者的退出权类型分为真实、事实、心理、象征，不可推导，作为框架起点。",
        controlled="Within the source framework, A3 classifies a responder's exit-right status into source-defined categories such as real, factual, psychological, or symbolic, without a typed rule that forces one unique category from observable inputs.",
        subject="A3 / responder exit-right status",
        predicate="relates a responder context to a source-defined exit-right category",
        formal_object_type="RELATION",
        scope="framework-internal categorization of exit-right status",
        boundary=["the category vocabulary is source-defined rather than legally or empirically standardized", "no typed classifier is given"],
        failure=["the same case can plausibly satisfy multiple category descriptions", "the absence case R=无 appears in verification but is not in the displayed set"],
        counterexample=["exhibit a source-compatible case that belongs to two categories at once"],
        allowed=["exit-right relation", "source-scoped category relation"],
        forbidden=["total function with proven unique output", "legal ontology of exit rights"],
        open_questions=["is R=无 a separate category or shorthand for symbolic/zero exit right?"],
        logic_status="CATEGORY_BOUNDARY_AMBIGUOUS",
        formalization_status="REQUIRES_TYPED_CATEGORY_SYSTEM",
        confidence=0.79,
    ),
    "A4": mechanism_spec(
        path="统一函数总表/0005-A4-R_perceived(t,L,C) 应约者感知退出权.md",
        ranges=[(18, 20), (57, 72)],
        original_claim="应约者感知到的退出权是真实退出权经过感知过滤后的结果。",
        controlled="Within the source framework, A4 states that perceived exit right is a filtered, awareness- and cost-sensitive projection of underlying exit-right conditions rather than a directly observed copy of A3.",
        subject="A4 / perceived exit right",
        predicate="models how actual exit-right conditions are filtered into what responders perceive",
        formal_object_type="MECHANISM_MODEL",
        scope="source-scoped perception mechanism around exit rights",
        boundary=["the filtering function f is unspecified", "the model does not identify causal effects from observational examples"],
        failure=["awareness, information access, and effective exit cost are not operationally defined", "different filters can reproduce the same prose"],
        counterexample=["show a case where A3 is high but perceived exit right stays low for reasons outside the stated filter family"],
        allowed=["perception mechanism", "filtered exit-right model"],
        forbidden=["causal model with identified effects", "fully typed function with executable semantics"],
        open_questions=["what are the four phase-transition paths referenced in the annotation?"],
    ),
    "A5": defn_spec(
        path="统一函数总表/0006-A5-应约者退出的成本.md",
        ranges=[(18, 20), (57, 72)],
        original_claim="应约者退出成本由八个维度构成，并可通过阈值统计得到锁定维度数。",
        controlled="Within the source framework, A5 introduces an eight-dimension cost description for exit, together with a threshold-counting summary n_lock, but it does not provide a typed measurement protocol that would make the cost object a strict metric or total function.",
        subject="A5 / exit cost profile",
        predicate="describes exit cost as a multi-dimension source-scoped cost profile with a threshold count summary",
        formal_object_type="NATURAL_LANGUAGE_CANDIDATE",
        scope="framework-internal cost profile only",
        boundary=["no units or aggregation rule are fixed for the eight dimensions", "the Landauer note is a theoretical add-on rather than part of the base operational rule"],
        failure=["dimension values cannot be compared without units", "thresholds θ_C(i) are unspecified"],
        counterexample=["show two incompatible threshold systems producing different n_lock values from the same case"],
        allowed=["multi-dimension cost profile", "source-scoped lock-count heuristic"],
        forbidden=["strict metric", "physically validated universal law"],
        open_questions=["which dimensions are mandatory in minimal reviews?"],
        logic_status="SCORING_RULE_UNDERDEFINED",
        formalization_status="INSUFFICIENTLY_TYPED_SCORE",
        proof_status="NOT_APPLICABLE_SCORE_DEFINITION",
        confidence=0.77,
    ),
    "A6": mechanism_spec(
        path="统一函数总表/0007-A6-H(t,L) 遮蔽函数(双源).md",
        ranges=[(18, 20), (57, 72)],
        original_claim="遮蔽函数由主动遮蔽和系统不兼容性双源构成，并通过更强来源主导退化类型。",
        controlled="Within the source framework, A6 is a source-scoped two-source obscuration mechanism combining proposer-side obscuration and system incompatibility, with the stronger source taken to dominate the degradation mode description.",
        subject="A6 / obscuration mechanism",
        predicate="models obscuration as a two-source mechanism affecting what responders can perceive",
        formal_object_type="MECHANISM_MODEL",
        scope="source-scoped explanatory mechanism for obscuration",
        boundary=["the aggregator f and the dominance rule are not fully typed", "the identity-locking extension is illustrative rather than validated"],
        failure=["H_pro and Σ_compatibility are not measurable under a shared protocol", "argmax over heterogeneous sources is underspecified"],
        counterexample=["show a case where dual-source obscuration predicts the wrong dominant mechanism under the source examples"],
        allowed=["dual-source obscuration mechanism", "source-scoped degradation driver"],
        forbidden=["identified causal model", "strict function with validated measurements"],
        open_questions=["how should the source compare active obscuration and structural incompatibility on one scale?"],
    ),
    "A7": defn_spec(
        path="统一函数总表/0008-A7-退出权信号.md",
        ranges=[(18, 20), (60, 75)],
        original_claim="退出权信号为八维展开，主权函数是各维度信号之和。",
        controlled="Within the source framework, A7 introduces a source-scoped sovereignty signal constructed from multiple dimensions, but it remains an informal score composition rather than a fully typed additive function with units and normalization.",
        subject="A7 / exit-right signal",
        predicate="describes a multi-dimension sovereignty signal and its additive summary",
        formal_object_type="NATURAL_LANGUAGE_CANDIDATE",
        scope="framework-internal signal concept only",
        boundary=["the ε_i dimensions are not typed or normalized", "simple summation is asserted but not justified across heterogeneous dimensions"],
        failure=["heterogeneous dimensions cannot be added without a normalization scheme", "signal meaning shifts across cases"],
        counterexample=["show two normalization choices that reverse the same case ranking"],
        allowed=["multi-dimension signal candidate", "source-scoped sovereignty index idea"],
        forbidden=["strict metric", "validated additive law"],
        open_questions=["what normalization makes ε_i commensurable across dimensions?"],
        strong_terms=["主权函数"],
        logic_status="HETEROGENEOUS_SUM_UNDERDEFINED",
        formalization_status="INSUFFICIENTLY_TYPED_SCORE",
        proof_status="NOT_APPLICABLE_SCORE_DEFINITION",
        confidence=0.77,
    ),
    "A8": defn_spec(
        path="统一函数总表/0009-A8-dim(t,L) 决策维度.md",
        ranges=[(18, 20), (61, 76)],
        original_claim="决策维度为二值结构变量：无犹豫域时为 2，有犹豫域时为 3。",
        controlled="Within the source framework, A8 acts as a binary structural predicate about whether a hesitation region is present; the displayed numeric values 2 and 3 encode absence versus presence of that region rather than a fully developed mathematical dimension theory.",
        subject="A8 / hesitation-region structure",
        predicate="classifies whether the local decision structure contains a hesitation region",
        formal_object_type="PREDICATE",
        scope="framework-internal structural distinction only",
        boundary=["the numeric labels 2 and 3 are descriptive codes, not a proof of geometric dimension", "historical examples do not operationalize classification"],
        failure=["the hesitation-region criterion is undefined", "the same case can be coded differently under different interpretations"],
        counterexample=["show a source-compatible case where hesitation-region presence is indeterminate"],
        allowed=["binary structural predicate", "hesitation-region classifier"],
        forbidden=["proved geometric dimension theorem", "strict dimension function on typed spaces"],
        open_questions=["what exact condition distinguishes dim=2 from dim=3 in new cases?"],
        logic_status="CATEGORY_BOUNDARY_AMBIGUOUS",
        formalization_status="PARTIALLY_FORMALIZED",
        confidence=0.8,
    ),
    "A9": mechanism_spec(
        path="统一函数总表/0010-A9-P_exit(t,L,C) 退出概率.md",
        ranges=[(18, 20), (60, 75)],
        original_claim="退出概率是退出权信号、退出成本和感知退出权的函数，任一因子为零则概率为零。",
        controlled="Within the source framework, A9 is a source-scoped probabilistic model sketch in which exit probability depends on signal strength, cost, and perceived exit right; the text supports a directional dependency claim but not a fully specified probability law.",
        subject="A9 / exit probability",
        predicate="models exit probability as depending on signal, cost, and perceived exit right",
        formal_object_type="PROBABILISTIC_MODEL",
        scope="framework-internal probability sketch only",
        boundary=["no sample space or probability calibration is supplied", "zero-factor claims are stated heuristically rather than proved"],
        failure=["P_exit is not tied to observable frequencies", "the dependency function f is unspecified"],
        counterexample=["show a source-compatible case with nonzero signal/cost/perception but ambiguous exit probability under multiple plausible models"],
        allowed=["probability-model sketch", "source-scoped dependency model"],
        forbidden=["calibrated probabilistic theorem", "identified causal model"],
        open_questions=["what probability space and event definition would make P_exit measurable?"],
        strong_terms=["概率"],
    ),
    "T1": proposition_spec(
        path="统一函数总表/0011-T1-点火充要条件.md",
        ranges=[(18, 20), (59, 74)],
        original_claim="点火（系统可持续）的充要条件由五因子乘法给出，任一因子为零则系统不可持续。",
        controlled="Within the source framework, T1 asserts a theorem-style biconditional: system sustainability is governed by a five-factor multiplicative structure whose zero factors destroy sustainability; the current text supports this as a source-scoped formal proposition but not as a proved necessary-and-sufficient theorem.",
        subject="T1 / sustainability condition",
        predicate="claims a five-factor multiplicative condition for system sustainability",
        formal_object_type="FORMAL_PROPOSITION",
        scope="source-defined internal model only; no external mathematical or empirical universality is established",
        boundary=["symbol types and quantifiers are omitted", "the biconditional strength is stronger than the provided derivation"],
        failure=["one factor can be zero while sustainability still holds under a faithful typed reading", "multiple typed formalizations disagree on necessity or sufficiency"],
        counterexample=["construct a typed model in which the five displayed factors are nonzero but sustainability fails, or vice versa"],
        allowed=["source-scoped five-factor proposition", "unproved theorem-style claim"],
        forbidden=["proved necessary-and-sufficient theorem", "externally validated law of sustainability"],
        open_questions=["what are the precise domains of I, Posture_deg, R, ε_eff, and Δv?", "does R denote a category or a numeric gate in the product?"],
        strong_terms=["充要条件"],
        confidence=0.86,
    ),
    "T3": mechanism_spec(
        path="统一函数总表/0013-T3-ε双向动力学.md",
        ranges=[(18, 20), (55, 74)],
        original_claim="退出权信号的双向动力学由增长项和衰减项组成，持续演化。",
        controlled="Within the source framework, T3 gives a state-transition sketch for ε in which awareness and speed-difference terms drive growth while posture and obscuration drive decay; it is a directional dynamics model rather than a proved differential equation theorem.",
        subject="T3 / epsilon dynamics",
        predicate="describes source-scoped growth and decay terms for ε over time",
        formal_object_type="STATE_TRANSITION",
        scope="source-scoped internal dynamics model only",
        boundary=["coefficients α and β are unspecified", "continuous-time notation is not tied to a typed state space or empirical time scale"],
        failure=["different interpretations of ε or σ(Δv) produce incompatible trajectories", "the convergence note to D12 leaves exact relation unresolved"],
        counterexample=["produce a faithful typing where the stated growth/decay sign pattern fails to predict the source examples"],
        allowed=["state-transition model", "directional dynamics sketch"],
        forbidden=["proved ODE theorem", "calibrated empirical differential law"],
        open_questions=["how exactly does T3 relate to D12 beyond being called a continuous version?"],
    ),
    "T4": analogy_spec(
        path="统一函数总表/0014-T4-乘法对称变换.md",
        ranges=[(18, 20), (55, 70)],
        original_claim="乘法系统存在对称变换，可将点火问题转换为生存概率问题。",
        controlled="Within the source framework, T4 proposes a mapping between a multiplicative ignition formulation and a survival-probability viewpoint, but the current text does not supply a typed bijection, inverse, or proof that the transformation preserves truth conditions exactly.",
        subject="T4 / multiplicative transform",
        predicate="maps an ignition framing to a survival-probability framing",
        formal_object_type="RELATION",
        scope="source-scoped reformulation claim only",
        boundary=["no explicit transformation rule is written beyond slogan-level symbol swaps", "equivalence is not proved"],
        failure=["two plausible transformations yield different truth values", "the mapped variables are not type-compatible"],
        counterexample=["give a typed ignition instance whose survival-probability image is non-equivalent under one plausible mapping"],
        allowed=["reformulation candidate", "structural mapping claim"],
        forbidden=["exact equivalence theorem", "strict isomorphism"],
        open_questions=["what is the actual transformation function between the two framings?", "is D ↔ 1-P definitional or heuristic?"],
        strong_terms=["对称变换"],
        confidence=0.81,
    ),
    "T5": analogy_spec(
        path="统一函数总表/0015-T5-凯利公式认知边界.md",
        ranges=[(18, 20), (55, 70)],
        original_claim="凯利公式给出最优下注比例，认知边界决定财富上限。",
        controlled="Within the source framework, T5 uses the Kelly formula as an analogy source to argue that cognition bounds attainable wealth, but the current text does not derive a structure-preserving theorem from Kelly betting to the point-fire cognition setting.",
        subject="T5 / Kelly cognition analogy",
        predicate="links Kelly-style optimal betting intuition to a cognition-bound wealth narrative",
        formal_object_type="RELATION",
        scope="analogy-level transfer from an external theorem source into the framework",
        boundary=["the financial and cognition variables are not formally linked", "wealth upper-bound language is stronger than the shown derivation"],
        failure=["the Kelly context and cognition context diverge under typed assumptions", "no inverse or preservation map exists"],
        counterexample=["show a cognition-wealth setup where the Kelly analogy does not preserve the claimed upper-bound behavior"],
        allowed=["structural analogy", "Kelly-inspired boundary intuition"],
        forbidden=["proved point-fire theorem", "exact imported theorem"],
        open_questions=["which variables in the cognition setting correspond to E[r] and Var(r]?"],
        strong_terms=["凯利公式"],
        confidence=0.8,
    ),
    "T6": defn_spec(
        path="统一函数总表/0016-T6-自举激活条件.md",
        ranges=[(18, 20), (59, 74)],
        original_claim="自举循环激活取决于三因子乘法超过阈值。",
        controlled="Within the source framework, T6 defines a threshold predicate for bootstrap activation using a three-factor product; it supports a source-scoped activation rule but not a proved universal theorem of self-bootstrap.",
        subject="T6 / bootstrap activation",
        predicate="marks whether the displayed activation product exceeds the bootstrap threshold",
        formal_object_type="PREDICATE",
        claim_type="ALGORITHMIC_CLAIM",
        scope="source-scoped threshold rule for bootstrap activation",
        boundary=["P_track and θ_boot are not typed or calibrated", "the inequality is presented as a rule rather than a proved necessity/sufficiency theorem"],
        failure=["the threshold can be shifted without a source rule", "different σ choices change activation outcomes"],
        counterexample=["show a faithful typed model where the product exceeds threshold but self-bootstrap still cannot start"],
        allowed=["threshold activation rule", "bootstrap gate predicate"],
        forbidden=["proved universal self-bootstrap theorem", "fully calibrated decision function"],
        open_questions=["what are the admissible ranges of P_track and θ_boot?"],
        strong_terms=["阈值条件"],
        logic_status="THRESHOLD_RULE_WITH_HIDDEN_PREMISES",
        formalization_status="REQUIRES_TYPED_THRESHOLD_SYSTEM",
        proof_status="NOT_APPLICABLE_ALGORITHMIC_TEMPLATE",
        confidence=0.82,
    ),
    "T7": mechanism_spec(
        path="统一函数总表/0017-T7-好奇心驱动函数.md",
        ranges=[(18, 20), (56, 71)],
        original_claim="好奇心驱动由四因子乘法构成，并被描述为自主意识的元点。",
        controlled="Within the source framework, T7 states a mechanism in which awareness, decision-structure, exit probability, and knowledge gain jointly support curiosity drive, but the current text does not prove that this product uniquely or universally determines curiosity.",
        subject="T7 / curiosity drive",
        predicate="models curiosity drive as a four-factor mechanism with threshold-like modulation",
        formal_object_type="MECHANISM_MODEL",
        scope="source-scoped internal mechanism for curiosity drive",
        boundary=["knowledge gain and threshold terms are undefined operationally", "the 'meta-point of autonomy' wording is explanatory rather than proved"],
        failure=["alternative mechanisms explain the same examples", "the product form is not uniquely justified"],
        counterexample=["show a source-compatible setting with high curiosity despite one factor near zero, or vice versa"],
        allowed=["mechanism hypothesis", "source-scoped curiosity model"],
        forbidden=["proved law of consciousness", "strict causal model"],
        open_questions=["what exactly is K₀ and how is ΔK measured?"],
        strong_terms=["元点"],
    ),
    "T8": mechanism_spec(
        path="统一函数总表/0018-T8-ε相变级联.md",
        ranges=[(18, 20), (54, 69)],
        original_claim="ε_aware 从 0 变为正会触发五个级联相变，统一于 D72 框架。",
        controlled="Within the source framework, T8 proposes a cascade state-transition story in which the sign change of ε_aware triggers multiple downstream shifts; the text supports a directional transition narrative, not a proved universal phase-transition theorem.",
        subject="T8 / epsilon cascade",
        predicate="describes a source-scoped cascade from ε_aware becoming positive",
        formal_object_type="STATE_TRANSITION",
        scope="source-scoped internal cascade narrative tied to D72",
        boundary=["the five phase changes are not enumerated in the object itself", "the trigger and downstream variables are not typed"],
        failure=["the D72 mapping is ambiguous", "multiple cascade decompositions fit the same prose"],
        counterexample=["show a faithful source-compatible model where ε_aware>0 does not induce the claimed cascade"],
        allowed=["cascade transition hypothesis", "D72-linked state-transition story"],
        forbidden=["proved phase-transition theorem", "externally validated law of cognition"],
        open_questions=["what are the five specific transitions and their order?"],
        strong_terms=["相变"],
    ),
    "T9": defn_spec(
        path="统一函数总表/0019-T9-自主意识函数.md",
        ranges=[(18, 20), (54, 69)],
        original_claim="自主意识的数学度量由三因子乘法给出，任一归零则 Ψ 归零。",
        controlled="Within the source framework, T9 proposes a score-like autonomy quantity built from awareness, decision structure, and exit probability, but the current text does not furnish a typed measurement protocol that would justify treating it as a strict metric or total function.",
        subject="T9 / autonomy quantity",
        predicate="introduces a source-scoped autonomy score candidate",
        formal_object_type="NATURAL_LANGUAGE_CANDIDATE",
        scope="framework-internal autonomy score only",
        boundary=["the displayed product lacks typed domains and units", "the derivative and zeroing remarks are not backed by a full proof here"],
        failure=["different normalizations alter the autonomy score materially", "the same examples fit multiple score constructions"],
        counterexample=["show two source-compatible product constructions yielding incompatible autonomy orderings"],
        allowed=["autonomy score candidate", "source-scoped product indicator"],
        forbidden=["strict metric", "proved universal consciousness law"],
        open_questions=["is Ψ_autonomy intended as ordinal, interval, or merely symbolic?"],
        strong_terms=["数学度量"],
        logic_status="SCORING_RULE_UNDERDEFINED",
        formalization_status="INSUFFICIENTLY_TYPED_SCORE",
        proof_status="NOT_APPLICABLE_SCORE_DEFINITION",
        confidence=0.78,
    ),
    "T10": proposition_spec(
        path="统一函数总表/0020-T10-缓存倒U型.md",
        ranges=[(18, 20), (52, 67)],
        original_claim="缓存冲突概率在缓存大小约为活跃节点数 1.4 倍时取最大值。",
        controlled="Within the source framework, T10 makes a theorem-style optimization claim about the location of a maximum collision probability near 1.4×N_active; the text supports this as an unproved optimization proposition rather than an established exact result.",
        subject="T10 / cache collision optimum",
        predicate="claims a peak location for collision probability as cache size varies",
        formal_object_type="OPTIMIZATION_PROBLEM",
        scope="source-scoped cache-model claim only",
        boundary=["the collision probability formula is not shown", "the constant 1.4 is asserted without derivation in this object"],
        failure=["different cache models yield different optimum constants", "the objective function is unspecified"],
        counterexample=["present a faithful cache model where the peak occurs away from 1.4×N_active"],
        allowed=["unproved optimum-location claim", "source-scoped optimization proposition"],
        forbidden=["proved exact optimum theorem", "hardware-general law"],
        open_questions=["what exact collision model yields the 1.4 constant?", "is 1.4 asymptotic, empirical, or illustrative?"],
        strong_terms=["倒U型", "最大值"],
        confidence=0.85,
    ),
    "T11": proposition_spec(
        path="统一函数总表/0021-T11-生存域函数.md",
        ranges=[(18, 20), (54, 69)],
        original_claim="系统只能在中间存活，存在上下界约束。",
        controlled="Within the source framework, T11 asserts a theorem-style bounded survival-domain claim: survival is limited to an interior region where the required factors remain nonzero; this remains an unproved formal proposition under the current source text.",
        subject="T11 / survival domain",
        predicate="claims bounded survival region constraints inside the source model",
        formal_object_type="FORMAL_PROPOSITION",
        scope="source-defined internal multiplicative model only",
        boundary=["the domain and bounds are not typed", "the phrase 'middle' is qualitative rather than formally specified"],
        failure=["a faithful typed reading permits survival on a boundary or disconnected region", "upper/lower bounds are defined differently under plausible interpretations"],
        counterexample=["construct a typed model consistent with the source symbols where survival occurs outside the claimed interior band"],
        allowed=["unproved bounded-survival proposition", "source-scoped interior-survival claim"],
        forbidden=["proved survival theorem", "fully specified boundary-value result"],
        open_questions=["what are the exact upper and lower bound variables of Ω_survive?"],
        strong_terms=["上下界约束"],
        confidence=0.84,
    ),
    "T12": defn_spec(
        path="统一函数总表/0022-T12-信息门效率统一.md",
        ranges=[(18, 20), (54, 69)],
        original_claim="信息门效率存在共享度倒 U 最优，完全同质化会使效率趋近于零。",
        controlled="Within the source framework, T12 introduces a source-scoped gate-efficiency score shaped by shared information and homogeneity, but the current text does not provide the typed information-theoretic setup needed to certify an exact inverted-U optimum.",
        subject="T12 / gate efficiency",
        predicate="describes a score-like gate-efficiency quantity that decreases under full homogeneity",
        formal_object_type="NATURAL_LANGUAGE_CANDIDATE",
        scope="framework-internal efficiency score only",
        boundary=["the homogeneity function is not defined", "the exact optimum structure is asserted but not derived here"],
        failure=["different homogeneity measures imply different efficiency curves", "the gate variable G is untyped"],
        counterexample=["show a source-compatible homogeneity rule where efficiency is monotone instead of inverted-U"],
        allowed=["efficiency score candidate", "source-scoped anti-homogeneity intuition"],
        forbidden=["proved exact inverted-U theorem", "strict metric"],
        open_questions=["what definition of H_homogeneity(G) makes the curve shape determinate?"],
        strong_terms=["统一", "倒U最优"],
        logic_status="SCORING_RULE_UNDERDEFINED",
        formalization_status="INSUFFICIENTLY_TYPED_SCORE",
        proof_status="NOT_APPLICABLE_SCORE_DEFINITION",
        confidence=0.78,
    ),
}


ESCALATION_SPECS: dict[str, dict[str, Any]] = {
    "T4": {
        "category": "TRANSFORMATION_EQUIVALENCE",
        "question": "Does the source support an exact equivalence transform between ignition and survival-probability formulations, or only a heuristic reformulation?",
        "interpretations": [
            "Exact equivalence: the transform preserves truth conditions and problem structure bidirectionally.",
            "Heuristic mapping: the transform only offers an intuition-level re-expression without exact preservation proof.",
        ],
        "evidence": [
            "Object text gives slogan-level substitutions but no explicit transform function, inverse, or preservation proof.",
            "The source language says 可以转换, which can be read as either exact or heuristic depending on formalization.",
        ],
    },
    "T10": {
        "category": "OPTIMUM_EQUIVALENCE",
        "question": "Is the source's 1.4×N_active peak claim an exact theorem under a specific cache model, or only an illustrative heuristic optimum?",
        "interpretations": [
            "Exact theorem: a fully specified collision model yields a provable optimum near 1.4×N_active.",
            "Illustrative heuristic: 1.4 is an empirically convenient or handwavy constant without a uniquely fixed model.",
        ],
        "evidence": [
            "The object asserts the constant but does not state the objective function or admissible cache model.",
            "Different plausible cache models could shift the maximizing constant materially.",
        ],
    },
}


def build_review_record(oid: str, spec: dict[str, Any], obj: dict[str, Any]) -> dict[str, Any]:
    rel_path = spec["legacy_path"]
    anchors = anchor_objects(rel_path, spec["source_ranges"])
    source_ref = parse_embedded_source_reference(rel_path)
    return {
        "record_id": f"080-{oid}-v1",
        "stable_id": oid,
        "legacy_id": oid,
        "legacy_path": rel_path,
        "legacy_blob_sha": sha256_path(ROOT / rel_path),
        "reviewed_at": utc8_now(),
        "reviewer_model_class": MODEL_CLASS,
        "review_method": REVIEW_METHOD,
        "review_status": "SOURCE_TEXT_SEMANTICALLY_ADJUDICATED",
        "coverage_eligible": True,
        "source_files_read": [rel_path],
        "source_reference_path": source_ref,
        "source_line_anchors": anchors,
        "direct_source_status": "EMBEDDED_SOURCE_RECOVERY_PRESENT" if source_ref else "LEGACY_BODY_ONLY",
        "original_claim_verbatim_or_precise_paraphrase": spec["original_claim"],
        "controlled_semantic_proposition": spec["controlled"],
        "subject": spec["subject"],
        "predicate_or_relation": spec["predicate"],
        "quantifiers": spec["quantifiers"],
        "modality": spec["modality"],
        "premises": spec["premises"],
        "hidden_premises": spec["hidden_premises"],
        "scope": spec["scope"],
        "boundary_conditions": spec["boundary"],
        "failure_conditions": spec["failure"],
        "counterexample_requirements": spec["counterexample"],
        "formal_object_type": spec["formal_object_type"],
        "claim_type": spec["claim_type"],
        "logic_form": spec["logic_form"],
        "logic_status": spec["logic_status"],
        "logic_risk_flags": [spec["logic_status"]] if spec["logic_status"] not in {"SCOPED_DEFINITION", "SCOPED_UPDATE_RULE"} else [],
        "formalization_status": spec["formalization_status"],
        "proof_status": spec["proof_status"],
        "evidence_status": spec["evidence_status"],
        "provenance_status": spec["provenance_status"],
        "related_cases": parse_related_cases(rel_path),
        "dependencies": obj.get("dependencies") or [],
        "strong_terms_found": spec["strong_terms"],
        "allowed_wording": spec["allowed"],
        "forbidden_wording": spec["forbidden"],
        "open_questions": spec["open_questions"],
        "highest_model_escalation_required": spec["highest_model_escalation_required"],
        "escalation_reason": spec["escalation_reason"],
        "confidence": spec["confidence"],
        "source_excerpt": excerpt(rel_path, spec["source_ranges"]),
        "current_version": True,
        "superseded_by": None,
    }


def build_escalation_record(oid: str, review_record: dict[str, Any]) -> dict[str, Any]:
    spec = ESCALATION_SPECS[oid]
    rel_path = review_record["legacy_path"]
    return {
        "escalation_id": f"080-escalation-{oid}-v1",
        "stable_id": oid,
        "category": spec["category"],
        "status": "PENDING_HIGHEST_MODEL_REVIEW",
        "legacy_path": rel_path,
        "source_files": [rel_path],
        "source_line_anchors": review_record["source_line_anchors"],
        "original_claim": review_record["original_claim_verbatim_or_precise_paraphrase"],
        "candidate_interpretations": spec["interpretations"],
        "known_evidence": spec["evidence"],
        "question_for_highest_model": spec["question"],
        "forbidden_mechanical_actions": [
            "do not edit legacy source files",
            "do not mass-reclassify adjacent objects",
            "do not merge pull requests",
        ],
        "created_at": utc8_now(),
    }


def refresh_status_from_reviews(
    queue_rows: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    review_map = {row["stable_id"]: row for row in review_rows if row.get("current_version", True)}
    refreshed: list[dict[str, Any]] = []
    for row in queue_rows:
        review = review_map.get(row["stable_id"])
        if review:
            row = dict(row)
            row["status"] = "COMPLETED_ACCEPTED"
            row["review_record_id"] = review["record_id"]
            row["last_updated_at"] = review["reviewed_at"]
        refreshed.append(row)
    return refreshed


def write_reports(queue_rows: list[dict[str, Any]], review_rows: list[dict[str, Any]], escalation_rows: list[dict[str, Any]]) -> None:
    review_map = {row["stable_id"]: row for row in review_rows}
    reviewed = [row for row in queue_rows if row["status"] == "COMPLETED_ACCEPTED"]
    type_counts = Counter(review_map[row["stable_id"]]["formal_object_type"] for row in reviewed)
    claim_counts = Counter(review_map[row["stable_id"]]["claim_type"] for row in reviewed)
    logic_risks = sum(1 for row in reviewed if review_map[row["stable_id"]]["logic_risk_flags"])
    incomplete = sum(
        1
        for row in reviewed
        if review_map[row["stable_id"]]["formalization_status"]
        not in {"FORMALLY_COMPLETE", "FULLY_FORMALIZED"}
    )
    remaining = [row for row in queue_rows if row["status"] != "COMPLETED_ACCEPTED"]
    next_pending = remaining[0]["stable_id"] if remaining else "NONE"

    report = f"""# 080 Full Semantic Adjudication Report

- status: `{STATUS}`
- model_class: `{MODEL_CLASS}`
- branch: `{BRANCH}`
- base_head: `{BASE_HEAD}`
- fixed_queue_total: `{len(queue_rows)}`
- newly_completed_this_run: `{len(reviewed)}`
- cumulative_verified_registry: `{5 + len(reviewed)}/622`
- remaining_pending: `{len(remaining)}`
- highest_model_escalations: `{len(escalation_rows)}`

## Batch 1

- completed_batch: `1`
- ids: `{", ".join(row["stable_id"] for row in reviewed)}`
- type_counts: `{dict(sorted(type_counts.items()))}`
- claim_counts: `{dict(sorted(claim_counts.items()))}`
- logic_risk_count: `{logic_risks}`
- formalization_incomplete_count: `{incomplete}`

## Resume

- next_pending_stable_id: `{next_pending}`
- next_pending_batch: `{remaining[0]["assigned_batch"] if remaining else "NONE"}`
- only resume from queue rows with `PENDING` or `IN_PROGRESS_STALE`
- do not recount any reviewed object whose `legacy_blob_sha` is unchanged
- if a source blob changes, append a new versioned adjudication row and mark the previous one superseded
"""
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "080-full-semantic-adjudication-report-20260713.md").write_text(report, encoding="utf-8")

    esc_lines = ["# 080 Highest Model Escalation Summary", ""]
    if escalation_rows:
        for row in escalation_rows:
            esc_lines.append(f"- {row['stable_id']}: {row['category']} — {row['question_for_highest_model']}")
    else:
        esc_lines.append("- none")
    (REPORTS / "080-highest-model-escalation-summary-20260713.md").write_text("\n".join(esc_lines) + "\n", encoding="utf-8")

    resume = f"""# 080 Resume Instructions

- branch: `{BRANCH}`
- status: `{STATUS}`
- next_pending_stable_id: `{next_pending}`
- next_pending_batch: `{remaining[0]["assigned_batch"] if remaining else "NONE"}`
- queue_file: `data/foundation/work-queues/080-semantic-review-queue.jsonl`
- adjudication_file: `data/foundation/adjudications/080-source-text-adjudications.jsonl`
- escalation_file: `data/foundation/escalations/080-highest-model-queue.jsonl`
- run_state: `data/foundation/adjudications/080-run-state.json`
- resume rule: process only `PENDING` or `IN_PROGRESS_STALE`; never overwrite an unchanged accepted review
"""
    (REPORTS / "080-resume-instructions-20260713.md").write_text(resume, encoding="utf-8")


def write_run_state(queue_rows: list[dict[str, Any]], review_rows: list[dict[str, Any]], escalation_rows: list[dict[str, Any]]) -> None:
    reviewed = [row for row in queue_rows if row["status"] == "COMPLETED_ACCEPTED"]
    remaining = [row for row in queue_rows if row["status"] != "COMPLETED_ACCEPTED"]
    review_map = {row["stable_id"]: row for row in review_rows}
    type_counts = Counter(review_map[row["stable_id"]]["formal_object_type"] for row in reviewed)
    claim_counts = Counter(review_map[row["stable_id"]]["claim_type"] for row in reviewed)
    logic_risk_count = sum(1 for row in reviewed if review_map[row["stable_id"]]["logic_risk_flags"])
    run_state = {
        "task_id": TASK_ID,
        "source_task": "IGNITION-20260709-079",
        "status": STATUS,
        "updated_at": utc8_now(),
        "reviewer_model_class": MODEL_CLASS,
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "fixed_queue_total": len(queue_rows),
        "completed_valid_reviews_this_task": len(reviewed),
        "carried_verified_from_079": 5,
        "cumulative_verified_registry_reviews": 5 + len(reviewed),
        "remaining_pending": len(remaining),
        "next_pending_stable_id": remaining[0]["stable_id"] if remaining else None,
        "next_pending_batch": remaining[0]["assigned_batch"] if remaining else None,
        "batch_size_limit": 25,
        "completed_batches": len({row["assigned_batch"] for row in reviewed}),
        "records_since_last_push": len(reviewed) % 100,
        "push_interval": 100,
        "quality_audit_interval": 100,
        "quality_audit_completed_windows": 0,
        "highest_model_escalations": len(escalation_rows),
        "highest_model_escalation_ids": [row["stable_id"] for row in escalation_rows],
        "reviewed_type_counts": dict(sorted(type_counts.items())),
        "reviewed_claim_type_counts": dict(sorted(claim_counts.items())),
        "logic_risk_count": logic_risk_count,
        "legacy_tables_modified": False,
        "getnote_reasoning_calls": 0,
        "prs_merged": 0,
    }
    dump_json(RUN_STATE_PATH, run_state)


def build() -> None:
    objects = load_objects()
    queue_rows = base_queue()
    review_rows = [build_review_record(oid, spec, objects[oid]) for oid, spec in FIRST_BATCH_SPECS.items()]
    for row in review_rows:
        if row["stable_id"] in ESCALATION_SPECS:
            row["highest_model_escalation_required"] = True
            row["escalation_reason"] = ESCALATION_SPECS[row["stable_id"]]["question"]
    escalation_rows = [build_escalation_record(oid, row) for oid, row in {r["stable_id"]: r for r in review_rows}.items() if oid in ESCALATION_SPECS]
    queue_rows = refresh_status_from_reviews(queue_rows, review_rows)
    dump_jsonl(ADJ_PATH, review_rows)
    dump_jsonl(ESCALATION_PATH, escalation_rows)
    dump_jsonl(QUALITY_PATH, [])
    dump_jsonl(QUEUE_PATH, queue_rows)
    write_run_state(queue_rows, review_rows, escalation_rows)
    write_reports(queue_rows, review_rows, escalation_rows)


def validate() -> None:
    import jsonschema

    queue_rows = load_jsonl(QUEUE_PATH)
    review_rows = load_jsonl(ADJ_PATH)
    escalation_rows = load_jsonl(ESCALATION_PATH)
    quality_rows = load_jsonl(QUALITY_PATH)
    run_state = json.loads(RUN_STATE_PATH.read_text(encoding="utf-8"))
    source_schema = json.loads((SCHEMAS / "source-text-adjudication.schema.json").read_text(encoding="utf-8"))
    escalation_schema = json.loads((SCHEMAS / "highest-model-escalation.schema.json").read_text(encoding="utf-8"))

    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    for row in review_rows:
        jsonschema.validate(row, source_schema)
    for row in escalation_rows:
        jsonschema.validate(row, escalation_schema)

    check("queue:617", len(queue_rows) == 617, f"actual={len(queue_rows)}")
    check("queue:stable_id_unique", len({row['stable_id'] for row in queue_rows}) == 617)
    check("queue:first_batch_25", sum(row["status"] == "COMPLETED_ACCEPTED" for row in queue_rows) == 25)
    check("reviews:25", len(review_rows) == 25, f"actual={len(review_rows)}")
    check("reviews:unique_ids", len({row["stable_id"] for row in review_rows}) == 25)
    check("reviews:all_full_source", all(row["review_method"] == REVIEW_METHOD for row in review_rows))
    check("reviews:no_079_overlap", not ({"Y1", "T2", "T16", "D220", "D598"} & {row["stable_id"] for row in review_rows}))
    check("reviews:anchors_present", all(row["source_line_anchors"] and row["source_excerpt"] for row in review_rows))
    check("escalations:subset", {row["stable_id"] for row in escalation_rows} <= {row["stable_id"] for row in review_rows})
    check("quality:empty_before_100", len(quality_rows) == 0)
    check("run_state:counts", run_state["completed_valid_reviews_this_task"] == 25 and run_state["remaining_pending"] == 592)
    check("run_state:cumulative", run_state["cumulative_verified_registry_reviews"] == 30)
    check("legacy:tables_unchanged", __import__("subprocess").run(["git", "diff", "--quiet", BASE_HEAD, "--", "统一函数总表", "统一案例总表"], cwd=ROOT).returncode == 0)

    for name, ok, detail in checks:
        print(("PASS" if ok else "FAIL"), name, detail)
    passed = sum(ok for _, ok, _ in checks)
    print(f"CHECKS_TOTAL={len(checks)} CHECKS_PASSED={passed} CHECKS_FAILED={len(checks)-passed}")
    if passed != len(checks):
        raise SystemExit(1)
    print("ALL_080_SOURCE_TEXT_ADJUDICATION_CHECKS_VALID")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        build()
    validate()
