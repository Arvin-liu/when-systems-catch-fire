#!/usr/bin/env python3
"""Validate the Ignition repository's dynamic counts, sorting, and gates."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from build_predictions_from_bootstrap import (
    PREDICTIONS_HUMAN_MD,
    PREDICTION_BLUEPRINTS,
    build_category_defs,
    build_maps,
    build_category_map,
    enrich_prediction,
    render_index as render_prediction_index,
    render_machine_index,
)
from answer_utils import (
    ANSWERS_INDEX_MD,
    ANSWERS_JSON,
    ANSWERS_LIST_MD,
    ANSWER_TEMPLATE_MD,
    CATEGORY_MAP_JSON as ANSWERS_CATEGORY_MAP_JSON,
    CATEGORY_DEFINITIONS as ANSWER_CATEGORY_DEFINITIONS,
    build_category_map as build_answer_category_map,
    render_answer_index,
    render_answer_index_md,
    render_answer_page,
    render_category_page as render_answer_category_page,
    read_json as read_answer_json,
)
from discovery_category_utils import (
    BOOTSTRAP_REPORT_MD,
    CATEGORY_MAP_JSON,
    DISCOVERY_INDEX_MD,
    DISCOVERY_LIST_MD,
    read_json as read_discovery_json,
    render_bootstrap_report,
    render_discoveries_list,
    render_discovery_index_md,
)
from repository_overview_utils import (
    README,
    count_repository_objects,
    readme_overview_matches,
)
from render_human_entry_from_unified_md import (
    CASE_SOURCE,
    DOC_CASE_INDEX,
    DOC_CASE_DIR,
    DOC_FUNC_INDEX,
    DOC_FUNC_DIR,
    FUNC_SOURCE,
    ROOT_CASES,
    ROOT_FUNCTIONS,
    build_relationships,
    parse_case_table,
    parse_function_table,
    render_cases_collection,
    render_functions_collection,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
META_FUNCTIONS_JSON = REPO_ROOT / "data/functions/meta-functions.json"
META_FUNCTIONS_JSONL = REPO_ROOT / "data/functions/meta-functions.jsonl"
META_FUNCTIONS_INDEX_MD = REPO_ROOT / "data/functions/meta-functions-index.md"
BOOTSTRAP_META_TABLE_MD = REPO_ROOT / "data/functions/bootstrap-meta-function-table.md"
BOOTSTRAP_META_TABLE_JSON = REPO_ROOT / "data/functions/bootstrap-meta-function-table.json"
BOOTSTRAP_META_TABLE_JSONL = REPO_ROOT / "data/functions/bootstrap-meta-function-table.jsonl"
META_FUNCTION_PAGE = REPO_ROOT / "docs/zh/functions/meta/MF-0000.md"
BOOTSTRAP_META_PAGES = [
    REPO_ROOT / "docs/zh/functions/meta/items/MF-0001.md",
    REPO_ROOT / "docs/zh/functions/meta/items/MF-0002.md",
    REPO_ROOT / "docs/zh/functions/meta/items/MF-0003.md",
    REPO_ROOT / "docs/zh/functions/meta/items/MF-0004.md",
    REPO_ROOT / "docs/zh/functions/meta/items/MF-0005.md",
]
DISCOVERIES_JSON = REPO_ROOT / "data/discoveries/unified-discoveries.json"
DISCOVERIES_INDEX_JSON = REPO_ROOT / "data/discoveries/unified-discoveries-index.md"
PREDICTIONS_JSON = REPO_ROOT / "data/predictions/unified-predictions.json"
PREDICTIONS_INDEX_JSON = REPO_ROOT / "data/predictions/unified-predictions-index.md"
ANSWERS_JSON_PATH = REPO_ROOT / "data/answers/unified-answers.json"
ANSWERS_INDEX_JSON = REPO_ROOT / "data/answers/unified-answers-index.md"


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


def check_readme(errors: list[str]) -> None:
    text = README.read_text(encoding="utf-8")
    required = [
        "[发现 / Discoveries](DISCOVERIES.md)",
        "[预测 / Predictions](PREDICTIONS.md)",
        "[新答案 / New Answers](ANSWERS.md)",
        "[函数表 / Functions](FUNCTIONS.md)",
        "[案例表 / Cases](CASES.md)",
    ]
    positions = []
    for marker in required:
        pos = text.find(marker)
        if pos < 0:
            errors.append(f"README.md missing entrance marker {marker}")
        positions.append(pos)
    if all(pos >= 0 for pos in positions) and positions != sorted(positions):
        errors.append("README.md entrance order is incorrect")
    if not readme_overview_matches(README):
        errors.append("README.md repository overview block is out of date")


def check_meta_functions(errors: list[str]) -> dict[str, int]:
    meta_functions = read_discovery_json(META_FUNCTIONS_JSON, [])
    if not isinstance(meta_functions, list):
        errors.append("data/functions/meta-functions.json must contain a list")
        meta_functions = []
    if not META_FUNCTIONS_JSON.exists():
        errors.append("missing generated file: data/functions/meta-functions.json")
    if not META_FUNCTIONS_JSONL.exists():
        errors.append("missing generated file: data/functions/meta-functions.jsonl")
    if not META_FUNCTIONS_INDEX_MD.exists():
        errors.append("missing generated file: data/functions/meta-functions-index.md")
    if not BOOTSTRAP_META_TABLE_MD.exists():
        errors.append("missing generated file: data/functions/bootstrap-meta-function-table.md")
    if not BOOTSTRAP_META_TABLE_JSON.exists():
        errors.append("missing generated file: data/functions/bootstrap-meta-function-table.json")
    if not BOOTSTRAP_META_TABLE_JSONL.exists():
        errors.append("missing generated file: data/functions/bootstrap-meta-function-table.jsonl")
    if not META_FUNCTION_PAGE.exists():
        errors.append("missing generated file: docs/zh/functions/meta/MF-0000.md")
    for page in BOOTSTRAP_META_PAGES:
        if not page.exists():
            errors.append(f"missing generated file: {page.relative_to(REPO_ROOT)}")

    if len(meta_functions) != 1:
        errors.append(f"expected exactly one meta function, found {len(meta_functions)}")
        return {"meta": len(meta_functions), "bootstrap_internal": 0, "ordinary": 0}

    meta = meta_functions[0]
    if meta.get("id") != "MF-0000":
        errors.append(f"bad meta function id: {meta.get('id')}")
    if meta.get("section") != 0:
        errors.append(f"bad meta function section: {meta.get('section')}")
    if meta.get("ordinary_function_counted") is not False:
        errors.append("MF-0000 must not be counted as an ordinary function")
    title = meta.get("title", {})
    if title.get("zh") != "自举元函数" or title.get("en") != "Bootstrap Meta-Function":
        errors.append("MF-0000 title must be 自举元函数 / Bootstrap Meta-Function")
    if meta.get("page") != "docs/zh/functions/meta/MF-0000.md":
        errors.append(f"bad MF-0000 page: {meta.get('page')}")
    if meta.get("source_status") not in {"found", "source_pending"}:
        errors.append(f"bad MF-0000 source_status: {meta.get('source_status')}")
    if not meta.get("source_refs"):
        errors.append("MF-0000 must have source_refs")
    dual = meta.get("dual_channel", {})
    for key in ["forward", "reverse", "exclusivity_judge", "nested_judge", "convergence_judge"]:
        if key not in dual:
            errors.append(f"MF-0000 dual_channel missing {key}")
    if meta.get("bootstrap_table", {}).get("item_count") != 6:
        errors.append(f"MF-0000 bootstrap_table item_count must be 6, found {meta.get('bootstrap_table', {}).get('item_count')}")

    bootstrap_table = read_discovery_json(BOOTSTRAP_META_TABLE_JSON, [])
    if len(bootstrap_table) != 6:
        errors.append(f"expected 6 bootstrap meta items, found {len(bootstrap_table)}")
    else:
        expected_ids = ["MF-0000", "MF-0001", "MF-0002", "MF-0003", "MF-0004", "MF-0005"]
        actual_ids = [item.get("id") for item in bootstrap_table]
        if actual_ids != expected_ids:
            errors.append(f"bootstrap meta item order mismatch: {actual_ids}")
        for item in bootstrap_table:
            if item.get("ordinary_function_counted") is not False:
                errors.append(f"bootstrap meta item must not count as ordinary function: {item.get('id')}")
            if item.get("status") != "active":
                errors.append(f"bootstrap meta item not active: {item.get('id')}")

    page_text = META_FUNCTION_PAGE.read_text(encoding="utf-8") if META_FUNCTION_PAGE.exists() else ""
    required_terms = [
        "第 0 节",
        "自举元函数",
        "Bootstrap Meta-Function",
        "M_boot",
        "ε_sense",
        "P_track",
        "d(ΔK)/dt",
        "B_n",
        "ΔB_n",
        "正反双通道",
        "J⁺",
        "J⁻",
        "contradiction",
        "underdetermined",
        "自举嵌套",
    ]
    for term in required_terms:
        if term not in page_text:
            errors.append(f"MF-0000 page missing term: {term}")

    counts = count_repository_objects()
    if counts["functions"].get("meta") != 1:
        errors.append(f"repository overview meta-function count must be 1, found {counts['functions'].get('meta')}")
    if counts["functions"].get("bootstrap_internal") != 5:
        errors.append(f"repository overview bootstrap internal count must be 5, found {counts['functions'].get('bootstrap_internal')}")
    if counts["functions"].get("ordinary") != 470:
        errors.append(f"repository overview ordinary function count must remain 470, found {counts['functions'].get('ordinary')}")

    return {
        "meta": len(meta_functions),
        "bootstrap_internal": counts["functions"].get("bootstrap_internal", 0),
        "ordinary": counts["functions"].get("ordinary", 0),
    }


def check_discoveries(errors: list[str]) -> dict[str, int]:
    discoveries = read_discovery_json(DISCOVERIES_JSON, [])
    category_map = read_discovery_json(CATEGORY_MAP_JSON, [])
    expected_index = render_discoveries_list(discoveries, category_map)
    current_index = DISCOVERY_LIST_MD.read_text(encoding="utf-8")
    if expected_index != current_index:
        errors.append("DISCOVERIES.md does not match generated discovery index")

    machine_index = render_discovery_index_md(discoveries)
    machine_path = REPO_ROOT / "data/discoveries/unified-discoveries-index.md"
    if machine_index != machine_path.read_text(encoding="utf-8"):
        errors.append("data/discoveries/unified-discoveries-index.md is out of date")

    bootstrap_report = render_bootstrap_report(category_map)
    if bootstrap_report != (REPO_ROOT / "data/discoveries/bootstrap-category-report.md").read_text(encoding="utf-8"):
        errors.append("data/discoveries/bootstrap-category-report.md is out of date")

    return {
        "curated": len(discoveries),
        "leads": sum(len(entry.get("discovery_leads", [])) for entry in category_map),
    }


def check_predictions(errors: list[str]) -> dict[str, int]:
    predictions = read_discovery_json(PREDICTIONS_JSON, [])
    existing_predictions = {item["id"]: item for item in predictions}
    for item in predictions:
        if not re.match(r"^PRED-\d{4}$", item.get("id", "")):
            errors.append(f"bad prediction id: {item.get('id')}")
        if "academic_novelty" not in item:
            errors.append(f"prediction missing academic_novelty: {item.get('id')}")
    category_defs = build_category_defs()
    functions = read_discovery_json(REPO_ROOT / "data/functions/unified-functions.json", [])
    cases = read_discovery_json(REPO_ROOT / "data/cases/unified-cases.json", [])
    discoveries = read_discovery_json(DISCOVERIES_JSON, [])
    func_map, case_map, disc_map = build_maps(functions, cases, discoveries)
    enriched = [
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
    category_map = build_category_map(enriched, category_defs)

    expected_human = render_prediction_index(enriched, category_map)
    current_human = PREDICTIONS_HUMAN_MD.read_text(encoding="utf-8")
    if expected_human != current_human:
        errors.append("PREDICTIONS.md does not match generated prediction index")

    machine_index = render_machine_index(enriched)
    current_machine = (REPO_ROOT / "data/predictions/unified-predictions-index.md").read_text(encoding="utf-8")
    if machine_index != current_machine:
        errors.append("data/predictions/unified-predictions-index.md is out of date")

    return {
        "curated": len(predictions),
        "passed_novelty": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "passed"),
        "pending_novelty": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "pending"),
        "failed_novelty": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "failed"),
        "novelty_passed": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "passed"),
        "novelty_pending": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "pending"),
        "novelty_failed": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "failed"),
    }


def check_predictions_quick(errors: list[str]) -> dict[str, int]:
    predictions = read_discovery_json(PREDICTIONS_JSON, [])
    for item in predictions:
        if not re.match(r"^PRED-\d{4}$", item.get("id", "")):
            errors.append(f"bad prediction id: {item.get('id')}")
        if "academic_novelty" not in item:
            errors.append(f"prediction missing academic_novelty: {item.get('id')}")
        novelty = item.get("academic_novelty", {})
        if novelty.get("status") not in {"pending", "passed", "failed", "inconclusive"}:
            errors.append(f"bad prediction novelty status: {item.get('id')}")
    return {
        "curated": len(predictions),
        "passed_novelty": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "passed"),
        "pending_novelty": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "pending"),
        "failed_novelty": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "failed"),
        "novelty_passed": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "passed"),
        "novelty_pending": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "pending"),
        "novelty_failed": sum(1 for pred in predictions if pred.get("academic_novelty", {}).get("status") == "failed"),
    }


def check_answers(errors: list[str]) -> dict[str, int]:
    answers = read_answer_json(ANSWERS_JSON_PATH, [])
    category_map = read_answer_json(REPO_ROOT / "data/answers/category-map.json", [])
    build_script = (REPO_ROOT / "scripts/build_answers_from_bootstrap.py").read_text(encoding="utf-8")
    expected_human = render_answer_index(answers, category_map)
    current_human = ANSWERS_LIST_MD.read_text(encoding="utf-8") if ANSWERS_LIST_MD.exists() else ""
    if expected_human != current_human:
        errors.append("ANSWERS.md does not match generated answer index")
    expected_machine = render_answer_index_md(answers)
    current_machine = ANSWERS_INDEX_MD.read_text(encoding="utf-8") if ANSWERS_INDEX_MD.exists() else ""
    if expected_machine != current_machine:
        errors.append("data/answers/unified-answers-index.md is out of date")
    template_ok = ANSWER_TEMPLATE_MD.exists()
    if not template_ok:
        errors.append("docs/zh/answers/ANSWER_TEMPLATE.md is missing")
    required_keywords = [
        "物理学七团乌云",
        "七团乌云",
        "七朵乌云",
        "ANSWER_RECOVERY_KEYWORDS",
        "LOW_PRIORITY_MISREAD_KEYWORDS",
        "PhysicsSevenCloudsRecovery",
    ]
    for keyword in required_keywords:
        if keyword not in build_script:
            errors.append(f"build_answers_from_bootstrap.py missing recovery keyword or marker: {keyword}")
    for item in answers:
        if not re.match(r"^ANS-\d{4}$", item.get("id", "")):
            errors.append(f"bad answer id: {item.get('id')}")
        if "academic_novelty" not in item:
            errors.append(f"answer missing academic_novelty: {item.get('id')}")
        if item.get("status") == "active" and item.get("academic_novelty", {}).get("status") != "passed":
            errors.append(f"active answer without passed novelty: {item.get('id')}")
    for category in category_map:
        if "Entry" in json.dumps(category, ensure_ascii=False):
            errors.append(f"answer category contains Entry column data: {category.get('id')}")
    return {
        "curated": sum(1 for item in answers if item.get("status") == "active" and item.get("academic_novelty", {}).get("status") == "passed"),
        "leads": sum(1 for item in answers if not (item.get("status") == "active" and item.get("academic_novelty", {}).get("status") == "passed")),
        "passed_novelty": sum(1 for item in answers if item.get("academic_novelty", {}).get("status") == "passed"),
        "pending_novelty": sum(1 for item in answers if item.get("academic_novelty", {}).get("status") == "pending"),
        "inconclusive_novelty": sum(1 for item in answers if item.get("academic_novelty", {}).get("status") == "inconclusive"),
        "failed_novelty": sum(1 for item in answers if item.get("academic_novelty", {}).get("status") == "failed"),
    }


def check_functions_cases(errors: list[str]) -> dict[str, int]:
    functions = parse_function_table(FUNC_SOURCE)
    cases = parse_case_table(CASE_SOURCE)
    rel = build_relationships(functions, cases)
    dangling = rel["dangling"]

    function_render = render_functions_collection(functions, ROOT_FUNCTIONS)
    if function_render != ROOT_FUNCTIONS.read_text(encoding="utf-8"):
        errors.append("FUNCTIONS.md does not match generated function collection")

    case_render = render_cases_collection(cases, ROOT_CASES)
    if case_render != ROOT_CASES.read_text(encoding="utf-8"):
        errors.append("CASES.md does not match generated case collection")

    return {
        "functions": len(functions),
        "cases": len(cases),
        "dangling_references": len(dangling),
    }


def check_presence(errors: list[str]) -> None:
    expected = [
        DOC_FUNC_INDEX,
        META_FUNCTIONS_JSON,
        META_FUNCTIONS_JSONL,
        META_FUNCTIONS_INDEX_MD,
        META_FUNCTION_PAGE,
        DOC_CASE_INDEX,
        DISCOVERY_INDEX_MD,
        REPO_ROOT / "data/functions/unified-functions-index.md",
        REPO_ROOT / "data/cases/unified-cases-index.md",
        PREDICTIONS_INDEX_JSON,
        REPO_ROOT / "data/predictions/unified-predictions-index.md",
        REPO_ROOT / "data/discoveries/unified-discoveries-index.md",
        REPO_ROOT / "data/discoveries/bootstrap-category-report.md",
        ANSWERS_LIST_MD,
        ANSWERS_INDEX_MD,
        ANSWER_TEMPLATE_MD,
        REPO_ROOT / "scripts/display_utils.py",
        REPO_ROOT / "scripts/build_answers_from_function_projection.py",
        REPO_ROOT / "scripts/normalize_bilingual_labels.py",
        REPO_ROOT / "scripts/detect_repetitive_text.py",
        REPO_ROOT / "data/answers/unified-answers.json",
        REPO_ROOT / "data/answers/unified-answers.jsonl",
        REPO_ROOT / "data/answers/unified-answers-index.md",
        REPO_ROOT / "data/answers/categories.json",
        REPO_ROOT / "data/answers/category-map.json",
        REPO_ROOT / "docs/zh/answers/items",
        REPO_ROOT / "docs/zh/answers/categories",
        REPO_ROOT / "data/rebuild/section-zero-bootstrap-metafunction-report.md",
        REPO_ROOT / "data/rebuild/section-zero-bootstrap-metafunction-report.json",
        BOOTSTRAP_REPORT_MD,
        REPO_ROOT / "data/rebuild/answer-leads-quality-report.md",
        REPO_ROOT / "data/rebuild/answer-leads-quality-report.json",
        REPO_ROOT / "data/rebuild/function-projection-answer-report.md",
        REPO_ROOT / "data/rebuild/function-projection-answer-report.json",
        REPO_ROOT / "data/rebuild/bilingual-label-cleanup-report.md",
        REPO_ROOT / "data/rebuild/bilingual-label-cleanup-report.json",
        REPO_ROOT / "data/rebuild/repetitive-text-report.md",
        REPO_ROOT / "data/rebuild/repetitive-text-report.json",
    ]
    for path in expected:
        if not path.exists():
            errors.append(f"missing generated file: {path.relative_to(REPO_ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    quick_mode = args.quick or (args.check and not args.full)

    check_readme(errors)
    meta_stats = check_meta_functions(errors)
    if quick_mode:
        discovery_stats = {
            "curated": len(read_discovery_json(DISCOVERIES_JSON, [])),
            "leads": 0,
        }
        prediction_stats = check_predictions_quick(errors)
        answer_stats = check_answers(errors)
        function_stats = {
            "functions": len(read_discovery_json(REPO_ROOT / "data/functions/unified-functions.json", [])),
            "cases": len(read_discovery_json(REPO_ROOT / "data/cases/unified-cases.json", [])),
            "dangling_references": 0,
        }
    else:
        discovery_stats = check_discoveries(errors)
        prediction_stats = check_predictions(errors)
        answer_stats = check_answers(errors)
        function_stats = check_functions_cases(errors)
    check_presence(errors)

    counts = count_repository_objects()
    report = {
        "readme_ok": readme_overview_matches(README),
        "mode": "quick" if quick_mode else "full",
        "counts": counts,
        "meta_functions": meta_stats,
        "discoveries": discovery_stats,
        "predictions": prediction_stats,
        "answers": answer_stats,
        "functions": function_stats,
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return fail(errors) if args.check or errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
