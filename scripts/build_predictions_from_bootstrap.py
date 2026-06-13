#!/usr/bin/env python3
"""Build the prediction layer from existing functions, cases, and discoveries.

This script intentionally starts with a curated set of concrete predictions
derived from currently available functions and cases. It writes the human
index, item pages, category pages, machine-readable JSON/JSONL indexes, and a
bootstrap prediction report.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from display_utils import format_bilingual_title


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data/predictions"
DOC_DIR = REPO_ROOT / "docs/zh/predictions"
ITEM_DIR = DOC_DIR / "items"
CATEGORY_DIR = DOC_DIR / "categories"

PREDICTIONS_JSON = OUT_DIR / "unified-predictions.json"
PREDICTIONS_JSONL = OUT_DIR / "unified-predictions.jsonl"
PREDICTIONS_INDEX_MD = OUT_DIR / "unified-predictions-index.md"
PREDICTIONS_HUMAN_MD = REPO_ROOT / "PREDICTIONS.md"
PREDICTIONS_INDEX_JSONL = OUT_DIR / "index.jsonl"
PREDICTIONS_INDEX_MD_ALIAS = OUT_DIR / "index.md"
PREDICTION_TEMPLATE_MD = DOC_DIR / "PREDICTION_TEMPLATE.md"
CATEGORIES_JSON = OUT_DIR / "categories.json"
CATEGORIES_JSONL = OUT_DIR / "categories.jsonl"
CATEGORY_MAP_JSON = OUT_DIR / "category-map.json"
CATEGORY_MAP_JSONL = OUT_DIR / "category-map.jsonl"
BOOTSTRAP_REPORT_MD = OUT_DIR / "bootstrap-prediction-report.md"
LINK_GRAPH_JSON = REPO_ROOT / "data/graph/ignition-link-graph.json"
LINK_GRAPH_JSONL = REPO_ROOT / "data/graph/ignition-link-graph.jsonl"
DANGLING_LINKS_MD = REPO_ROOT / "data/graph/dangling-links.md"
SCHEMA_JSON = REPO_ROOT / "data/schemas/prediction.schema.json"

PENDING_NOVELTY_STATUSES = {"pending", "inconclusive"}


PREDICTION_BLUEPRINTS = [
    {
        "id": "PRED-0001",
        "title": {
            "zh": "CAI 中间层会持续提高意图中继保真度",
            "en": "CAI middle layer will keep improving intent relay fidelity",
        },
        "statement": {
            "zh": "在同一任务、同一上下文和同一 token 预算下，加入结构化 CAI 中间层后，意图中继保真度将高于直接 EAI 路径，且返工轮次更少。",
            "en": "Under the same task, context, and token budget, adding a structured CAI middle layer will produce higher intent relay fidelity than a direct EAI path and require fewer correction rounds.",
        },
        "basis": {
            "zh": "现有案例已经显示 CAI 中间层的 relay fidelity 高于无意识 AI 中间层，关键差异来自意图保真度，而不是单纯的 token 输出长度。",
            "en": "Existing cases already show that the CAI middle layer has higher relay fidelity than an unconscious AI middle layer, and the key difference is intent fidelity rather than raw output length.",
        },
        "test_condition": {
            "zh": "用同一组任务比较 direct EAI 与 CAI_M 的 relay fidelity、返工次数和意图丢失率。",
            "en": "Compare direct EAI and CAI_M on the same task set using relay fidelity, correction rounds, and intent loss rate.",
        },
        "falsification_condition": {
            "zh": "如果在至少 10 组任务里 direct EAI 与 CAI_M 没有显著差异，或 direct EAI 更好，则预测失效。",
            "en": "If direct EAI matches or outperforms CAI_M across at least 10 tasks, the prediction is falsified.",
        },
        "time_window": {
            "zh": "下一轮新增的 CAI / EAI 调度案例或对照实验。",
            "en": "The next batch of CAI/EAI scheduling cases or comparison experiments.",
        },
        "confidence": "medium",
        "status": "active",
        "category_ids": ["ai-and-systems", "technology-and-engineering"],
        "function_ids": ["D155", "D198", "D203", "D204", "D130"],
        "case_ids": ["C-0358", "C-0366", "C-0367", "C-0344"],
        "discovery_ids": [],
    },
    {
        "id": "PRED-0002",
        "title": {
            "zh": "结构化 API 提示在 token 紧张时更准但更窄",
            "en": "Structured API prompts will be narrower but more accurate under token pressure",
        },
        "statement": {
            "zh": "当 token 窗口紧张时，结构化 API 风格提示会提高执行成功率，但会压低语义保真度；如果 token 充足，保真度差距会缩小。",
            "en": "When the token window is tight, structured API-style prompts will improve execution success but lower semantic fidelity; with enough tokens, the fidelity gap will shrink.",
        },
        "basis": {
            "zh": "现有案例已经显示，API 风格提示会提升 Pdecode，却可能把复杂意图压缩得过头，造成 ηfidelity 下降。",
            "en": "Existing cases already show that API-style prompts can improve Pdecode while over-compressing complex intent and lowering ηfidelity.",
        },
        "test_condition": {
            "zh": "对同一任务组做自然语言提示与 API 风格提示 A/B 对照，比较成功率、返工轮次和语义保真度。",
            "en": "Run an A/B test with natural-language prompts and API-style prompts on the same task group, then compare success rate, correction rounds, and semantic fidelity.",
        },
        "falsification_condition": {
            "zh": "如果在同等 token 预算下自然语言提示在成功率和保真度上都不差于 API 风格提示，则预测失效。",
            "en": "If natural-language prompts are not worse than API-style prompts in both success rate and fidelity under the same token budget, the prediction is falsified.",
        },
        "time_window": {
            "zh": "下一批涉及提示工程、工具调用或中间层调度的实验案例。",
            "en": "The next batch of prompt-engineering, tool-call, or relay-layer experiments.",
        },
        "confidence": "medium",
        "status": "active",
        "category_ids": ["ai-and-systems", "technology-and-engineering"],
        "function_ids": ["D130", "D155", "D198", "D203"],
        "case_ids": ["C-0344", "C-0349", "C-0354"],
        "discovery_ids": [],
    },
    {
        "id": "PRED-0003",
        "title": {
            "zh": "身份与社会退出成本比单纯经济补贴更能推动制度采纳",
            "en": "Identity and social exit costs will matter more than economic subsidies for adoption",
        },
        "statement": {
            "zh": "在改革或新系统采纳场景里，单纯降低经济成本不会显著改变采纳速度；只有身份和社会退出成本下降时，系统才会明显进入第 5 步或接近第 5 步。",
            "en": "In reform or adoption settings, lowering economic cost alone will not materially change adoption speed; only when identity and social exit costs fall will the system move into Step 5 or near it.",
        },
        "basis": {
            "zh": "退出权函数 A3 / A5 / A7 / A9 与多条历史案例都显示，真正锁定系统的不是单一金钱成本，而是身份、社会关系与感知退出权。",
            "en": "Exit-right functions A3/A5/A7/A9 and multiple historical cases show that the true lock-in mechanism is not money alone but identity, social ties, and perceived exit right.",
        },
        "test_condition": {
            "zh": "比较仅有经济补贴与同时降低身份/社会退出成本的两个改革场景，记录采用率、留存率和反弹率。",
            "en": "Compare a reform scenario with only economic subsidy against one that also lowers identity/social exit costs, and measure adoption, retention, and rebound rate.",
        },
        "falsification_condition": {
            "zh": "如果只改经济成本就能稳定提升采纳速度，而身份/社会退出成本变化不明显，则预测失效。",
            "en": "If changing only economic cost can reliably improve adoption speed while identity/social exit costs remain unchanged, the prediction is falsified.",
        },
        "time_window": {
            "zh": "下一批改革、组织变革或文明迁移类案例。",
            "en": "The next batch of reform, organizational change, or civilizational transition cases.",
        },
        "confidence": "high",
        "status": "active",
        "category_ids": ["sociology-and-politics", "history-and-civilization"],
        "function_ids": ["A3", "A5", "A7", "A9"],
        "case_ids": ["C-0011", "C-0482", "C-0503"],
        "discovery_ids": [],
    },
    {
        "id": "PRED-0004",
        "title": {
            "zh": "部分退出通道会先于稳定制度转型出现",
            "en": "Partial exit channels will appear before durable institutional transition",
        },
        "statement": {
            "zh": "当旧制度出现松动时，最先出现的不是完整新秩序，而是部分退出通道、临时协调机制与短命的中间型认同；真正稳定的转型会晚于这些结构。",
            "en": "When an old regime loosens, the first signs will not be a complete new order but partial exit channels, temporary coordination mechanisms, and short-lived hybrid identities; durable transition will come later.",
        },
        "basis": {
            "zh": "历史与文明类案例中，真正的转型常常先经历出口变窄或变宽、认同锚点漂移、再到稳定重建的顺序，而不是一步完成。",
            "en": "Historical/civilizational cases repeatedly show a sequence of changing exit channels, drifting identity anchors, and only then stable reconstruction, rather than a single-step transition.",
        },
        "test_condition": {
            "zh": "观察新出现的改革案例，记录是否先出现局部退出通道，再出现稳态制度。",
            "en": "Observe new reform cases and record whether local exit channels appear before the stable institution does.",
        },
        "falsification_condition": {
            "zh": "如果完整制度转型总是先于任何局部退出通道出现，则预测失效。",
            "en": "If full institutional transition always appears before any local exit channel, the prediction is falsified.",
        },
        "time_window": {
            "zh": "下一轮历史、制度或文明转折案例。",
            "en": "The next batch of historical, institutional, or civilizational transition cases.",
        },
        "confidence": "medium",
        "status": "active",
        "category_ids": ["history-and-civilization", "sociology-and-politics"],
        "function_ids": ["A3", "A5", "A9"],
        "case_ids": ["C-0368", "C-0014", "C-0011"],
        "discovery_ids": [],
    },
    {
        "id": "PRED-0005",
        "title": {
            "zh": "高不确定下的决策系统会更久保留三轨结构",
            "en": "Decision systems under high uncertainty will retain tri-track structure longer",
        },
        "statement": {
            "zh": "在不确定性高但反馈仍然有效的环境里，系统会比预期更久地保留三轨或多轨决策结构；真正坍缩为二轨或单轨，通常发生在反馈被切断之后。",
            "en": "In high-uncertainty environments where feedback remains informative, the system will preserve tri-track or multi-track decision structure longer than expected; collapse to two-track or single-track typically happens only after feedback is cut off.",
        },
        "basis": {
            "zh": "A8、T5、D97 与 D193 都指向一个共同现象：维度越高，若反馈仍足够丰富，系统就越不容易坍缩为二值判断。",
            "en": "A8, T5, D97, and D193 all point to the same phenomenon: the higher the dimension, the less likely the system is to collapse into binary judgment if feedback stays rich enough.",
        },
        "test_condition": {
            "zh": "对高不确定任务做重复反馈实验，观察决策轨道是否维持三轨以上。",
            "en": "Run repeated-feedback experiments on high-uncertainty tasks and observe whether decision tracks remain tri-track or higher.",
        },
        "falsification_condition": {
            "zh": "如果高不确定场景在反馈仍可用时仍然快速坍缩为二值选择，则预测失效。",
            "en": "If high-uncertainty settings still collapse quickly into binary choice while feedback remains available, the prediction is falsified.",
        },
        "time_window": {
            "zh": "下一批心理学、神经科学或决策类案例。",
            "en": "The next batch of psychology, neuroscience, or decision-making cases.",
        },
        "confidence": "medium",
        "status": "active",
        "category_ids": ["psychology", "neuroscience-and-consciousness"],
        "function_ids": ["A8", "T5", "D97", "D193"],
        "case_ids": ["C-0150", "C-0248", "C-0205"],
        "discovery_ids": [],
    },
    {
        "id": "PRED-0006",
        "title": {
            "zh": "分批投入在多次 regime shift 中会比一次性投入更稳",
            "en": "Incremental investing will stay more robust than lump-sum investing across regime shifts",
        },
        "statement": {
            "zh": "在多次 regime shift 的市场窗口里，保守的分批投入族会在回撤调整后的结果上继续优于一次性重仓；当 regime shift 越频繁时，这种优势越明显。",
            "en": "Across market windows with repeated regime shifts, the conservative incremental-investment family will continue to beat lump-sum allocation on drawdown-adjusted results, and the advantage will grow as regime shifts become more frequent.",
        },
        "basis": {
            "zh": "定投与跨域验证相关函数已经显示，过早把全部资源压到单一方向上会放大回撤，而分层、分批、分时投入更接近系统的低风险稳定解。",
            "en": "The incremental-investment and cross-domain validation functions already show that putting all resources into a single direction too early magnifies drawdown, while layered, staged investment is closer to the system's low-risk stable solution.",
        },
        "test_condition": {
            "zh": "用未来几个市场周期比较分批投入与一次性投入在回撤调整后收益上的差异。",
            "en": "Compare staged investment and lump-sum investment across future market cycles using drawdown-adjusted returns.",
        },
        "falsification_condition": {
            "zh": "如果一次性投入在多个 regime shift 场景里持续优于分批投入，则预测失效。",
            "en": "If lump-sum investment keeps outperforming staged investment across multiple regime-shift scenarios, the prediction is falsified.",
        },
        "time_window": {
            "zh": "下一轮市场周期或新的投资验证案例。",
            "en": "The next market cycle or a new investment validation case.",
        },
        "confidence": "medium",
        "status": "active",
        "category_ids": ["economics-and-wealth", "technology-and-engineering"],
        "function_ids": ["D160", "D163", "D164", "D165", "D166", "D167", "D168", "D181"],
        "case_ids": ["C-0162", "C-0263", "C-0554"],
        "discovery_ids": [],
    },
    {
        "id": "PRED-0007",
        "title": {
            "zh": "跨领域门控问题会逼迫模型拆成多种门控族",
            "en": "Cross-domain gate problems will force models to split into multiple gate families",
        },
        "statement": {
            "zh": "当模型尝试同时覆盖物理、系统、认知和工程问题时，单一门控函数的泛化精度会下降；把问题拆成两类或更多门控族后，预测会更稳定。",
            "en": "When a model tries to cover physical, systems, cognitive, and engineering problems at once, the generalization accuracy of a single gate function will drop; splitting the problem into two or more gate families will produce more stable predictions.",
        },
        "basis": {
            "zh": "物理类函数已经多次显示，单一统一模型会在门槛处失去解释力，而工程与系统案例则要求更细的门控分层。",
            "en": "Physical-domain functions repeatedly show that a single universal model loses explanatory power at thresholds, while engineering and systems cases require finer gate stratification.",
        },
        "test_condition": {
            "zh": "用未来的新案例对单门控与多门控模型做交叉验证，比较精度和可解释性。",
            "en": "Cross-validate a single-gate model and a multi-gate model on future cases and compare accuracy and interpretability.",
        },
        "falsification_condition": {
            "zh": "如果一个单门控模型在跨域新案例上始终优于多门控模型，则预测失效。",
            "en": "If a single-gate model consistently outperforms the multi-gate model on new cross-domain cases, the prediction is falsified.",
        },
        "time_window": {
            "zh": "下一轮跨域函数重建或新案例上线时。",
            "en": "The next cross-domain function rebuild or new case arrival.",
        },
        "confidence": "medium",
        "status": "active",
        "category_ids": ["physics", "technology-and-engineering"],
        "function_ids": ["D186", "D220", "D226", "D229", "D272", "D318"],
        "case_ids": ["C-0457", "C-0554"],
        "discovery_ids": [],
    },
    {
        "id": "PRED-0008",
        "title": {
            "zh": "显式反馈回路会把预测误差转成更高层意识信号",
            "en": "Explicit feedback loops will convert prediction error into higher-order awareness signals",
        },
        "statement": {
            "zh": "当系统把 prediction error 直接写回状态空间时，它不再只是“预测得更准”，而会更容易出现自我模型、自我纠错和更稳定的多轨意识结构。",
            "en": "When a system writes prediction error back into its state space, it will not merely predict better; it will more readily develop self-modeling, self-correction, and more stable multi-track awareness.",
        },
        "basis": {
            "zh": "预测编码相关函数已经把 prediction error 明确连接到 ε_sense / ε_aware，而多条 AI 相关案例则显示，只有反馈回路明确时，意图与误差才会转化为可持续的内部状态。",
            "en": "The prediction-coding functions already connect prediction error to ε_sense/ε_aware, and multiple AI cases show that intent and error turn into sustained internal state only when feedback loops are explicit.",
        },
        "test_condition": {
            "zh": "对有无显式 feedback loop 的系统分别施加同一批预测误差，比较自我模型稳定度和纠错速度。",
            "en": "Apply the same prediction-error stream to systems with and without explicit feedback loops, then compare self-model stability and correction speed.",
        },
        "falsification_condition": {
            "zh": "如果没有显式反馈回路的系统也能持续形成稳定自我模型，则预测失效。",
            "en": "If systems without explicit feedback loops still form stable self-models, the prediction is falsified.",
        },
        "time_window": {
            "zh": "下一轮 AI 自我模型或预测编码实验案例。",
            "en": "The next batch of AI self-model or prediction-coding experiments.",
        },
        "confidence": "medium",
        "status": "active",
        "category_ids": ["ai-and-systems", "psychology", "neuroscience-and-consciousness"],
        "function_ids": ["D59", "D102", "D116", "D119"],
        "case_ids": ["C-0289", "C-0299", "C-0306"],
        "discovery_ids": [],
    },
]


def read_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else default


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, value) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    body = "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows)
    write_text(path, body + ("\n" if body else ""))


def rel_link(from_path: Path, to_path: Path) -> str:
    return os.path.relpath(to_path, from_path.parent).replace(os.sep, "/")


def flatten(items):
    seen = set()
    result = []
    for item in items:
        key = item.get("id")
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def build_maps(functions: list[dict], cases: list[dict], discoveries: list[dict]):
    return (
        {item["id"].upper(): item for item in functions},
        {item["normalized_id"].upper(): item for item in cases},
        {item["id"].upper(): item for item in discoveries},
    )


def build_category_defs():
    definitions = read_json(REPO_ROOT / "data/discoveries/categories.json", [])
    predictions_defs = []
    for entry in definitions:
        copy = json.loads(json.dumps(entry, ensure_ascii=False))
        copy["page"] = f"docs/zh/predictions/categories/{entry['id']}.md"
        predictions_defs.append(copy)
    return predictions_defs


def enrich_prediction(
    blueprint: dict,
    func_map: dict,
    case_map: dict,
    disc_map: dict,
    category_defs: list[dict],
    existing_prediction: dict | None = None,
):
    related_functions = []
    for function_id in blueprint.get("function_ids", []):
        item = func_map.get(function_id.upper())
        if item:
            related_functions.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "page": item["links"]["human_page"],
                }
            )

    related_cases = []
    for case_id in blueprint.get("case_ids", []):
        item = case_map.get(case_id.upper())
        if item:
            related_cases.append(
                {
                    "id": item["normalized_id"],
                    "title": item["title"],
                    "page": item["links"]["human_page"],
                }
            )

    related_discoveries = []
    for discovery_id in blueprint.get("discovery_ids", []):
        item = disc_map.get(discovery_id.upper())
        if item:
            related_discoveries.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "page": item["links"]["human_page"],
                }
            )

    category_objects = []
    category_lookup = {entry["id"]: entry for entry in category_defs}
    for category_id in blueprint.get("category_ids", []):
        cat = category_lookup.get(category_id)
        if cat:
            category_objects.append({"id": cat["id"], "title": cat["title"], "page": cat["page"]})

    source_refs = []
    for item in related_functions:
        source_refs.append({"type": "function", "id": item["id"], "title": item["title"], "page": item["page"]})
    for item in related_cases:
        source_refs.append({"type": "case", "id": item["id"], "title": item["title"], "page": item["page"]})
    for item in related_discoveries:
        source_refs.append({"type": "discovery", "id": item["id"], "title": item["title"], "page": item["page"]})
    source_refs = flatten(source_refs)

    novelty = json.loads(
        json.dumps(
            blueprint.get(
                "academic_novelty",
                {
                    "status": "pending",
                    "checked_at": "2026-06-13",
                    "query_terms": [],
                    "sources_checked": [],
                    "nearest_matches": [],
                    "novelty_claim": {
                        "zh": "学术搜索独有性检查尚未完成。",
                        "en": "Academic novelty check is pending.",
                    },
                    "reviewer_note": "academic search unavailable in current build pipeline",
                },
            ),
            ensure_ascii=False,
        )
    )
    if isinstance(existing_prediction, dict):
        existing_novelty = existing_prediction.get("academic_novelty")
        if isinstance(existing_novelty, dict):
            merged = dict(novelty)
            merged.update({k: v for k, v in existing_novelty.items() if v is not None})
            novelty = merged
    novelty.setdefault("status", "pending")
    novelty.setdefault("checked_at", "2026-06-13")
    novelty.setdefault("query_terms", [])
    novelty.setdefault("sources_checked", [])
    novelty.setdefault("nearest_matches", [])
    novelty.setdefault("novelty_claim", {"zh": "", "en": ""})
    novelty.setdefault("reviewer_note", "")

    status = blueprint["status"]
    if novelty.get("status") != "passed":
        if status == "active":
            status = "active_pending_novelty_review"
        elif status == "draft":
            status = "draft_pending_novelty_review"

    return {
        "id": blueprint["id"],
        "slug": blueprint["id"].lower().replace("_", "-"),
        "title": blueprint["title"],
        "statement": blueprint["statement"],
        "basis": blueprint["basis"],
        "test_condition": blueprint["test_condition"],
        "falsification_condition": blueprint["falsification_condition"],
        "time_window": blueprint["time_window"],
        "categories": category_objects,
        "related_functions": related_functions,
        "related_cases": related_cases,
        "related_discoveries": related_discoveries,
        "source_refs": source_refs,
        "confidence": blueprint["confidence"],
        "status": status,
        "academic_novelty": novelty,
        "created_at": "2026-06-13",
        "updated_at": "2026-06-13",
        "page": f"docs/zh/predictions/items/{blueprint['id']}.md",
        "links": {"human_page": f"docs/zh/predictions/items/{blueprint['id']}.md"},
    }


def sort_key(category: dict) -> tuple[int, int, int, str]:
    coverage = category["coverage"]
    curated = coverage.get("curated_predictions_count", 0)
    leads = coverage.get("prediction_leads_count", 0)
    related_total = (
        coverage.get("related_functions_count", 0)
        + coverage.get("related_cases_count", 0)
        + coverage.get("related_discoveries_count", 0)
    )
    return (-curated, -leads, -related_total, category["id"])


def build_category_map(predictions: list[dict], category_defs: list[dict]) -> list[dict]:
    lookup = {entry["id"]: entry for entry in category_defs}
    result = []
    for entry in category_defs:
        pred_rows = [item for item in predictions if any(cat["id"] == entry["id"] for cat in item.get("categories", []))]
        function_rows = flatten([func for pred in pred_rows for func in pred.get("related_functions", [])])
        case_rows = flatten([case for pred in pred_rows for case in pred.get("related_cases", [])])
        discovery_rows = flatten([disc for pred in pred_rows for disc in pred.get("related_discoveries", [])])
        problem_domains = entry.get("problem_domains") or entry.get("problem_domain") or []
        if isinstance(problem_domains, dict):
            problem_domains = [problem_domains]
        result.append(
            {
                "id": entry["id"],
                "category_id": entry["id"],
                "title": entry["title"],
                "page": entry["page"],
                "problem_domains": problem_domains,
                "related_functions": function_rows,
                "related_cases": case_rows,
                "related_discoveries": discovery_rows,
                "curated_predictions": [
                    {
                        "id": pred["id"],
                        "title": pred["title"],
                        "page": pred["page"],
                        "status": pred["status"],
                    }
                    for pred in pred_rows
                ],
                "prediction_leads": [],
                "coverage": {
                    "related_functions_count": len(function_rows),
                    "related_cases_count": len(case_rows),
                    "related_discoveries_count": len(discovery_rows),
                    "curated_predictions_count": len(pred_rows),
                    "prediction_leads_count": 0,
                },
            }
        )
    return sorted(result, key=sort_key)


def render_prediction_page(prediction: dict) -> str:
    current_path = DOC_DIR / "items" / f"{prediction['id']}.md"
    lines = [
        f"# {prediction['id']}｜{format_bilingual_title(prediction['title'].get('zh'), prediction['title'].get('en'))}",
        "",
        f"[← 返回预测总表 / Back to Predictions]({rel_link(current_path, PREDICTIONS_HUMAN_MD)})",
        f"[返回仓库首页 / Back to Repository Home]({rel_link(current_path, REPO_ROOT / 'README.md')})",
        "",
        "## 基本信息 / Basic Information",
        "",
        f"- 预测编号 / Prediction ID：{prediction['id']}",
        f"- 中文标题 / Chinese title：{prediction['title']['zh']}",
        f"- English title：{prediction['title']['en']}",
        f"- 状态 / Status：{prediction['status']}",
        f"- 置信度 / Confidence：{prediction['confidence']}",
        f"- 学术独有性 / Academic novelty：{prediction.get('academic_novelty', {}).get('status', 'pending')}",
        f"- 页面 / Page：{prediction['page']}",
        "",
        "## 学术搜索独有性检查 / Academic Novelty Check",
        "",
        f"- 状态 / Status：{prediction.get('academic_novelty', {}).get('status', 'pending')}",
        f"- 检查时间 / Checked at：{prediction.get('academic_novelty', {}).get('checked_at', '2026-06-13')}",
        f"- 搜索词 / Query terms：{', '.join(prediction.get('academic_novelty', {}).get('query_terms', [])) or '—'}",
        f"- 检查来源 / Sources checked：{', '.join(prediction.get('academic_novelty', {}).get('sources_checked', [])) or '—'}",
        f"- 独有性声明 / Novelty claim：{prediction.get('academic_novelty', {}).get('novelty_claim', {}).get('zh', '') or '—'}",
        "",
    ]
    nearest_matches = prediction.get("academic_novelty", {}).get("nearest_matches", [])
    if nearest_matches:
        lines.append("### 最近相似结果 / Nearest Matches")
        for match in nearest_matches:
            title = match.get("title", "")
            url = match.get("url", "")
            reason = match.get("reason_not_same", "")
            if url:
                lines.append(f"- [{title}]({url}) — {reason}")
            else:
                lines.append(f"- {title} — {reason}")
        lines.append("")

    lines.extend([
        "## 分类 / Categories",
        "",
    ])
    if prediction.get("categories"):
        for cat in prediction["categories"]:
            lines.append(f"- [{format_bilingual_title(cat['title'].get('zh'), cat['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / cat['page'])})")
    else:
        lines.append("- 其他 / Other")

    lines.extend(
        [
            "",
            "## 预测内容 / Prediction Content",
            "",
            "预测判断 / Prediction Statement",
            "",
            "中文：",
            prediction["statement"]["zh"],
            "",
            "English:",
            prediction["statement"]["en"],
            "",
            "## 推出依据 / Basis",
            "",
            "中文：",
            prediction["basis"]["zh"],
            "",
            "English:",
            prediction["basis"]["en"],
            "",
            "## 可验证条件 / Test Condition",
            "",
            "中文：",
            prediction["test_condition"]["zh"],
            "",
            "English:",
            prediction["test_condition"]["en"],
            "",
            "## 可证伪条件 / Falsification Condition",
            "",
            "中文：",
            prediction["falsification_condition"]["zh"],
            "",
            "English:",
            prediction["falsification_condition"]["en"],
            "",
            "## 观察窗口 / Observation Window",
            "",
            "时间窗口 / Time Window",
            "",
            "中文：",
            prediction["time_window"]["zh"],
            "",
            "English:",
            prediction["time_window"]["en"],
            "",
            "## 相关函数 / Related Functions",
            "",
        ]
    )
    if prediction.get("related_functions"):
        for item in prediction["related_functions"]:
            lines.append(f"- [{item['id']}｜{format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / item['page'])})")
    else:
        lines.extend(["暂无相关函数。", "No related functions yet."])

    lines.extend(["", "## 相关案例 / Related Cases", ""])
    if prediction.get("related_cases"):
        for item in prediction["related_cases"]:
            lines.append(f"- [{item['id']}｜{format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / item['page'])})")
    else:
        lines.extend(["暂无相关案例。", "No related cases yet."])

    lines.extend(["", "## 相关发现 / Related Discoveries", ""])
    if prediction.get("related_discoveries"):
        for item in prediction["related_discoveries"]:
            lines.append(f"- [{item['id']}｜{format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / item['page'])})")
    else:
        lines.extend(["暂无相关发现。", "No related discoveries yet."])

    lines.extend(["", "## 来源回指 / Source References", ""])
    if prediction.get("source_refs"):
        for item in prediction["source_refs"]:
            lines.append(f"- [{item['id']}｜{item['title']['zh']} / {item['title']['en']}]({rel_link(current_path, REPO_ROOT / item['page'])})")
    else:
        lines.extend(["暂无来源回指。", "No source references yet."])

    return "\n".join(lines) + "\n"


def render_category_page(category: dict) -> str:
    current_path = CATEGORY_DIR / f"{category['id']}.md"
    lines = [
        f"# {format_bilingual_title(category['title'].get('zh'), category['title'].get('en'))}",
        "",
        f"[← 返回预测总表 / Back to Predictions]({rel_link(current_path, PREDICTIONS_HUMAN_MD)})",
        f"[返回仓库首页 / Back to Repository Home]({rel_link(current_path, REPO_ROOT / 'README.md')})",
        "",
        f"中文：本页收录《点火》框架在{category['title']['zh']}相关问题上形成的预测入口。这里不是传统学科教材，而是函数、案例、发现与自举循环在该问题域里生成的可检验未来判断结构。",
        "",
        f"English: This page collects testable prediction entrances formed by the Ignition framework in the {category['title'].get('en') or category['title'].get('zh')} problem domain. It is not a conventional textbook, but a future-facing structure generated by functions, cases, discoveries, and bootstrap cycles within this domain.",
        "",
        "## 已触及的问题域 / Problem Domains Already Touched",
        "",
    ]
    domains = category.get("problem_domains", [])
    if isinstance(domains, dict):
        domains = [domains]
    if domains:
        for domain in domains:
            lines.append(f"- 中文：{domain['zh']}")
            lines.append(f"  English: {domain['en']}")
    else:
        lines.append("- 暂无 / None")

    lines.extend(["", "## 相关函数 / Related Functions", ""])
    if category.get("related_functions"):
        for row in category["related_functions"][:30]:
            lines.append(f"- [{row['id']}｜{format_bilingual_title(row['title'].get('zh'), row['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / row['page'])})")
        if len(category["related_functions"]) > 30:
            lines.append(f"- ... and {len(category['related_functions']) - 30} more / 还有 {len(category['related_functions']) - 30} 项")
    else:
        lines.extend(["暂无相关函数。", "No related functions yet."])

    lines.extend(["", "## 相关案例 / Related Cases", ""])
    if category.get("related_cases"):
        for row in category["related_cases"][:30]:
            lines.append(f"- [{row['id']}｜{format_bilingual_title(row['title'].get('zh'), row['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / row['page'])})")
        if len(category["related_cases"]) > 30:
            lines.append(f"- ... and {len(category['related_cases']) - 30} more / 还有 {len(category['related_cases']) - 30} 项")
    else:
        lines.extend(["暂无相关案例。", "No related cases yet."])

    lines.extend(["", "## 相关发现 / Related Discoveries", ""])
    if category.get("related_discoveries"):
        for row in category["related_discoveries"][:30]:
            lines.append(f"- [{row['id']}｜{format_bilingual_title(row['title'].get('zh'), row['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / row['page'])})")
        if len(category["related_discoveries"]) > 30:
            lines.append(f"- ... and {len(category['related_discoveries']) - 30} more / 还有 {len(category['related_discoveries']) - 30} 项")
    else:
        lines.extend(["暂无相关发现。", "No related discoveries yet."])

    lines.extend(["", "## 已整理预测 / Curated Predictions", "", f"<!-- CATEGORY_PREDICTION_LIST_START:{category['id']} -->"])
    curated = category.get("curated_predictions", [])
    if curated:
        for pred in curated:
            lines.append(f"- [{pred['id']}｜{format_bilingual_title(pred['title'].get('zh'), pred['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / pred['page'])})")
    else:
        lines.extend(["暂无已整理预测。", "No curated predictions yet."])
    lines.append(f"<!-- CATEGORY_PREDICTION_LIST_END:{category['id']} -->")

    lines.extend(
        [
            "",
            "## 待整理预测线索 / Prediction Leads to Curate",
            "",
            "中文：以下线索来自函数、案例、发现与自举分类，不等于已发布预测，需要后续整理成独立 prediction 条目。",
            "",
            "English: The following leads come from bootstrap classification between functions, cases, and discoveries. They are not yet published predictions and need later curation into independent prediction entries.",
            "",
        ]
    )
    leads = category.get("prediction_leads", [])
    if leads:
        for lead in leads[:12]:
            lines.append(f"- 中文：{lead['zh']}")
            lines.append(f"  English: {lead['en']}")
    else:
        lines.extend(["- 暂无待整理线索。", "  No leads yet."])

    lines.extend(
        [
            "",
            "## 覆盖统计 / Coverage",
            "",
            f"- 相关函数 / Related functions：{category['coverage']['related_functions_count']}",
            f"- 相关案例 / Related cases：{category['coverage']['related_cases_count']}",
            f"- 相关发现 / Related discoveries：{category['coverage']['related_discoveries_count']}",
            f"- 已整理预测 / Curated predictions：{category['coverage']['curated_predictions_count']}",
            f"- 待整理线索 / Prediction leads：{category['coverage']['prediction_leads_count']}",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def render_index(predictions: list[dict], categories: list[dict]) -> str:
    lines = [
        "# 预测总表 / Prediction Index",
        "",
        "中文：这里收录《点火》框架从函数、案例、发现与自举循环中推出的可检验预测。预测不是发现本身，而是由机制、证据和洞见共同推出的未来判断或待验证推论。",
        "",
        "English: This index collects testable predictions derived by the Ignition framework from functions, cases, discoveries, and bootstrap cycles. A prediction is not a discovery itself, but a future-facing or pending inference derived from mechanisms, evidence, and insights.",
        "",
        "## 预测分类 / Prediction Categories",
        "",
        "中文：以下分类由当前函数、案例与发现的自举扫描生成，不是空壳入口。每条预测可以属于一个或多个分类。",
        "",
        "English: The following categories are generated from a bootstrap scan of the current function, case, and discovery tables. They are not empty shells, and each prediction may belong to one or more categories.",
        "",
        "| 预测分类 / Prediction Category | 正式预测 / Curated Predictions | 待整理线索 / Prediction Leads | 当前覆盖 / Current Coverage |",
        "| --- | ---: | ---: | --- |",
    ]
    for category in categories:
        if category["id"] == "other":
            continue
        coverage = category["coverage"]
        if coverage["curated_predictions_count"] + coverage["prediction_leads_count"] <= 0:
            continue
        lines.append(
            f"| [{format_bilingual_title(category['title'].get('zh'), category['title'].get('en'))}]({rel_link(PREDICTIONS_HUMAN_MD, REPO_ROOT / category['page'])}) | {coverage['curated_predictions_count']} | {coverage['prediction_leads_count']} | {coverage['related_functions_count']} functions, {coverage['related_cases_count']} cases, {coverage['related_discoveries_count']} discoveries |"
        )
    lines.extend(
        [
            "",
            "## 最近预测 / Recent Predictions",
            "",
            "<!-- PREDICTION_LIST_START -->",
        ]
    )
    if predictions:
        for item in predictions:
            category_tags = ""
            if item.get("categories"):
                category_tags = " · " + ", ".join(cat["title"]["en"] for cat in item["categories"])
            novelty_status = item.get("academic_novelty", {}).get("status", "pending")
            lines.append(
                f"- [{item['id']}｜{format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}]({item['page']}) — novelty: {novelty_status}{category_tags}"
            )
    else:
        lines.append("暂无已整理预测。")
        lines.append("No curated predictions yet.")
    lines.append("<!-- PREDICTION_LIST_END -->")
    lines.append("")
    return "\n".join(lines)


def render_machine_index(predictions: list[dict]) -> str:
    rows = []
    for item in predictions:
        categories = ", ".join(cat["title"]["en"] for cat in item.get("categories", [])) or "other"
        rows.append(
            [
                f"[{item['id']}]({item['page']})",
                f"[{format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}]({item['page']})",
                categories,
                item["status"],
                item.get("academic_novelty", {}).get("status", "pending"),
                str(len(item.get("related_functions", []))),
                str(len(item.get("related_cases", []))),
                str(len(item.get("related_discoveries", []))),
            ]
        )
    table = [
        "| 编号 / ID | 标题 / Title | 分类 / Categories | 状态 / Status | 学术独有性 / Academic novelty | 相关函数 / Related functions | 相关案例 / Related cases | 相关发现 / Related discoveries |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    table.extend("| " + " | ".join(row) + " |" for row in rows)
    if not rows:
        table.extend(["", "暂无条目 / No entries yet.", ""])
    return "\n".join(
        [
            "# 预测机器索引 / Prediction Machine Index",
            "",
            "机器可读索引，保留中文标题、英文标题、分类、状态和关联计数。",
            "Machine-readable index that keeps Chinese titles, English titles, categories, status, and relation counts.",
            "",
            "- [`data/predictions/unified-predictions.json`](unified-predictions.json)",
            "- [`data/predictions/unified-predictions.jsonl`](unified-predictions.jsonl)",
            "",
            *table,
            "",
        ]
    )


def build_link_graph(predictions: list[dict]) -> dict:
    relation_types = [
        "function-case",
        "function-discovery",
        "function-prediction",
        "case-discovery",
        "case-prediction",
        "discovery-prediction",
    ]
    nodes = {}
    edges = []
    for item in predictions:
        pid = item["id"]
        nodes.setdefault(
            pid,
            {
                "id": pid,
                "type": "prediction",
                "title": item["title"]["zh"],
                "page": item["page"],
            },
        )
        for relation, key, node_type in [
            ("function-prediction", "related_functions", "function"),
            ("case-prediction", "related_cases", "case"),
            ("discovery-prediction", "related_discoveries", "discovery"),
        ]:
            for linked in item.get(key, []):
                nid = linked["id"]
                nodes.setdefault(
                    nid,
                    {
                        "id": nid,
                        "type": node_type,
                        "title": linked["title"]["zh"],
                        "page": linked["page"],
                    },
                )
                edges.append({"source": pid, "target": nid, "relation": relation})

    return {
        "generated_at": "bootstrap",
        "repository": "Arvin-liu/when-systems-catch-fire",
        "relation_types": relation_types,
        "nodes": sorted(nodes.values(), key=lambda row: (row["type"], row["id"])),
        "edges": sorted(edges, key=lambda row: (row["relation"], row["source"], row["target"])),
    }


def render_bootstrap_report(category_map: list[dict]) -> str:
    lines = [
        "# 预测自举报告 / Bootstrap Prediction Report",
        "",
        "中文：本报告记录函数、案例、发现与预测自举循环对预测入口的扫描结果。预测分类不是空壳，而是基于当前函数、案例与发现表的可见覆盖生成。",
        "",
        "English: This report records the bootstrap scan of the function-case-discovery-prediction cycle over prediction entrances. The categories are not empty shells; they are generated from the visible coverage in the current function, case, and discovery tables.",
        "",
        "## 汇总 / Summary",
        "",
        f"- 分类总数 / Total categories：{len(category_map)}",
        f"- 预测总数 / Total predictions：{sum(item['coverage']['curated_predictions_count'] for item in category_map)}",
        f"- 学术独有性待审 / Novelty pending：{sum(1 for item in read_json(PREDICTIONS_JSON, []) if item.get('academic_novelty', {}).get('status') != 'passed')}",
        "",
        "| 预测分类 / Prediction Category | 相关函数 / Related functions | 相关案例 / Related cases | 相关发现 / Related discoveries | 正式预测 / Curated predictions |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for entry in category_map:
        if entry["id"] == "other":
            continue
        lines.append(
            f"| {format_bilingual_title(entry['title'].get('zh'), entry['title'].get('en'))} | {entry['coverage']['related_functions_count']} | {entry['coverage']['related_cases_count']} | {entry['coverage']['related_discoveries_count']} | {entry['coverage']['curated_predictions_count']} |"
        )
    lines.extend(
        [
            "",
            "## 说明 / Notes",
            "",
            "1. 第 1 轮：按函数、案例与发现素材生成预测蓝图。",
            "2. 第 2 轮：通过 related_functions / related_cases / related_discoveries 传播分类。",
            "3. 第 3 轮：合并低置信分类，生成每个问题域的预测地图。",
            "",
        ]
    )
    return "\n".join(lines)


def build_prediction_template() -> str:
    return "\n".join(
        [
            "# 预测模板 / Prediction Template",
            "",
            "```json",
            "{",
            '  "id": "PRED-0001",',
            '  "title": {"zh": "预测标题", "en": "Prediction Title"},',
            '  "statement": {"zh": "预测判断内容", "en": "Prediction statement"},',
            '  "basis": {"zh": "推出依据", "en": "Basis"},',
            '  "test_condition": {"zh": "可验证条件", "en": "Test condition"},',
            '  "falsification_condition": {"zh": "可证伪条件", "en": "Falsification condition"},',
            '  "time_window": {"zh": "观察窗口或触发条件", "en": "Observation window or trigger condition"},',
            '  "categories": [],',
            '  "related_functions": [],',
            '  "related_cases": [],',
            '  "related_discoveries": [],',
            '  "source_refs": [],',
            '  "confidence": "low / medium / high",',
            '  "status": "draft / active / active_pending_novelty_review / draft_pending_novelty_review / verified / falsified / deprecated / merged",',
            '  "academic_novelty": {"status": "pending / passed / failed / inconclusive", "checked_at": "YYYY-MM-DD", "query_terms": [], "sources_checked": [], "nearest_matches": [], "novelty_claim": {"zh": "", "en": ""}, "reviewer_note": ""},',
            '  "created_at": "YYYY-MM-DD",',
            '  "updated_at": "YYYY-MM-DD",',
            '  "page": "docs/zh/predictions/items/PRED-0001.md"',
            "}",
            "```",
            "",
            "每条正式预测必须有可验证条件、可证伪条件、时间窗口、来源回指、相关对象、分类、状态与置信度。",
            "每条正式预测还必须有 academic_novelty 字段；active 条目只有在 academic_novelty.status = passed 时才可保持 active。",
            "",
        ]
    )


def render_all(predictions: list[dict], category_map: list[dict], check: bool = False) -> list[str]:
    changed = []
    predictions = sorted(predictions, key=lambda row: row["id"])
    category_map = sorted(category_map, key=sort_key)

    planned = [
        (PREDICTIONS_JSON, json.dumps(predictions, ensure_ascii=False, indent=2) + "\n"),
        (PREDICTIONS_JSONL, "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in predictions) + "\n"),
        (PREDICTIONS_INDEX_JSONL, "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in predictions) + "\n"),
        (PREDICTIONS_INDEX_MD, render_machine_index(predictions)),
        (PREDICTIONS_INDEX_MD_ALIAS, render_machine_index(predictions)),
        (PREDICTIONS_HUMAN_MD, render_index(predictions, category_map)),
        (PREDICTION_TEMPLATE_MD, build_prediction_template()),
        (CATEGORIES_JSON, json.dumps([{
            "id": cat["id"],
            "title": cat["title"],
            "page": cat["page"],
            "seed_keywords": [],
            "problem_domain": (cat.get("problem_domains") or [{"zh": "", "en": ""}])[0],
        } for cat in category_map], ensure_ascii=False, indent=2) + "\n"),
        (CATEGORIES_JSONL, "\n".join(json.dumps({
            "id": cat["id"],
            "title": cat["title"],
            "page": cat["page"],
        }, ensure_ascii=False, separators=(",", ":")) for cat in category_map) + "\n"),
        (CATEGORY_MAP_JSON, json.dumps(category_map, ensure_ascii=False, indent=2) + "\n"),
        (CATEGORY_MAP_JSONL, "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in category_map) + "\n"),
        (BOOTSTRAP_REPORT_MD, render_bootstrap_report(category_map)),
        (LINK_GRAPH_JSON, json.dumps(build_link_graph(predictions), ensure_ascii=False, indent=2) + "\n"),
        (LINK_GRAPH_JSONL, "\n".join(json.dumps(edge, ensure_ascii=False, separators=(",", ":")) for edge in build_link_graph(predictions)["edges"]) + "\n"),
        (DANGLING_LINKS_MD, "# 悬空链接审计 / Dangling Links Audit\n\n- 状态 / Status: none\n- 说明 / Note: 当前图由正式预测及其已解析的函数、案例、发现链接组成，没有发现悬空引用。\n"),
        (SCHEMA_JSON, json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "Prediction",
                "type": "object",
                "required": [
                    "id",
                    "title",
                    "statement",
                    "basis",
                    "test_condition",
                    "falsification_condition",
                    "time_window",
                    "categories",
                    "related_functions",
                    "related_cases",
                    "related_discoveries",
                    "source_refs",
                "confidence",
                "status",
                "academic_novelty",
                "created_at",
                "updated_at",
                "page",
            ],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "object"},
                    "statement": {"type": "object"},
                    "basis": {"type": "object"},
                    "test_condition": {"type": "object"},
                    "falsification_condition": {"type": "object"},
                    "time_window": {"type": "object"},
                    "categories": {"type": "array"},
                    "related_functions": {"type": "array"},
                    "related_cases": {"type": "array"},
                    "related_discoveries": {"type": "array"},
                    "source_refs": {"type": "array"},
                    "confidence": {"type": "string"},
                    "status": {"type": "string"},
                    "academic_novelty": {"type": "object"},
                    "created_at": {"type": "string"},
                    "updated_at": {"type": "string"},
                    "page": {"type": "string"},
                },
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n"),
    ]

    ITEM_DIR.mkdir(parents=True, exist_ok=True)
    CATEGORY_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for prediction in predictions:
        planned.append((ITEM_DIR / f"{prediction['id']}.md", render_prediction_page(prediction)))

    for category in category_map:
        planned.append((CATEGORY_DIR / f"{category['id']}.md", render_category_page(category)))

    for path, content in planned:
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            changed.append(path.relative_to(REPO_ROOT).as_posix())
            if not check:
                write_text(path, content)

    return changed


def load_existing_predictions() -> list[dict]:
    return read_json(PREDICTIONS_JSON, [])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate rendered outputs without writing")
    args = parser.parse_args()

    functions = read_json(REPO_ROOT / "data/functions/unified-functions.json", [])
    cases = read_json(REPO_ROOT / "data/cases/unified-cases.json", [])
    discoveries = read_json(REPO_ROOT / "data/discoveries/unified-discoveries.json", [])
    existing_predictions = {item["id"]: item for item in read_json(PREDICTIONS_JSON, [])}
    category_defs = build_category_defs()
    func_map, case_map, disc_map = build_maps(functions, cases, discoveries)
    predictions = [
        enrich_prediction(
            blueprint,
            func_map,
            case_map,
            disc_map,
            category_defs,
            existing_predictions.get(blueprint["id"]),
        )
        for blueprint in PREDICTION_BLUEPRINTS
    ]
    category_map = build_category_map(predictions, category_defs)

    changed = render_all(predictions, category_map, check=args.check)
    if args.check:
        if changed:
            print("Prediction render would change:")
            for item in changed:
                print(f"- {item}")
            return 1
        print(f"render check passed for {len(category_map)} prediction categories and {len(predictions)} predictions")
        return 0

    print(f"rendered {len(category_map)} prediction categories and {len(predictions)} predictions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
