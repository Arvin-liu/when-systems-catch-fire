from __future__ import annotations

import copy
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from display_utils import format_bilingual_title


REPO_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_DIR = REPO_ROOT / "docs/zh/discoveries"
CATEGORY_DIR = DISCOVERY_DIR / "categories"
DATA_DIR = REPO_ROOT / "data/discoveries"

DISCOVERY_JSON = DATA_DIR / "unified-discoveries.json"
DISCOVERY_JSONL = DATA_DIR / "unified-discoveries.jsonl"
DISCOVERY_INDEX_MD = DATA_DIR / "unified-discoveries-index.md"
DISCOVERY_LIST_MD = REPO_ROOT / "DISCOVERIES.md"

CATEGORIES_JSON = DATA_DIR / "categories.json"
CATEGORIES_JSONL = DATA_DIR / "categories.jsonl"
CATEGORY_MAP_JSON = DATA_DIR / "category-map.json"
CATEGORY_MAP_JSONL = DATA_DIR / "category-map.jsonl"
BOOTSTRAP_REPORT_MD = DATA_DIR / "bootstrap-category-report.md"

FUNC_JSON = REPO_ROOT / "data/functions/unified-functions.json"
CASE_JSON = REPO_ROOT / "data/cases/unified-cases.json"

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
DISCOVERY_ID_RE = re.compile(r"^DISC-(\d{4})$")


CATEGORY_DEFINITIONS: list[dict] = [
    {
        "id": "physics",
        "title": {"zh": "物理学", "en": "Physics"},
        "page": "docs/zh/discoveries/categories/physics.md",
        "seed_keywords": ["物理", "量子", "电磁", "热力", "力学", "粒子", "能量", "熵", "场", "波", "光", "相变", "引力", "Planck", "宇宙"],
        "problem_domain": {
            "zh": "力、场、统一、尺度、相变与物理域中的结构转化",
            "en": "Forces, fields, unification, scale, phase transitions, and structural transformations in physical domains",
        },
    },
    {
        "id": "psychology",
        "title": {"zh": "心理学", "en": "Psychology"},
        "page": "docs/zh/discoveries/categories/psychology.md",
        "seed_keywords": ["心理", "认知", "动机", "行为", "情绪", "自我", "意志", "偏好", "注意", "判断", "直觉", "决策", "犹豫", "恐惧"],
        "problem_domain": {
            "zh": "认知、动机、行为、情绪、决策与自我模型",
            "en": "Cognition, motivation, behavior, emotion, decision-making, and self-models",
        },
    },
    {
        "id": "chemistry",
        "title": {"zh": "化学", "en": "Chemistry"},
        "page": "docs/zh/discoveries/categories/chemistry.md",
        "seed_keywords": ["化学", "分子", "反应", "催化", "化合", "溶液", "酸", "碱", "键", "物质", "材料", "有机", "无机"],
        "problem_domain": {
            "zh": "分子、反应、催化、溶液、物质转化与材料过程",
            "en": "Molecules, reactions, catalysis, solutions, material transformation, and chemical processes",
        },
    },
    {
        "id": "biology",
        "title": {"zh": "生物学", "en": "Biology"},
        "page": "docs/zh/discoveries/categories/biology.md",
        "seed_keywords": ["生物", "细胞", "基因", "蛋白", "进化", "代谢", "物种", "繁殖", "生命", "有机"],
        "problem_domain": {
            "zh": "生命体、细胞、进化、代谢、生态位与生物组织",
            "en": "Living systems, cells, evolution, metabolism, ecological niches, and biological organization",
        },
    },
    {
        "id": "neuroscience-and-consciousness",
        "title": {"zh": "神经科学与意识", "en": "Neuroscience and Consciousness"},
        "page": "docs/zh/discoveries/categories/neuroscience-and-consciousness.md",
        "seed_keywords": ["神经", "脑", "意识", "神经元", "突触", "自主意识", "认知", "心智"],
        "problem_domain": {
            "zh": "意识、神经元、脑、主观体验与认知机制",
            "en": "Consciousness, neurons, the brain, subjective experience, and cognitive mechanisms",
        },
    },
    {
        "id": "medicine-and-health",
        "title": {"zh": "医学与健康", "en": "Medicine and Health"},
        "page": "docs/zh/discoveries/categories/medicine-and-health.md",
        "seed_keywords": ["医学", "健康", "疾病", "治疗", "诊断", "临床", "药", "免疫", "病原", "耐药", "疗", "病"],
        "problem_domain": {
            "zh": "健康、疾病、免疫、诊断、治疗与耐药",
            "en": "Health, disease, immunity, diagnosis, treatment, and resistance",
        },
    },
    {
        "id": "philosophy",
        "title": {"zh": "哲学", "en": "Philosophy"},
        "page": "docs/zh/discoveries/categories/philosophy.md",
        "seed_keywords": ["哲学", "本体", "认识论", "自由意志", "存在", "意义", "真理", "伦理", "形而上", "悖论", "实在", "主体"],
        "problem_domain": {
            "zh": "存在、真理、自由意志、伦理与认识论",
            "en": "Being, truth, free will, ethics, and epistemology",
        },
    },
    {
        "id": "history-and-civilization",
        "title": {"zh": "历史与文明", "en": "History and Civilization"},
        "page": "docs/zh/discoveries/categories/history-and-civilization.md",
        "seed_keywords": ["历史", "文明", "朝代", "王朝", "帝国", "古代", "近代", "现代", "周公", "孔子", "秦", "汉", "唐", "宋", "元", "明", "清"],
        "problem_domain": {
            "zh": "王朝更替、文明延续、制度转化与历史记忆",
            "en": "Dynastic change, civilizational continuity, institutional transformation, and historical memory",
        },
    },
    {
        "id": "literature-and-narrative",
        "title": {"zh": "文学与叙事", "en": "Literature and Narrative"},
        "page": "docs/zh/discoveries/categories/literature-and-narrative.md",
        "seed_keywords": ["文学", "叙事", "文本", "故事", "小说", "诗", "修辞", "隐喻", "叙述", "话语"],
        "problem_domain": {
            "zh": "叙事、文本、修辞、隐喻与故事结构",
            "en": "Narrative, text, rhetoric, metaphor, and story structure",
        },
    },
    {
        "id": "art-and-photography",
        "title": {"zh": "艺术与摄影", "en": "Art and Photography"},
        "page": "docs/zh/discoveries/categories/art-and-photography.md",
        "seed_keywords": ["图像", "视觉", "观看", "审美", "摄影", "照片", "图形", "图片", "美学", "构图", "镜头"],
        "problem_domain": {
            "zh": "观看、图像、摄影、审美与视觉构图",
            "en": "Viewing, imagery, photography, aesthetics, and visual composition",
        },
    },
    {
        "id": "economics-and-wealth",
        "title": {"zh": "经济与财富", "en": "Economics and Wealth"},
        "page": "docs/zh/discoveries/categories/economics-and-wealth.md",
        "seed_keywords": ["经济", "财富", "成本", "收益", "市场", "投资", "金融", "交易", "资源", "激励", "预算", "现金流", "利润", "风险", "凯利"],
        "problem_domain": {
            "zh": "成本、收益、市场、投资、激励与财富分配",
            "en": "Cost, return, markets, investment, incentives, and wealth allocation",
        },
    },
    {
        "id": "law-and-institutions",
        "title": {"zh": "法律与制度", "en": "Law and Institutions"},
        "page": "docs/zh/discoveries/categories/law-and-institutions.md",
        "seed_keywords": ["法律", "法治", "契约", "权利", "主权", "治理", "监管", "司法", "民事", "法条", "义务", "制度"],
        "problem_domain": {
            "zh": "权利、法治、制度、主权、规则与治理",
            "en": "Rights, rule of law, institutions, sovereignty, rules, and governance",
        },
    },
    {
        "id": "sociology-and-politics",
        "title": {"zh": "社会学与政治", "en": "Sociology and Politics"},
        "page": "docs/zh/discoveries/categories/sociology-and-politics.md",
        "seed_keywords": ["社会", "政治", "群体", "组织", "阶层", "公共", "政权", "文化", "协作", "博弈", "代际"],
        "problem_domain": {
            "zh": "群体、组织、政治、阶层、协作与社会结构",
            "en": "Groups, organizations, politics, class structure, cooperation, and social structure",
        },
    },
    {
        "id": "ai-and-systems",
        "title": {"zh": "AI 与系统", "en": "AI and Systems"},
        "page": "docs/zh/discoveries/categories/ai-and-systems.md",
        "seed_keywords": ["AI", "智能体", "agent", "调度", "接口", "协议", "门控", "工具", "工具链", "pipeline", "workflow", "中间层", "多智能体", "框架", "协同"],
        "problem_domain": {
            "zh": "AI、智能体、调度、接口、协议、门控与工具链",
            "en": "AI, agents, scheduling, interfaces, protocols, gating, and toolchains",
        },
    },
    {
        "id": "technology-and-engineering",
        "title": {"zh": "技术与工程", "en": "Technology and Engineering"},
        "page": "docs/zh/discoveries/categories/technology-and-engineering.md",
        "seed_keywords": ["技术", "工程", "架构", "实现", "算法", "控制", "部署", "性能", "优化", "并发", "缓存", "标度", "系统设计"],
        "problem_domain": {
            "zh": "架构、实现、算法、工程、控制与性能",
            "en": "Architecture, implementation, algorithms, engineering, control, and performance",
        },
    },
    {
        "id": "education-and-learning",
        "title": {"zh": "教育与学习", "en": "Education and Learning"},
        "page": "docs/zh/discoveries/categories/education-and-learning.md",
        "seed_keywords": ["教育", "学习", "教学", "训练", "课程", "学生", "老师", "复习", "课堂", "考试", "练习", "学习者"],
        "problem_domain": {
            "zh": "学习、训练、教学、验证、复习与认知发展",
            "en": "Learning, training, teaching, validation, review, and cognitive development",
        },
    },
    {
        "id": "ecology-and-environment",
        "title": {"zh": "生态与环境", "en": "Ecology and Environment"},
        "page": "docs/zh/discoveries/categories/ecology-and-environment.md",
        "seed_keywords": ["生态", "环境", "气候", "污染", "自然", "循环", "可持续", "资源", "物种", "灭绝"],
        "problem_domain": {
            "zh": "生态、环境、循环、资源、气候与可持续性",
            "en": "Ecology, environment, cycles, resources, climate, and sustainability",
        },
    },
    {
        "id": "other",
        "title": {"zh": "其他", "en": "Other"},
        "page": "docs/zh/discoveries/categories/other.md",
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


def safe_english(text: str) -> str:
    if not text:
        return ""
    if CJK_RE.search(text):
        return "Rule-based English rendering pending human review."
    return text


def parse_csv_ids(value: str) -> list[str]:
    items = []
    for raw in value.split(","):
        token = raw.strip()
        if token:
            items.append(token)
    return items


def normalize_case_token(token: str) -> tuple[str, str]:
    raw = token.strip()
    if not raw:
        return "", ""
    numeric = re.fullmatch(r"#?(\d+)", raw)
    if numeric:
        seq = int(numeric.group(1))
        return f"#{seq}", f"C-{seq:04d}"
    normalized = re.fullmatch(r"C-(\d{4})", raw.upper())
    if normalized:
        seq = int(normalized.group(1))
        return f"#{seq}", f"C-{seq:04d}"
    return raw, raw


def next_discovery_id(items: list[dict]) -> str:
    max_num = 0
    for item in items:
        match = DISCOVERY_ID_RE.match(item.get("id", ""))
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"DISC-{max_num + 1:04d}"


def load_function_map() -> dict[str, dict]:
    items = read_json(FUNC_JSON, [])
    mapping: dict[str, dict] = {}
    for item in items:
        mapping[item["id"].upper()] = item
        normalized = item.get("normalized_id")
        if normalized:
            mapping[str(normalized).upper()] = item
    return mapping


def load_case_map() -> dict[str, dict]:
    items = read_json(CASE_JSON, [])
    mapping: dict[str, dict] = {}
    for item in items:
        mapping[item["normalized_id"].upper()] = item
        raw_id = item.get("id")
        if raw_id:
            mapping[str(raw_id).upper()] = item
    return mapping


def build_related_functions(ids: list[str], func_map: dict[str, dict]) -> tuple[list[dict], list[str]]:
    related = []
    warnings = []
    seen = set()
    for fid in ids:
        key = fid.upper()
        if key in seen:
            continue
        seen.add(key)
        func = func_map.get(key)
        if func:
            related.append(
                {
                    "id": func["id"],
                    "title": func["title"],
                    "page": func["links"]["human_page"],
                    "found": True,
                }
            )
        else:
            warnings.append(f"warning: function {fid} not found in unified-functions.json")
            related.append(
                {
                    "id": fid,
                    "title": {
                        "zh": f"{fid}（未在当前函数表中找到 / Not found in the current function table）",
                        "en": f"{fid} (not found in the current function table)",
                    },
                    "page": None,
                    "found": False,
                }
            )
    return related, warnings


def build_related_cases(ids: list[str], case_map: dict[str, dict]) -> tuple[list[dict], list[str]]:
    related = []
    warnings = []
    seen = set()
    for token in ids:
        display_id, normalized = normalize_case_token(token)
        key = normalized.upper()
        if key in seen:
            continue
        seen.add(key)
        case = case_map.get(key)
        if case:
            related.append(
                {
                    "id": display_id,
                    "normalized_id": case["normalized_id"],
                    "title": case["title"],
                    "page": case["links"]["human_page"],
                    "found": True,
                }
            )
        else:
            warnings.append(f"warning: case {token} not found in unified-cases.json")
            related.append(
                {
                    "id": display_id,
                    "normalized_id": normalized,
                    "title": {
                        "zh": f"{token}（未在当前案例表中找到 / Not found in the current case table）",
                        "en": f"{token} (not found in the current case table)",
                    },
                    "page": None,
                    "found": False,
                }
            )
    return related, warnings


def resolve_categories(category_ids: Iterable[str]) -> list[dict]:
    resolved = []
    seen = set()
    ids = list(category_ids)
    if not ids:
        ids = ["other"]
    for raw in ids:
        key = raw.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        entry = CATEGORY_LOOKUP.get(key)
        if not entry:
            raise SystemExit(f"unknown category id: {raw}")
        resolved.append(
            {
                "id": entry["id"],
                "title": entry["title"],
                "page": entry["page"],
            }
        )
    if not resolved:
        other = CATEGORY_LOOKUP["other"]
        resolved = [{"id": other["id"], "title": other["title"], "page": other["page"]}]
    return resolved


def _normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value or "")


def _field_text(item: dict, field: str) -> str:
    value = item.get(field, "")
    if isinstance(value, dict):
        return " ".join(_normalize_text(str(v)) for v in value.values() if v)
    if isinstance(value, list):
        return " ".join(_normalize_text(str(v)) for v in value if v)
    return _normalize_text(str(value))


def item_text_blob(item: dict, extra: str = "") -> str:
    parts = [
        _field_text(item, "title"),
        _field_text(item, "content"),
        _field_text(item, "explanation"),
        _field_text(item, "source"),
        extra,
    ]
    return " ".join(part for part in parts if part)


def _count_keyword_hits(text: str, keywords: list[str]) -> tuple[int, Counter]:
    lowered = text.lower()
    total = 0
    matched = Counter()
    for keyword in keywords:
        token = keyword.lower()
        if not token:
            continue
        occurrences = lowered.count(token)
        if occurrences:
            total += occurrences
            matched[keyword] += occurrences
    return total, matched


def score_item_for_category(item: dict, category: dict) -> tuple[int, Counter]:
    if category["id"] == "other":
        return 0, Counter()

    title_text = _field_text(item, "title")
    content_text = _field_text(item, "content")
    explanation_text = _field_text(item, "explanation")
    source_text = _field_text(item, "source")

    score = 0
    matched = Counter()
    for weight, text in ((4, title_text), (2, content_text), (2, explanation_text), (1, source_text)):
        field_score, field_hits = _count_keyword_hits(text, category["seed_keywords"])
        if field_score:
            score += field_score * weight
            matched.update(field_hits)

    return score, matched


def _category_rank(category_id: str) -> int:
    for idx, entry in enumerate(CATEGORY_DEFINITIONS):
        if entry["id"] == category_id:
            return idx
    return len(CATEGORY_DEFINITIONS)


def _sorted_category_ids(category_ids: Iterable[str]) -> list[str]:
    unique = []
    seen = set()
    for category_id in category_ids:
        if category_id in seen:
            continue
        seen.add(category_id)
        unique.append(category_id)
    return sorted(unique, key=_category_rank)


def classify_bootstrap_items(functions: list[dict], cases: list[dict]) -> dict:
    items = []
    function_by_id = {}
    case_by_id = {}
    for func in functions:
        record = {
            "kind": "function",
            "id": func["id"],
            "normalized_id": func.get("normalized_id", func["id"]),
            "title": func["title"],
            "page": func["links"]["human_page"],
            "item": func,
        }
        items.append(record)
        function_by_id[str(func["id"]).upper()] = record
        function_by_id[str(func.get("normalized_id", func["id"])).upper()] = record
    for case in cases:
        record = {
            "kind": "case",
            "id": case["id"],
            "normalized_id": case["normalized_id"],
            "title": case["title"],
            "page": case["links"]["human_page"],
            "item": case,
        }
        items.append(record)
        case_by_id[str(case["id"]).upper()] = record
        case_by_id[str(case["normalized_id"]).upper()] = record

    direct_scores: dict[str, Counter] = {}
    matched_terms: dict[str, dict[str, Counter]] = {}
    category_items: dict[str, set[str]] = defaultdict(set)
    item_categories: dict[str, set[str]] = {}

    for record in items:
        key = f"{record['kind']}:{record['normalized_id']}"
        direct_scores[key] = Counter()
        matched_terms[key] = {}
        for category in CATEGORY_DEFINITIONS:
            score, hits = score_item_for_category(record["item"], category)
            if score > 0:
                direct_scores[key][category["id"]] = score
                matched_terms[key][category["id"]] = hits
        initial = {cid for cid, score in direct_scores[key].items() if score > 0}
        if not initial:
            initial = {"other"}
        item_categories[key] = set(initial)
        for cid in initial:
            category_items[cid].add(key)

    adjacency: dict[str, set[str]] = defaultdict(set)
    for func in functions:
        source = f"function:{func.get('normalized_id', func['id'])}"
        related_cases = func.get("related_cases", []) or []
        for related in related_cases:
            normalized = related.get("normalized_id")
            if normalized:
                target = f"case:{normalized}"
                adjacency[source].add(target)
                adjacency[target].add(source)
    for case in cases:
        source = f"case:{case['normalized_id']}"
        related_functions = case.get("related_functions", []) or []
        for related in related_functions:
            normalized = related.get("normalized_id") or related.get("id")
            if normalized:
                target = f"function:{normalized}"
                adjacency[source].add(target)
                adjacency[target].add(source)

    # Three bootstrap rounds:
    # 1) direct keyword hits
    # 2) relation propagation from strongly matched neighbors
    # 3) merge low-confidence propagation and finalise each item's category set
    propagated_votes: dict[str, Counter] = {key: Counter() for key in item_categories}
    for _round in range(2):
        round_votes: dict[str, Counter] = {key: Counter() for key in item_categories}
        for source_key, categories in item_categories.items():
            source_direct = direct_scores[source_key]
            strong_categories = {
                cid
                for cid in categories
                if cid != "other" and (source_direct.get(cid, 0) >= 2 or len(categories) > 1)
            }
            if not strong_categories:
                continue
            for target_key in adjacency.get(source_key, set()):
                if target_key not in round_votes:
                    continue
                for cid in strong_categories:
                    round_votes[target_key][cid] += 1
        for target_key, votes in round_votes.items():
            for cid, vote_count in votes.items():
                if cid == "other":
                    continue
                if vote_count >= 2 or (vote_count >= 1 and direct_scores[target_key].get(cid, 0) > 0):
                    propagated_votes[target_key][cid] += vote_count
                    item_categories[target_key].add(cid)

    # Final reconciliation.
    for key, categories in list(item_categories.items()):
        final_categories = {cid for cid in categories if cid != "other"}
        if not final_categories:
            final_categories = {"other"}
        item_categories[key] = final_categories
        for cid in final_categories:
            category_items[cid].add(key)

    return {
        "items": items,
        "direct_scores": direct_scores,
        "matched_terms": matched_terms,
        "item_categories": item_categories,
        "category_items": category_items,
        "adjacency": adjacency,
        "propagated_votes": propagated_votes,
    }


def _display_item_id(record: dict) -> str:
    if record["kind"] == "case":
        return record["item"]["normalized_id"]
    return record["item"]["id"]


def _category_entry_base(category_id: str) -> dict:
    definition = CATEGORY_LOOKUP[category_id]
    return {
        "category_id": category_id,
        "title": copy.deepcopy(definition["title"]),
        "page": definition["page"],
        "problem_domains": [copy.deepcopy(definition["problem_domain"])],
        "related_functions": [],
        "related_cases": [],
        "curated_discoveries": [],
        "discovery_leads": [],
        "coverage": {
            "related_functions_count": 0,
            "related_cases_count": 0,
            "curated_discoveries_count": 0,
            "discovery_leads_count": 0,
        },
    }


def build_category_map(functions: list[dict], cases: list[dict], classification: dict) -> list[dict]:
    items_by_key = {f"function:{record['normalized_id']}": record for record in classification["items"] if record["kind"] == "function"}
    items_by_key.update({f"case:{record['normalized_id']}": record for record in classification["items"] if record["kind"] == "case"})

    category_map: list[dict] = []
    for category in CATEGORY_DEFINITIONS:
        entry = _category_entry_base(category["id"])
        function_rows = []
        case_rows = []
        keyword_counter = Counter()

        for key in classification["category_items"].get(category["id"], set()):
            record = items_by_key[key]
            display_id = _display_item_id(record)
            title = copy.deepcopy(record["title"])
            score = classification["direct_scores"][key].get(category["id"], 0)
            matched = classification["matched_terms"][key].get(category["id"], Counter())
            keyword_counter.update(matched)
            row = {
                "id": display_id,
                "title": title,
                "page": record["page"],
                "score": score,
            }
            if record["kind"] == "function":
                function_rows.append(row)
            else:
                row["normalized_id"] = record["item"]["normalized_id"]
                case_rows.append(row)

        function_rows.sort(key=lambda row: (-row["score"], row["id"]))
        case_rows.sort(key=lambda row: (-row["score"], row["id"]))

        top_items = []
        for row in function_rows[:3]:
            top_items.append(("function", row))
        for row in case_rows[:3]:
            top_items.append(("case", row))

        leads = []
        for kind, row in top_items[:5]:
            if kind == "function":
                lead_zh = f"{row['id']}｜{row['title']['zh']} 仍可继续整理为 {entry['title']['zh']} 方向的独立发现。"
                lead_en = f"{row['id']} | {row['title']['en']} remains a curation lead in {entry['title']['en']}."
                leads.append(
                    {
                        "zh": lead_zh,
                        "en": lead_en,
                        "related_functions": [row["id"]],
                        "related_cases": [],
                        "status": "lead",
                    }
                )
            else:
                lead_zh = f"{row['id']}｜{row['title']['zh']} 仍可继续整理为 {entry['title']['zh']} 方向的独立发现。"
                lead_en = f"{row['id']} | {row['title']['en']} remains a curation lead in {entry['title']['en']}."
                leads.append(
                    {
                        "zh": lead_zh,
                        "en": lead_en,
                        "related_functions": [],
                        "related_cases": [row["normalized_id"]],
                        "status": "lead",
                    }
                )

        if not keyword_counter:
            keyword_counter.update(entry["problem_domains"][0]["zh"].split("、"))

        # Ensure the lead text remains conservative and traceable.
        if len(leads) < 3:
            for row in function_rows[3:5]:
                leads.append(
                    {
                        "zh": f"{row['id']}｜{row['title']['zh']} 是 {entry['title']['zh']} 分类下的补充入口。",
                        "en": f"{row['id']} | {row['title']['en']} is a supplemental entry in {entry['title']['en']}.",
                        "related_functions": [row["id"]],
                        "related_cases": [],
                        "status": "lead",
                    }
                )

        entry["related_functions"] = function_rows
        entry["related_cases"] = case_rows
        entry["coverage"]["related_functions_count"] = len(function_rows)
        entry["coverage"]["related_cases_count"] = len(case_rows)
        entry["coverage"]["discovery_leads_count"] = len(leads)
        entry["discovery_leads"] = leads
        entry["curated_discoveries"] = []
        if category["id"] == "other" and not function_rows and not case_rows:
            entry["problem_domains"] = [copy.deepcopy(category["problem_domain"])]
        else:
            # Keep a single concise bootstrap summary and let the counts speak for themselves.
            entry["problem_domains"] = [copy.deepcopy(category["problem_domain"])]
        category_map.append(entry)

    return category_map


def discovery_page_categories(item: dict) -> list[dict]:
    return resolve_categories([cat["id"] for cat in item.get("categories", [])])


def _related_ref_label(entry: dict, case: bool = False) -> str:
    if case:
        rid = entry.get("normalized_id") or entry.get("id") or ""
    else:
        rid = entry.get("id") or entry.get("function_id") or ""
    title = (entry.get("title") or {}).get("zh") or rid
    return f"{rid}（{title}）" if title and title != rid else rid


def _related_ref_ids(item: dict, key: str, case: bool = False) -> list[str]:
    ids = []
    for entry in item.get(key, []) or []:
        if isinstance(entry, dict):
            value = entry.get("normalized_id") if case else (entry.get("id") or entry.get("function_id"))
            value = value or entry.get("id")
        else:
            value = str(entry)
        if value and value not in ids:
            ids.append(value)
    return ids


def _discovery_page_chain(item: dict) -> dict[str, str]:
    did = item["id"]
    title = item["title"].get("zh") or did
    category = ", ".join(cat["title"].get("zh", cat["id"]) for cat in item.get("categories", [])) or "未分类"
    functions = item.get("related_functions", []) or []
    cases = item.get("related_cases", []) or []
    function_labels = "、".join(_related_ref_label(entry) for entry in functions[:4])
    case_labels = "、".join(_related_ref_label(entry, case=True) for entry in cases[:4])
    if functions and cases:
        zh = (
            f"本发现把 {function_labels} 与 {case_labels} 放入同一个可审计对象：函数侧提供机制、变量或约束，案例侧提供状态见证。"
            f"推导先检查这些对象能否回指到源页，再把它们在“{category}”问题域中的共同结构写作信息增益 ΔI_{{{did}}}。"
            f"若 ΔI_{{{did}}} 高于阈值且内部反向检查未发现冲突，则保留为待学术独有性检索的发现线索；这仍是推论，不是定论。"
        )
        en = (
            f"This discovery places {function_labels} and {case_labels} into one auditable object: functions provide mechanisms, variables, or constraints, while cases provide state witnesses. "
            f"The derivation first checks source traceability, then records their shared structure in the {category} domain as information gain ΔI_{{{did}}}. "
            "If the gain clears the threshold and the internal reverse check finds no conflict, the item remains a discovery lead pending academic novelty review; this is an inference, not a conclusion."
        )
    elif functions:
        zh = (
            f"本发现来自 {function_labels} 的机制抽象。推导先读取相关函数的标题、定义、数学表达和依赖关系，"
            f"再判断该机制在“{category}”问题域中是否形成独立可审计的结构洞见。由于当前没有明确案例见证，"
            f"页面只给出机制侧发现线索，后续仍需案例补证与学术独有性检索；这不是 active 结论。"
        )
        en = (
            f"This discovery is derived from the mechanism abstraction of {function_labels}. The derivation reads the related function titles, definitions, mathematical expressions, and dependencies, "
            f"then checks whether the mechanism forms an auditable structural insight in the {category} domain. Because no explicit case witness is attached yet, the page records a function-side discovery lead only; case support and academic novelty review are still required."
        )
    elif cases:
        zh = (
            f"本发现来自 {case_labels} 的案例状态。推导先把案例描述编码为状态见证，抽取其中可复核的函数线索或结构模式，"
            f"再判断该模式是否足以成为“{category}”方向的发现候选。当前不补造函数，也不把案例写成证明；"
            f"页面只保留案例触发的推论路径。"
        )
        en = (
            f"This discovery is derived from the case state of {case_labels}. The derivation encodes the case description as a state witness, extracts auditable function clues or structural patterns, "
            f"and checks whether the pattern can stand as a {category} discovery candidate. It does not synthesize functions or treat the case as proof; it records a case-triggered inference path."
        )
    else:
        zh = (
            f"本发现暂时只有来源笔记和分类线索。推导先保留 {title} 的来源回指，再等待函数、案例或数学表达补齐后重新计算 ΔI_{{{did}}}。"
            "当前状态只能作为待复核发现线索。"
        )
        en = (
            f"This discovery currently has only source-note and category traces. The derivation preserves the source reference for {title} and waits for related functions, cases, or mathematical expressions before recomputing ΔI_{{{did}}}. "
            "The current state is a reviewable discovery lead only."
        )
    return {"zh": zh, "en": en}


def _discovery_page_derivation(item: dict, derivation: dict) -> dict:
    did = item["id"]
    fids = _related_ref_ids(item, "related_functions")
    cids = _related_ref_ids(item, "related_cases", case=True)
    deps = fids + cids
    function_set = "{" + ", ".join(fids) + "}" if fids else "∅"
    case_set = "{" + ", ".join(cids) + "}" if cids else "∅"
    if fids and cids:
        support_step = f"3. Compute ΔI_{{{did}}}=I(structure | F={function_set}, C={case_set})-I(prior | category) and keep the item only as an inference lead."
    elif fids:
        support_step = f"3. Compute ΔI_{{{did}}}=I(structure | F={function_set})-I(prior | category); because C=∅, mark the case side as support pending."
    elif cids:
        support_step = f"3. Compute ΔI_{{{did}}}=I(pattern | C={case_set})-I(prior | category); because F=∅, do not synthesize a function."
    else:
        support_step = f"3. Keep ΔI_{{{did}}} pending until at least one related function or case becomes traceable."
    return {
        "kind": derivation.get("kind") or "discovery_information_gain_derivation",
        "status": derivation.get("status") or "internal_page_derivation_completed",
        "depends_on": deps,
        "steps_math": [
            f"1. Trace the discovery object D_{{{did}}} back to its source note, category, and human page.",
            f"2. Build the evidence pair (F,C) with F={function_set} and C={case_set}; missing sides are left empty rather than fabricated.",
            support_step,
            f"4. Accept the page-level derivation only as inference_not_conclusion when J_n^+(D_{{{did}}})=1 and the internal reverse check does not find contradiction.",
            "5. Leave external novelty, active status, and migration decisions to later academic search and dual-channel bootstrap tasks.",
        ],
        "proof_obligations": [
            "source_reference_traceable",
            "related_object_traceable_or_explicitly_empty",
            "information_gain_boundary_declared",
            "inference_not_conclusion",
            "external_novelty_still_inconclusive",
        ],
        "forward_check": {"condition": f"J_n^+(D_{{{did}}})=1 ∧ trace(F,C,source)=true"},
        "reverse_check": {"condition": f"J_n^-(D_{{{did}}})=0 under internal duplicate/conflict scan"},
        "convergence": f"PageDerivation(D_{{{did}}}) ⇔ trace(source)=true ∧ ΔI_{{{did}}} declared ∧ inference_not_conclusion=true",
    }


def render_discovery_page(item: dict) -> str:
    current_path = DISCOVERY_DIR / "items" / f"{item['id']}.md"
    formal = item.get("mathematical_formalization") or {}
    derivation = item.get("mathematical_derivation") or {}
    page_chain = _discovery_page_chain(item)
    page_derivation = _discovery_page_derivation(item, derivation)
    lines = [
        f"# {item['id']}｜{format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}",
        "",
        f"[← 返回发现总表 / Back to Discoveries]({rel_link(current_path, DISCOVERY_LIST_MD)})",
        f"[返回仓库首页 / Back to Repository Home]({rel_link(current_path, REPO_ROOT / 'README.md')})",
        "",
        "## 基本信息 / Basic Information",
        "",
        f"- 发现编号 / Discovery ID：{item['id']}",
        f"- 中文标题 / Chinese title：{item['title']['zh']}",
        f"- English title：{item['title']['en']}",
        f"- 状态 / Status：{item['status']}",
        f"- 日期 / Date：{item['source']['date']}",
        f"- 来源 / Source：{item['source']['source_note'] or item['source']['conversation'] or '—'}",
        "",
        "## 分类 / Categories",
        "",
    ]

    categories = item.get("categories", [])
    if categories:
        for cat in categories:
            lines.append(f"- {format_bilingual_title(cat['title'].get('zh'), cat['title'].get('en'))}")
    else:
        lines.extend(["- 其他 / Other"])

    lines.extend(
        [
            "",
            "## 发现内容 / Discovery",
            "",
            "中文：",
            item["content"]["zh"],
            "",
            "English:",
            safe_english(item["content"]["en"]),
            "",
            "## 它为什么重要 / Why It Matters",
            "",
            "中文：",
            item["why_it_matters"]["zh"],
            "",
            "English:",
            safe_english(item["why_it_matters"]["en"]),
            "",
            "## 推论链条 / Inference Chain",
            "",
            "中文：",
            page_chain["zh"],
            "",
            "English:",
            page_chain["en"],
            "",
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
            f"- 推导类型 / Derivation type: `{page_derivation.get('kind', '')}`",
            f"- 收敛状态 / Convergence status: `{page_derivation.get('status', '')}`",
            f"- 依赖 / Depends on: {', '.join(f'`{dep}`' for dep in page_derivation.get('depends_on', [])) if page_derivation.get('depends_on') else '`source_state`'}",
            "- 推导步骤 / Steps:",
            *(f"  - {step}" for step in page_derivation.get("steps_math", [])),
            "- 证明义务 / Proof obligations:",
            *(f"  - `{obligation}`" for obligation in page_derivation.get("proof_obligations", [])),
            f"- 正向检查 / Forward check: `{(page_derivation.get('forward_check') or {}).get('condition', '')}`",
            f"- 反向检查 / Reverse check: `{(page_derivation.get('reverse_check') or {}).get('condition', '')}`",
            f"- 收敛判据 / Convergence: `{page_derivation.get('convergence', '')}`",
            "",
            "## 相关函数 / Related Functions",
            "",
        ]
    )

    related_functions = item.get("related_functions", [])
    if related_functions:
        for entry in related_functions:
            if entry.get("found") and entry.get("page"):
                lines.append(
                    f"- [{entry['id']}｜{format_bilingual_title(entry['title'].get('zh'), entry['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / entry['page'])})"
                )
            else:
                lines.append(f"- {entry['title']['zh']}")
    else:
        lines.extend(["暂无明确相关函数。", "No explicit related functions yet."])

    lines.extend(["", "## 相关案例 / Related Cases", ""])
    related_cases = item.get("related_cases", [])
    if related_cases:
        for entry in related_cases:
            if entry.get("found") and entry.get("page"):
                lines.append(
                    f"- [{entry['id']}｜{format_bilingual_title(entry['title'].get('zh'), entry['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / entry['page'])})"
                )
            else:
                lines.append(f"- {entry['title']['zh']}")
    else:
        lines.extend(["暂无明确相关案例。", "No explicit related cases yet."])

    lines.extend(
        [
            "",
            "## 来源回指 / Source Reference",
            "",
            f"- 对话来源 / Conversation source：{item['source']['conversation'] or '—'}",
            f"- 笔记来源 / Source note：{item['source']['source_note'] or '—'}",
            f"- 相关提交 / Related commit：{item['source']['related_commit'] or '—'}",
            "",
        ]
    )
    return "\n".join(lines)


def render_discoveries_list(items: list[dict], categories: list[dict] | None = None) -> str:
    lines = [
        "# 发现总表 / Discovery Index",
        "",
        "中文：这里收录《点火》框架在函数、案例与自举循环中产生的新发现。每条发现都应该独立成条，并连接到相关函数、案例、来源与推论链条。",
        "",
        "English: This index collects new discoveries generated by the Ignition framework through functions, cases, and bootstrap cycles. Each discovery should be recorded as an independent entry and linked to related functions, cases, sources, and inference chains.",
        "",
        "## 如何新增发现 / How to Add a Discovery",
        "",
        "中文：每跑出一个新发现，新增一条发现记录，不要把新发现塞进函数表或案例表里。函数表保存机制，案例表保存证据，发现表保存由机制和证据共同推出的新洞见。",
        "",
        "English: Whenever a new discovery is produced, add it as a separate discovery entry. Do not bury discoveries inside the function table or case table. The function table stores mechanisms, the case table stores evidence, and the discovery table stores new insights derived from mechanisms and evidence.",
        "",
        "模板 / Template：[`docs/zh/discoveries/DISCOVERY_TEMPLATE.md`](docs/zh/discoveries/DISCOVERY_TEMPLATE.md)",
        "",
    ]

    lines.extend(
        [
            "## 发现列表 / Discoveries",
            "",
            "<!-- DISCOVERY_LIST_START -->",
        ]
    )
    if items:
        for item in items:
            category_tags = ""
            if item.get("categories"):
                category_tags = " · " + ", ".join(cat["title"]["en"] for cat in item["categories"])
            novelty_status = item.get("academic_novelty", {}).get("status", "pending")
            lines.append(
                f"- [{item['id']}｜{format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}]({item['links']['human_page']}) — novelty: {novelty_status}{category_tags}"
            )
    else:
        lines.append("暂无已整理发现。")
        lines.append("No curated discoveries yet.")
    lines.append("<!-- DISCOVERY_LIST_END -->")
    lines.append("")
    return "\n".join(lines)


def render_discovery_index_md(items: list[dict]) -> str:
    rows = []
    for item in items:
        categories = ", ".join(cat["title"]["en"] for cat in item.get("categories", [])) or "other"
        novelty = item.get("academic_novelty", {}).get("status", "pending")
        rows.append(
            [
                item["id"],
                f"[{format_bilingual_title(item['title'].get('zh'), item['title'].get('en'))}]({item['links']['human_page']})",
                categories,
                item["status"],
                novelty,
                str(len(item.get("related_functions", []))),
                str(len(item.get("related_cases", []))),
            ]
        )
    table = [
        "| 编号 / ID | 标题 / Title | 分类 / Categories | 状态 / Status | 学术独有性 / Academic novelty | 相关函数 / Related functions | 相关案例 / Related cases |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    table.extend("| " + " | ".join(row) + " |" for row in rows)
    if not rows:
        table.extend(["", "暂无条目 / No entries yet.", ""])
    return "\n".join(
        [
            "# 发现机器索引 / Discovery Machine Index",
            "",
            "机器可读索引，保留中文标题、英文标题、分类、状态和关联计数。",
            "Machine-readable index that keeps Chinese titles, English titles, categories, status, and relation counts.",
            "",
            "- [`data/discoveries/unified-discoveries.json`](unified-discoveries.json)",
            "- [`data/discoveries/unified-discoveries.jsonl`](unified-discoveries.jsonl)",
            "",
            *table,
            "",
        ]
    )


def render_category_page(category: dict) -> str:
    current_path = CATEGORY_DIR / f"{category['category_id']}.md"
    lines = [
        f"# {format_bilingual_title(category['title'].get('zh'), category['title'].get('en'))}",
        "",
        f"[← 返回发现总表 / Back to Discoveries]({rel_link(current_path, DISCOVERY_LIST_MD)})",
        f"[返回仓库首页 / Back to Repository Home]({rel_link(current_path, REPO_ROOT / 'README.md')})",
        "",
        f"中文：本页收录《点火》框架在{category['title']['zh']}相关问题上形成的发现入口。这里不是传统学科教材，而是函数、案例与自举循环在该问题域里生成的解释结构。",
        "",
        f"English: This page collects discovery entrances formed by the Ignition framework in the {category['title']['en']} problem domain. It is not a conventional textbook, but an explanatory structure generated by functions, cases, and bootstrap cycles within this domain.",
        "",
        "## 已触及的问题域 / Problem Domains Already Touched",
        "",
    ]
    for domain in category.get("problem_domains", []):
        lines.append(f"- 中文：{domain['zh']}")
        lines.append(f"  English: {domain['en']}")

    lines.extend(["", "## 相关函数 / Related Functions", ""])
    related_functions = category.get("related_functions", [])
    if related_functions:
        for row in related_functions[:30]:
            lines.append(
                f"- [{row['id']}｜{format_bilingual_title(row['title'].get('zh'), row['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / row['page'])})"
            )
        if len(related_functions) > 30:
            lines.append(f"- ... and {len(related_functions) - 30} more / 还有 {len(related_functions) - 30} 项")
    else:
        lines.extend(["暂无相关函数。", "No related functions yet."])

    lines.extend(["", "## 相关案例 / Related Cases", ""])
    related_cases = category.get("related_cases", [])
    if related_cases:
        for row in related_cases[:30]:
            lines.append(
                f"- [{row['normalized_id']}｜{format_bilingual_title(row['title'].get('zh'), row['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / row['page'])})"
            )
        if len(related_cases) > 30:
            lines.append(f"- ... and {len(related_cases) - 30} more / 还有 {len(related_cases) - 30} 项")
    else:
        lines.extend(["暂无相关案例。", "No related cases yet."])

    lines.extend(["", "## 已整理发现 / Curated Discoveries", "", f"<!-- CATEGORY_DISCOVERY_LIST_START:{category['category_id']} -->"])
    curated = category.get("curated_discoveries", [])
    if curated:
        for discovery in curated:
            lines.append(
                f"- [{discovery['id']}｜{format_bilingual_title(discovery['title'].get('zh'), discovery['title'].get('en'))}]({rel_link(current_path, REPO_ROOT / discovery['page'])})"
            )
    else:
        lines.extend(["暂无已整理发现。", "No curated discoveries yet."])
    lines.append(f"<!-- CATEGORY_DISCOVERY_LIST_END:{category['category_id']} -->")

    lines.extend(
        [
            "",
            "## 待整理发现线索 / Discovery Leads to Curate",
            "",
            "中文：以下线索来自函数与案例的自举分类，不等于已发布发现，需要后续整理成独立 discovery 条目。",
            "",
            "English: The following leads come from bootstrap classification between functions and cases. They are not yet published discoveries and need later curation into independent discovery entries.",
            "",
        ]
    )
    leads = category.get("discovery_leads", [])
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
            f"- 已整理发现 / Curated discoveries：{category['coverage']['curated_discoveries_count']}",
            f"- 待整理线索 / Discovery leads：{category['coverage']['discovery_leads_count']}",
            "",
        ]
    )
    return "\n".join(lines)


def render_bootstrap_report(category_map: list[dict]) -> str:
    def sort_key(category: dict) -> tuple[int, int, int, str]:
        coverage = category["coverage"]
        curated = coverage.get("curated_discoveries_count", 0)
        leads = coverage.get("discovery_leads_count", 0)
        related_total = coverage.get("related_functions_count", 0) + coverage.get("related_cases_count", 0)
        return (-curated, -leads, -related_total, category["category_id"])

    lines = [
        "# 自举分类报告 / Bootstrap Category Report",
        "",
        "中文：本报告记录函数—案例—发现自举循环对学科入口的扫描结果。分类不是空壳，而是基于当前函数与案例表的可见覆盖生成。",
        "",
        "English: This report records the bootstrap scan of the function-case-discovery cycle over disciplinary entrances. The categories are not empty shells; they are generated from the visible coverage in the current function and case tables.",
        "",
        "## 汇总 / Summary",
        "",
        f"- 分类总数 / Total categories：{len(category_map)}",
        f"- 函数总数 / Total functions：{len(read_json(FUNC_JSON, []))}",
        f"- 案例总数 / Total cases：{len(read_json(CASE_JSON, []))}",
        "",
        "| 分类 / Category | 相关函数 / Related functions | 相关案例 / Related cases | 待整理线索 / Leads |",
        "| --- | --- | --- | --- |",
    ]
    for entry in sorted([entry for entry in category_map if entry["category_id"] != "other"], key=sort_key):
        lines.append(
            f"| {format_bilingual_title(entry['title'].get('zh'), entry['title'].get('en'))} | {entry['coverage']['related_functions_count']} | {entry['coverage']['related_cases_count']} | {entry['coverage']['discovery_leads_count']} |"
        )
    lines.extend(["", "## 说明 / Notes", "", "1. 第 1 轮：按关键词和标题粗分学科。", "2. 第 2 轮：通过 related_functions / related_cases 传播分类。", "3. 第 3 轮：合并低置信分类，生成每个学科的问题域地图。", ""])
    return "\n".join(lines)


def update_category_map_with_discovery(category_map: list[dict], discovery: dict) -> list[dict]:
    category_lookup = {entry["category_id"]: entry for entry in category_map}
    discovery_categories = discovery.get("categories", [])
    for category in discovery_categories:
        entry = category_lookup.get(category["id"])
        if not entry:
            continue
        curated = entry.setdefault("curated_discoveries", [])
        if any(existing.get("id") == discovery["id"] for existing in curated):
            continue
        curated.append(
            {
                "id": discovery["id"],
                "title": copy.deepcopy(discovery["title"]),
                "page": discovery["links"]["human_page"],
                "status": discovery.get("status", "draft"),
            }
        )
        curated.sort(key=lambda row: row["id"])
        entry["coverage"]["curated_discoveries_count"] = len(curated)
    return [category_lookup[entry["category_id"]] for entry in category_map]
