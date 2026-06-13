#!/usr/bin/env python3
"""Shared helpers for the New Answers layer."""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from display_utils import format_bilingual_title


REPO_ROOT = Path(__file__).resolve().parents[1]
ANSWER_DIR = REPO_ROOT / "docs/zh/answers"
CATEGORY_DIR = ANSWER_DIR / "categories"
ITEM_DIR = ANSWER_DIR / "items"
DATA_DIR = REPO_ROOT / "data/answers"

ANSWERS_JSON = DATA_DIR / "unified-answers.json"
ANSWERS_JSONL = DATA_DIR / "unified-answers.jsonl"
ANSWERS_INDEX_MD = DATA_DIR / "unified-answers-index.md"
ANSWERS_LIST_MD = REPO_ROOT / "ANSWERS.md"
ANSWER_TEMPLATE_MD = ANSWER_DIR / "ANSWER_TEMPLATE.md"
CATEGORIES_JSON = DATA_DIR / "categories.json"
CATEGORIES_JSONL = DATA_DIR / "categories.jsonl"
CATEGORY_MAP_JSON = DATA_DIR / "category-map.json"
CATEGORY_MAP_JSONL = DATA_DIR / "category-map.jsonl"
BOOTSTRAP_REPORT_MD = DATA_DIR / "bootstrap-answer-report.md"
BOOTSTRAP_REPORT_JSON = DATA_DIR / "bootstrap-answer-report.json"

FUNCTIONS_JSON = REPO_ROOT / "data/functions/unified-functions.json"
CASES_JSON = REPO_ROOT / "data/cases/unified-cases.json"
DISCOVERIES_JSON = REPO_ROOT / "data/discoveries/unified-discoveries.json"
PREDICTIONS_JSON = REPO_ROOT / "data/predictions/unified-predictions.json"

START_MARKER = "<!-- ANSWER_LIST_START -->"
END_MARKER = "<!-- ANSWER_LIST_END -->"

ANSWER_ID_RE = re.compile(r"^ANS-(\d{4})$")


CATEGORY_DEFINITIONS: list[dict] = [
    {
        "id": "physics",
        "title": {"zh": "物理学", "en": "Physics"},
        "page": "docs/zh/answers/categories/physics.md",
        "seed_keywords": ["物理", "量子", "引力", "统一", "大统一", "黑洞", "宇宙", "维度"],
        "problem_domain": {
            "zh": "基础物理、统一理论、引力、黑洞、维度与宇宙学",
            "en": "Fundamental physics, unification, gravity, black holes, dimensions, and cosmology",
        },
    },
    {
        "id": "psychology",
        "title": {"zh": "心理学", "en": "Psychology"},
        "page": "docs/zh/answers/categories/psychology.md",
        "seed_keywords": ["心理", "认知", "动机", "情绪", "决策", "意识", "好奇心"],
        "problem_domain": {
            "zh": "认知、动机、情绪、决策与主观体验",
            "en": "Cognition, motivation, emotion, decision-making, and subjective experience",
        },
    },
    {
        "id": "chemistry",
        "title": {"zh": "化学", "en": "Chemistry"},
        "page": "docs/zh/answers/categories/chemistry.md",
        "seed_keywords": ["化学", "分子", "反应", "催化", "材料"],
        "problem_domain": {
            "zh": "分子、反应、催化、材料转化",
            "en": "Molecules, reactions, catalysis, and material transformation",
        },
    },
    {
        "id": "biology",
        "title": {"zh": "生物学", "en": "Biology"},
        "page": "docs/zh/answers/categories/biology.md",
        "seed_keywords": ["生物", "细胞", "基因", "进化", "代谢"],
        "problem_domain": {
            "zh": "生命体、细胞、进化、代谢与生态组织",
            "en": "Living systems, cells, evolution, metabolism, and biological organization",
        },
    },
    {
        "id": "neuroscience-and-consciousness",
        "title": {"zh": "神经科学与意识", "en": "Neuroscience and Consciousness"},
        "page": "docs/zh/answers/categories/neuroscience-and-consciousness.md",
        "seed_keywords": ["神经", "脑", "意识", "心智", "主观体验"],
        "problem_domain": {
            "zh": "意识、神经元、主观体验与认知机制",
            "en": "Consciousness, neurons, subjective experience, and cognitive mechanisms",
        },
    },
    {
        "id": "medicine-and-health",
        "title": {"zh": "医学与健康", "en": "Medicine and Health"},
        "page": "docs/zh/answers/categories/medicine-and-health.md",
        "seed_keywords": ["医学", "健康", "疾病", "治疗", "诊断", "免疫"],
        "problem_domain": {
            "zh": "健康、疾病、免疫、诊断与治疗",
            "en": "Health, disease, immunity, diagnosis, and treatment",
        },
    },
    {
        "id": "philosophy",
        "title": {"zh": "哲学", "en": "Philosophy"},
        "page": "docs/zh/answers/categories/philosophy.md",
        "seed_keywords": ["哲学", "本体", "认识论", "自由意志", "意义", "真理"],
        "problem_domain": {
            "zh": "存在、真理、自由意志、伦理与认识论",
            "en": "Being, truth, free will, ethics, and epistemology",
        },
    },
    {
        "id": "history-and-civilization",
        "title": {"zh": "历史与文明", "en": "History and Civilization"},
        "page": "docs/zh/answers/categories/history-and-civilization.md",
        "seed_keywords": ["历史", "文明", "王朝", "统一", "转身", "制度"],
        "problem_domain": {
            "zh": "王朝更替、文明延续、制度转化与历史记忆",
            "en": "Dynastic change, civilizational continuity, institutional transformation, and historical memory",
        },
    },
    {
        "id": "literature-and-narrative",
        "title": {"zh": "文学与叙事", "en": "Literature and Narrative"},
        "page": "docs/zh/answers/categories/literature-and-narrative.md",
        "seed_keywords": ["文学", "叙事", "文本", "故事", "隐喻"],
        "problem_domain": {
            "zh": "叙事、文本、修辞、隐喻与故事结构",
            "en": "Narrative, text, rhetoric, metaphor, and story structure",
        },
    },
    {
        "id": "art-and-photography",
        "title": {"zh": "艺术与摄影", "en": "Art and Photography"},
        "page": "docs/zh/answers/categories/art-and-photography.md",
        "seed_keywords": ["图像", "视觉", "审美", "摄影", "图片"],
        "problem_domain": {
            "zh": "观看、图像、摄影、审美与视觉构图",
            "en": "Viewing, imagery, photography, aesthetics, and visual composition",
        },
    },
    {
        "id": "economics-and-wealth",
        "title": {"zh": "经济与财富", "en": "Economics and Wealth"},
        "page": "docs/zh/answers/categories/economics-and-wealth.md",
        "seed_keywords": ["经济", "财富", "成本", "收益", "市场", "投资", "金融", "风险"],
        "problem_domain": {
            "zh": "成本、收益、市场、投资、激励与财富分配",
            "en": "Cost, return, markets, investment, incentives, and wealth allocation",
        },
    },
    {
        "id": "law-and-institutions",
        "title": {"zh": "法律与制度", "en": "Law and Institutions"},
        "page": "docs/zh/answers/categories/law-and-institutions.md",
        "seed_keywords": ["法律", "法治", "契约", "权利", "治理", "制度"],
        "problem_domain": {
            "zh": "权利、法治、制度、规则与治理",
            "en": "Rights, rule of law, institutions, rules, and governance",
        },
    },
    {
        "id": "sociology-and-politics",
        "title": {"zh": "社会学与政治", "en": "Sociology and Politics"},
        "page": "docs/zh/answers/categories/sociology-and-politics.md",
        "seed_keywords": ["社会", "政治", "群体", "组织", "认同", "退出权"],
        "problem_domain": {
            "zh": "群体、组织、政治、阶层、协作与社会结构",
            "en": "Groups, organizations, politics, class structure, cooperation, and social structure",
        },
    },
    {
        "id": "ai-and-systems",
        "title": {"zh": "AI 与系统", "en": "AI and Systems"},
        "page": "docs/zh/answers/categories/ai-and-systems.md",
        "seed_keywords": ["AI", "智能体", "调度", "协议", "门控", "工具链", "中间层"],
        "problem_domain": {
            "zh": "AI、智能体、调度、接口、协议、门控与工具链",
            "en": "AI, agents, scheduling, interfaces, protocols, gating, and toolchains",
        },
    },
    {
        "id": "technology-and-engineering",
        "title": {"zh": "技术与工程", "en": "Technology and Engineering"},
        "page": "docs/zh/answers/categories/technology-and-engineering.md",
        "seed_keywords": ["技术", "工程", "架构", "实现", "算法", "系统设计"],
        "problem_domain": {
            "zh": "架构、实现、算法、工程、控制与性能",
            "en": "Architecture, implementation, algorithms, engineering, control, and performance",
        },
    },
    {
        "id": "education-and-learning",
        "title": {"zh": "教育与学习", "en": "Education and Learning"},
        "page": "docs/zh/answers/categories/education-and-learning.md",
        "seed_keywords": ["教育", "学习", "教学", "训练", "课程"],
        "problem_domain": {
            "zh": "学习、训练、教学、验证与认知发展",
            "en": "Learning, training, teaching, validation, and cognitive development",
        },
    },
    {
        "id": "ecology-and-environment",
        "title": {"zh": "生态与环境", "en": "Ecology and Environment"},
        "page": "docs/zh/answers/categories/ecology-and-environment.md",
        "seed_keywords": ["生态", "环境", "气候", "污染", "资源"],
        "problem_domain": {
            "zh": "生态、环境、气候、资源与可持续性",
            "en": "Ecology, environment, climate, resources, and sustainability",
        },
    },
    {
        "id": "other",
        "title": {"zh": "其他", "en": "Other"},
        "page": "docs/zh/answers/categories/other.md",
        "seed_keywords": [],
        "problem_domain": {
            "zh": "暂未归入单一学科的跨域条目",
            "en": "Cross-domain entries not yet placed into a single discipline",
        },
    },
]

CATEGORY_LOOKUP = {entry["id"]: entry for entry in CATEGORY_DEFINITIONS}


def read_json(path: Path, default):
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return json.loads(text)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, value) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, rows) -> None:
    body = "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows)
    write_text(path, body + ("\n" if body else ""))


def rel_link(from_path: Path, to_path: Path) -> str:
    return Path(os.path.relpath(to_path, from_path.parent)).as_posix()


def next_answer_id(items: list[dict]) -> str:
    max_num = 0
    for item in items:
        match = ANSWER_ID_RE.match(item.get("id", ""))
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"ANS-{max_num + 1:04d}"


def novelty_counts(items: list[dict]) -> dict[str, int]:
    counts = Counter()
    for item in items:
        counts[item.get("academic_novelty", {}).get("status", "pending")] += 1
    return {
        "passed": counts.get("passed", 0),
        "pending": counts.get("pending", 0),
        "inconclusive": counts.get("inconclusive", 0),
        "failed": counts.get("failed", 0),
    }


def is_curated_answer(item: dict) -> bool:
    return item.get("status") == "active" and item.get("academic_novelty", {}).get("status") == "passed"


def normalize_source_refs(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        token = value.strip()
        if not token or token in seen:
            continue
        seen.add(token)
        result.append(token)
    return result


def answer_counts(answers: list[dict], category_map: list[dict]) -> dict[str, int]:
    return {
        "curated": sum(1 for item in answers if is_curated_answer(item)),
        "leads": sum(1 for item in answers if not is_curated_answer(item)),
        "passed_novelty": sum(1 for item in answers if item.get("academic_novelty", {}).get("status") == "passed"),
        "pending_novelty": sum(1 for item in answers if item.get("academic_novelty", {}).get("status") == "pending"),
        "inconclusive_novelty": sum(1 for item in answers if item.get("academic_novelty", {}).get("status") == "inconclusive"),
        "failed_novelty": sum(1 for item in answers if item.get("academic_novelty", {}).get("status") == "failed"),
    }


def build_lookup(items: list[dict]) -> dict[str, dict]:
    return {item["id"]: item for item in items}


def select_related(items: list[dict], key: str) -> list[dict]:
    selected = []
    for item in items:
        for ref in item.get(key, []):
            if ref not in selected:
                selected.append(ref)
    return selected


def build_category_map(
    answers: list[dict],
    categories: list[dict],
    functions: list[dict] | None = None,
    cases: list[dict] | None = None,
    discoveries: list[dict] | None = None,
    predictions: list[dict] | None = None,
) -> list[dict]:
    function_lookup = build_lookup(functions or [])
    case_lookup = {item.get("normalized_id", item["id"]): item for item in (cases or [])}
    discovery_lookup = build_lookup(discoveries or [])
    prediction_lookup = build_lookup(predictions or [])

    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in answers:
        for category_id in item.get("categories", []):
            grouped[category_id].append(item)

    result = []
    for category in categories:
        items = grouped.get(category["id"], [])
        curated = [item for item in items if is_curated_answer(item)]
        leads = [item for item in items if not is_curated_answer(item)]
        related_functions = []
        related_cases = []
        related_discoveries = []
        related_predictions = []
        for item in items:
            for fid in item.get("related_functions", []):
                func = function_lookup.get(fid)
                if func and fid not in {entry["id"] for entry in related_functions}:
                    related_functions.append({"id": func["id"], "title": func["title"], "page": func["links"]["human_page"]})
            for cid in item.get("related_cases", []):
                case = case_lookup.get(cid) or case_lookup.get(cid.upper())
                if case and cid not in {entry["id"] for entry in related_cases}:
                    related_cases.append({"id": case["normalized_id"], "title": case["title"], "page": case["links"]["human_page"]})
            for did in item.get("related_discoveries", []):
                disc = discovery_lookup.get(did)
                if disc and did not in {entry["id"] for entry in related_discoveries}:
                    related_discoveries.append({"id": disc["id"], "title": disc["title"], "page": disc["links"]["human_page"]})
            for pid in item.get("related_predictions", []):
                pred = prediction_lookup.get(pid)
                if pred and pid not in {entry["id"] for entry in related_predictions}:
                    related_predictions.append({"id": pred["id"], "title": pred["title"], "page": pred["links"]["human_page"], "status": pred.get("status")})
        result.append(
            {
                "id": category["id"],
                "category_id": category["id"],
                "title": category["title"],
                "page": category["page"],
                "problem_domains": [category["problem_domain"]],
                "related_functions": related_functions,
                "related_cases": related_cases,
                "related_discoveries": related_discoveries,
                "related_predictions": related_predictions,
                "curated_answers": [
                    {"id": item["id"], "title": item["title"], "page": item["page"], "status": item.get("status")}
                    for item in curated
                ],
                "answer_leads": [
                    {"id": item["id"], "title": item["title"], "page": item["page"], "status": item.get("status")}
                    for item in leads
                ],
                "coverage": {
                    "related_functions_count": len(related_functions),
                    "related_cases_count": len(related_cases),
                    "related_discoveries_count": len(related_discoveries),
                    "related_predictions_count": len(related_predictions),
                    "curated_answers_count": len(curated),
                    "answer_leads_count": len(leads),
                },
            }
        )
    return result


def sort_category_rows(category_map: list[dict]) -> list[dict]:
    def key(row: dict) -> tuple:
        cov = row.get("coverage", {})
        return (
            -cov.get("curated_answers_count", 0),
            -cov.get("answer_leads_count", 0),
            -(cov.get("related_functions_count", 0) + cov.get("related_cases_count", 0) + cov.get("related_discoveries_count", 0) + cov.get("related_predictions_count", 0)),
            row.get("id", ""),
        )

    return sorted(category_map, key=key)


def render_source_list(items: list[str]) -> str:
    if not items:
        return "-"
    return "\n".join(f"- {item}" for item in items)


def render_link_list(entries: list[dict], current_path: Path) -> str:
    if not entries:
        return "-\n"
    lines = []
    for entry in entries:
        label = f"{entry['id']}｜{format_bilingual_title(entry['title'].get('zh'), entry['title'].get('en'))}"
        if entry.get("page"):
            lines.append(f"- [{label}]({rel_link(current_path, REPO_ROOT / entry['page'])})")
        else:
            lines.append(f"- {label}")
    return "\n".join(lines)


def render_answer_page(item: dict) -> str:
    current_path = ITEM_DIR / f"{item['id']}.md"
    lines = [
        f"# {item['id']} {format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}",
        "",
        f"[← 返回新答案总表 / Back to New Answers]({rel_link(current_path, ANSWERS_LIST_MD)})",
        f"[返回仓库首页 / Back to Repository Home]({rel_link(current_path, REPO_ROOT / 'README.md')})",
        "",
        "## 问题 / Question",
        "",
        f"中文：{item['question']['zh']}",
        f"English: {item['question']['en']}",
        "",
        "## 新答案 / New Answer",
        "",
        f"中文：{item['answer']['zh']}",
        f"English: {item['answer']['en']}",
        "",
        "## 已有答案或旧问题背景 / Existing Answers or Prior Problem Background",
        "",
        f"中文：{item['prior_answers']['zh']}",
        f"English: {item['prior_answers']['en']}",
        "",
        "## 新解释在哪里 / What Is New in This Answer",
        "",
        f"中文：{item['new_explanation']['zh']}",
        f"English: {item['new_explanation']['en']}",
        "",
        "## 推出依据 / Basis",
        "",
        f"中文：{item['basis']['zh']}",
        f"English: {item['basis']['en']}",
        "",
        "## 可检验性 / Testability",
        "",
        f"中文：{item['testability']['zh']}",
        f"English: {item['testability']['en']}",
        "",
        "## 分类 / Categories",
        "",
    ]
    if item.get("categories"):
        for category_id in item["categories"]:
            category = CATEGORY_LOOKUP.get(category_id)
            if category:
                lines.append(f"- {category['title']['zh']} / {category['title']['en']}")
            else:
                lines.append(f"- {category_id}")
    else:
        lines.append("-")
    lines.extend(
        [
            "",
            "## 相关函数 / Related Functions",
            "",
            render_source_list(item.get("related_functions", [])),
            "",
            "## 相关案例 / Related Cases",
            "",
            render_source_list(item.get("related_cases", [])),
            "",
            "## 相关发现 / Related Discoveries",
            "",
            render_source_list(item.get("related_discoveries", [])),
            "",
            "## 相关预测 / Related Predictions",
            "",
            render_source_list(item.get("related_predictions", [])),
            "",
            "## 来源回指 / Source References",
            "",
            render_source_list(item.get("source_refs", [])),
            "",
            "## 学术搜索独有性检查 / Academic Novelty Check",
            "",
            f"- 状态 / Status：{item['academic_novelty']['status']}",
            f"- 检查时间 / Checked at：{item['academic_novelty'].get('checked_at', '')}",
            f"- 搜索词 / Query terms：{', '.join(item['academic_novelty'].get('query_terms', []))}",
            f"- 检查来源 / Sources checked：{', '.join(item['academic_novelty'].get('sources_checked', []))}",
            f"- 最近相似结果 / Nearest matches：{json.dumps(item['academic_novelty'].get('nearest_matches', []), ensure_ascii=False)}",
            f"- 为什么不是同一答案 / Why not identical：{item['academic_novelty'].get('reviewer_note', '')}",
            f"- 独有性声明 / Novelty claim：{item['academic_novelty'].get('novelty_claim', {}).get('zh', '')} / {item['academic_novelty'].get('novelty_claim', {}).get('en', '')}",
            "",
            "## 状态 / Status",
            "",
            item["status"],
            "",
            "## 置信度 / Confidence",
            "",
            item["confidence"],
            "",
        ]
    )
    return "\n".join(lines)


def render_category_page(category: dict) -> str:
    current_path = CATEGORY_DIR / f"{category['id']}.md"
    lines = [
        f"# {format_bilingual_title(category['title'].get('zh'), category['title'].get('en'))}",
        "",
        f"[← 返回新答案总表 / Back to New Answers]({rel_link(current_path, ANSWERS_LIST_MD)})",
        f"[返回仓库首页 / Back to Repository Home]({rel_link(current_path, REPO_ROOT / 'README.md')})",
        "",
        "## 已整理新答案 / Curated Answers",
        "",
    ]
    if category.get("curated_answers"):
        lines.extend(render_link_list(category["curated_answers"], current_path).splitlines())
    else:
        lines.append("-")
    lines.extend(
        [
            "",
            "## 待整理答案线索 / Answer Leads to Curate",
            "",
        ]
    )
    if category.get("answer_leads"):
        lines.extend(render_link_list(category["answer_leads"], current_path).splitlines())
    else:
        lines.append("-")
    lines.extend(
        [
            "",
            "## 相关函数、案例、发现与预测 / Related Functions, Cases, Discoveries, and Predictions",
            "",
        ]
    )
    if category.get("related_functions"):
        lines.append("### 相关函数 / Related Functions")
        lines.extend(render_link_list(category["related_functions"], current_path).splitlines())
        lines.append("")
    if category.get("related_cases"):
        lines.append("### 相关案例 / Related Cases")
        lines.extend(render_link_list(category["related_cases"], current_path).splitlines())
        lines.append("")
    if category.get("related_discoveries"):
        lines.append("### 相关发现 / Related Discoveries")
        lines.extend(render_link_list(category["related_discoveries"], current_path).splitlines())
        lines.append("")
    if category.get("related_predictions"):
        lines.append("### 相关预测 / Related Predictions")
        lines.extend(render_link_list(category["related_predictions"], current_path).splitlines())
        lines.append("")
    return "\n".join(lines)


def render_answers_index(answers: list[dict], category_map: list[dict]) -> str:
    counts = answer_counts(answers, category_map)
    sorted_categories = sort_category_rows(category_map)
    lines = [
        "# 新答案总表 / New Answer Index",
        "",
        "中文：这里收录《点火》框架对既有问题、经典问题、未解问题或已有答案给出的新回答。新答案不是普通问答记录；它必须有明确问题、明确回答、推论依据、来源回指，并通过学术搜索独有性检查。",
        "",
        "English: This index collects new answers generated by the Ignition framework for existing, classic, unresolved, or previously answered questions. A new answer is not an ordinary Q&A note; it must include a clear question, a clear answer, a basis of inference, source references, and an academic novelty check.",
        "",
        "## 答案分类 / Answer Categories",
        "",
        "| 答案分类 / Answer Category | 正式新答案 / Curated Answers | 待整理线索 / Answer Leads | 当前覆盖 / Current Coverage |",
        "|---|---:|---:|---|",
    ]
    for category in sorted_categories:
        page = category["page"]
        cov = category["coverage"]
        coverage = (
            f"{cov['related_functions_count']} functions, {cov['related_cases_count']} cases, "
            f"{cov['related_discoveries_count']} discoveries, {cov['related_predictions_count']} predictions"
        )
        label = f"[{format_bilingual_title(category['title'].get('zh'), category['title'].get('en'))}]({page})"
        lines.append(
            f"| {label} | {cov['curated_answers_count']} | {cov['answer_leads_count']} | {coverage} |"
        )
    lines.extend(
        [
            "",
            "## 最近新答案 / Recent New Answers",
            "",
        ]
    )
    recent = [item for item in answers if is_curated_answer(item)]
    recent.sort(key=lambda item: (item.get("created_at", ""), item["id"]), reverse=True)
    if recent:
        for item in recent[:20]:
            categories = ", ".join(item.get("categories", [])) or "other"
            lines.append(
                f"- [{item['id']}｜{format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}]({item['page']}) "
                f"({categories}; novelty: {item['academic_novelty']['status']})"
            )
    else:
        lines.append("- 暂无正式新答案。 / No curated answers yet.")
    lines.append("")
    return "\n".join(lines)


def render_answer_index(answers: list[dict], category_map: list[dict]) -> str:
    return render_answers_index(answers, category_map)


def render_answer_index_md(answers: list[dict]) -> str:
    lines = ["# 新答案索引 / New Answers Index", ""]
    for item in answers:
        lines.append(f"- {item['id']} | {item['title']['zh']} | {item['status']} | {item['academic_novelty']['status']}")
    lines.append("")
    return "\n".join(lines)


def render_bootstrap_report(answers: list[dict], category_map: list[dict], sources_summary: dict[str, int], notes: list[str]) -> tuple[dict, str]:
    counts = answer_counts(answers, category_map)
    payload = {
        "generated_at": notes[0] if notes else "",
        "answers": counts,
        "sources_summary": sources_summary,
        "notes": notes,
    }
    lines = [
        "# New Answers Bootstrap Report",
        "",
        f"- curated_answers: {counts['curated']}",
        f"- answer_leads: {counts['leads']}",
        f"- passed_novelty: {counts['passed_novelty']}",
        f"- pending_novelty: {counts['pending_novelty']}",
        f"- inconclusive_novelty: {counts['inconclusive_novelty']}",
        f"- failed_novelty: {counts['failed_novelty']}",
        "",
        "## Sources",
        "",
    ]
    for key, value in sources_summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Notes", ""])
    for note in notes:
        lines.append(f"- {note}")
    lines.append("")
    return payload, "\n".join(lines)
