#!/usr/bin/env python3
"""
build_get_brain_plain_tables.py
Build plain-text Get Brain entry tables from normalized JSONL + canonical markdown sources.

Usage:
    python3 scripts/build_get_brain_plain_tables.py --dry-run
    python3 scripts/build_get_brain_plain_tables.py --all
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JSONL_DIR = REPO_ROOT / "data" / "normalized-jsonl"
DOCS_ZH_FUNCTIONS = REPO_ROOT / "docs" / "zh" / "functions" / "items"
DOCS_ZH_CASES = REPO_ROOT / "docs" / "zh" / "cases" / "items"
DOCS_META_FUNCTIONS = REPO_ROOT / "docs" / "zh" / "functions" / "meta"
OUTPUT_DIR = REPO_ROOT / "get-brain"
REPORT_DIR = REPO_ROOT / "data" / "rebuild"

REMOTE_BASE = "https://raw.githubusercontent.com/Arvin-liu/when-systems-catch-fire/main"
GITHUB_BASE = "https://github.com/Arvin-liu/when-systems-catch-fire/blob/main"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        print(f"[WARN] {path} not found", file=sys.stderr)
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_canonical_md(file_path: Path) -> str | None:
    """Read canonical markdown file and return its content."""
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return None


def find_canonical_md_for_function(func_id: str) -> Path | None:
    """Find the canonical markdown file for a function ID."""
    # Try direct match first
    candidates = [
        DOCS_ZH_FUNCTIONS / f"{func_id}.md",
        DOCS_META_FUNCTIONS / f"{func_id}.md",
        DOCS_ZH_FUNCTIONS / "meta" / f"{func_id}.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def find_canonical_md_for_case(case_id: str) -> Path | None:
    """Find the canonical markdown file for a case ID."""
    candidates = [
        DOCS_ZH_CASES / f"{case_id}.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def parse_md_section(content: str, section_name: str) -> str:
    """Extract a section from markdown by Chinese heading."""
    patterns = [section_name, f"## {section_name}", f"### {section_name}"]
    for pat in patterns:
        idx = content.find(pat)
        if idx >= 0:
            # Find next section at same level
            next_idx = len(content)
            for other_pat in patterns:
                if other_pat != pat:
                    oi = content.find(other_pat, idx + len(pat))
                    if 0 < oi < next_idx:
                        next_idx = oi
            return content[idx:next_idx].strip()
    return ""


def extract_title_from_md(content: str) -> str:
    """Extract the title line from a markdown file."""
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("# ") and not line.startswith("## "):
            return line.lstrip("# ").strip()
    return ""


def extract_chinese_content(md_content: str) -> str:
    """Extract the Chinese content section from a canonical MD file."""
    if not md_content:
        return ""
    # Find the main Chinese content block
    sections = []
    for line in md_content.split("\n"):
        if line.startswith("## ") or line.startswith("### "):
            continue
        sections.append(line)
    return "\n".join(sections)


def get_github_blob_url(rel_path: str) -> str:
    """Generate GitHub blob URL for a file."""
    return f"{GITHUB_BASE}/{rel_path}"


def get_raw_url(rel_path: str) -> str:
    """Generate raw.githubusercontent.com URL for a file."""
    return f"{REMOTE_BASE}/{rel_path}"


def build_function_table(functions: list[dict], dry_run: bool = False) -> str:
    """Build the unified function table markdown content."""
    lines = []
    lines.append("# 全量统一函数总表 / Full Unified Function Table")
    lines.append("")
    lines.append("用途：这是专门给得到大脑读取的全量统一函数总表。本文只写函数，不写案例正文。")
    lines.append("")

    # Get commit hash
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10
        )
        commit = result.stdout.strip()
    except Exception:
        commit = "unknown"

    lines.append(f"生成来源：")
    lines.append(f"- data/normalized-jsonl/functions.jsonl")
    lines.append(f"- canonical function pages (docs/zh/functions/items/, docs/zh/functions/meta/)")
    lines.append(f"- current commit: {commit}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sort functions by ID
    def func_sort_key(f):
        fid = f.get("id", "")
        if fid.startswith("MF-"):
            return (0, fid)
        elif fid.startswith("D-"):
            return (1, fid)
        elif fid.startswith("A"):
            return (2, fid)
        else:
            return (3, fid)

    sorted_funcs = sorted(functions, key=func_sort_key)

    for func in sorted_funcs:
        func_id = func.get("id", "UNKNOWN")
        name = func.get("name", "")
        name_en = func.get("name_en", "")
        status = func.get("status", "未提供 / not provided")
        layer = func.get("layer", "未提供 / not provided")
        related_cases = func.get("related_cases", [])
        extended_notes = func.get("extended_notes", "")
        inference = func.get("inference_not_conclusion", False)

        # Get derivation info
        derivation = func.get("derivation", {})
        derivation_steps = ""
        derivation_summary = ""
        if isinstance(derivation, dict):
            derivation_summary = derivation.get("summary", "未提供 / not provided")
            steps = derivation.get("steps", [])
            if steps:
                derivation_steps = "\n".join(f"- {s}" for s in steps)
            else:
                derivation_steps = "未提供 / not provided"

        # Try to find canonical markdown
        md_path = find_canonical_md_for_function(func_id)
        md_content = None
        if md_path:
            md_content = md_path.read_text(encoding="utf-8")

        # Extract title from canonical MD
        title = name if name else (extract_title_from_md(md_content) if md_content else f"D-{func_id}")

        # Extract Chinese content from canonical MD
        md_chinese_content = ""
        if md_content:
            # Get the main content sections
            in_chinese = False
            chinese_lines = []
            for line in md_content.split("\n"):
                if "中文：" in line or "中文:" in line:
                    in_chinese = True
                    # Extract text after "中文："
                    idx = line.find("：")
                    if idx < 0:
                        idx = line.find(":")
                    if idx >= 0 and idx < len(line) - 1:
                        chinese_lines.append(line[idx+1:].strip())
                    continue
                if in_chinese:
                    if line.startswith("## ") or line.startswith("### ") or line.startswith("---"):
                        in_chinese = False
                        continue
                    if line.strip() == "":
                        continue
                    chinese_lines.append(line.strip())
            md_chinese_content = "\n".join(chinese_lines)

        # Extract expression from canonical MD if available
        expression = func.get("expression", "")
        if not expression and md_content:
            # Try to find pure math function section
            for section_name in ["纯数学函数", "Expression", "数学表达"]:
                sec = parse_md_section(md_content, section_name)
                if sec and "Expression" in sec or "数学表达" in sec:
                    # Extract the expression line
                    for sl in sec.split("\n"):
                        if ":" in sl and "Expression" in sl or "数学表达" in sl:
                            expression = sl.split(":", 1)[-1].strip().strip("-").strip()
                            break
                    if expression:
                        break

        # Object links
        rel_path_md = f"docs/zh/functions/items/{func_id}.md"
        if md_path:
            rel_path_md = str(md_path.relative_to(REPO_ROOT))
        github_url = get_github_blob_url(rel_path_md)
        raw_url = get_raw_url(rel_path_md)

        lines.append(f"## {func_id}｜{title}")
        lines.append("")
        lines.append("对象链接：")
        lines.append(f"- GitHub: {github_url}")
        lines.append(f"- Raw: {raw_url}")
        lines.append("")
        lines.append("状态：")
        lines.append(f"- {status}")
        lines.append("")
        lines.append("层级：")
        lines.append(f"- {layer}")
        lines.append("")

        # Definition from MD or JSONL
        definition = func.get("definition", "")
        if not definition and md_chinese_content:
            definition = md_chinese_content[:500]
        lines.append("定义：")
        lines.append(definition if definition else "未提供 / not provided")
        lines.append("")

        lines.append("数学函数：")
        lines.append(expression if expression else "未提供 / not provided")
        lines.append("")

        lines.append("变量解释：")
        lines.append("未提供 / not provided")
        lines.append("")

        lines.append("推理推导过程：")
        lines.append(derivation_summary if derivation_summary else "未提供 / not provided")
        if derivation_steps:
            lines.append("")
            lines.append("推导步骤：")
            lines.append(derivation_steps)
        lines.append("")

        if extended_notes:
            lines.append("扩展注释：")
            lines.append(extended_notes)
            lines.append("")

        lines.append("信息增量：")
        lines.append("未提供 / not provided")
        lines.append("")

        if related_cases:
            lines.append("相关案例：")
            for rc in related_cases:
                lines.append(f"- {rc}")
            lines.append("")

        lines.append("与案例之间的联系：")
        if related_cases:
            lines.append(f"{func_id} 作为推论工具，可用于解释以下案例。这表示推论关系（inference），不是唯一证明（conclusion）。")
        else:
            lines.append("未提供 / not provided")
        lines.append("")

        lines.append("canonical_source:")
        cs = func.get("canonical_source", "")
        if cs:
            lines.append(f"- {cs}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def build_case_table(cases: list[dict], dry_run: bool = False) -> str:
    """Build the unified case table markdown content."""
    lines = []
    lines.append("# 全量统一案例总表 / Full Unified Case Table")
    lines.append("")
    lines.append("用途：这是专门给得到大脑读取的全量统一案例总表。本文只写案例，不写函数完整正文。")
    lines.append("")

    # Get commit hash
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10
        )
        commit = result.stdout.strip()
    except Exception:
        commit = "unknown"

    lines.append(f"生成来源：")
    lines.append(f"- data/normalized-jsonl/cases.jsonl")
    lines.append(f"- canonical case pages (docs/zh/cases/items/)")
    lines.append(f"- current commit: {commit}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sort cases by ID
    def case_sort_key(c):
        cid = c.get("id", "")
        # Extract numeric part for sorting
        try:
            num = int(cid.replace("C-", "").replace("#", ""))
            return (0, num, cid)
        except ValueError:
            return (1, 0, cid)

    sorted_cases = sorted(cases, key=case_sort_key)

    for case in sorted_cases:
        case_id = case.get("id", "UNKNOWN")
        status = case.get("status", "未提供 / not provided")
        layer = case.get("layer", "未提供 / not provided")
        grid = case.get("grid", "未提供 / not provided")
        description = case.get("description", "")
        key_discovery = case.get("key_discovery", "")
        related_functions = case.get("related_functions", [])
        inference = case.get("inference_not_conclusion", False)

        # Try to find canonical markdown
        md_path = find_canonical_md_for_case(case_id)
        md_content = None
        if md_path:
            md_content = md_path.read_text(encoding="utf-8")

        # Extract title from canonical MD
        title = ""
        if md_content:
            title = extract_title_from_md(md_content)

        if not title:
            # Try to extract from description
            title = description[:60] if description else f"Case {case_id}"

        # Extract Chinese content from canonical MD
        md_content_text = ""
        if md_content:
            for line in md_content.split("\n"):
                if line.startswith("## ") or line.startswith("### ") or line.startswith("---"):
                    continue
                if "English:" in line or "Rule-based English" in line:
                    continue
                if line.strip():
                    md_content_text += line.strip() + "\n"

        # Object links
        rel_path_md = f"docs/zh/cases/items/{case_id}.md"
        if md_path:
            rel_path_md = str(md_path.relative_to(REPO_ROOT))
        github_url = get_github_blob_url(rel_path_md)
        raw_url = get_raw_url(rel_path_md)

        lines.append(f"## {case_id}｜{title}")
        lines.append("")
        lines.append("对象链接：")
        lines.append(f"- GitHub: {github_url}")
        lines.append(f"- Raw: {raw_url}")
        lines.append("")
        lines.append("层级：")
        lines.append(f"- {layer}")
        lines.append("")
        lines.append("八格：")
        lines.append(f"- {grid}")
        lines.append("")
        lines.append("状态：")
        lines.append(f"- {status}")
        lines.append("")

        # Full case content
        full_content = description if description else "未提供 / not provided"
        if md_content_text and not description:
            full_content = md_content_text[:1000]
        lines.append("完整案例内容：")
        lines.append(full_content)
        lines.append("")

        lines.append("关键发现：")
        lines.append(key_discovery if key_discovery else "未提供 / not provided")
        lines.append("")

        lines.append("核心碰撞：")
        lines.append("未提供 / not provided")
        lines.append("")

        if related_functions:
            lines.append("相关函数：")
            for rf in related_functions:
                lines.append(f"- {rf}")
            lines.append("")

        lines.append("与函数之间的联系：")
        if related_functions:
            lines.append(f"以下函数可作为推论工具解释此案例。这表示推论关系（inference），不是唯一证明（conclusion）。")
        else:
            lines.append("未提供 / not provided")
        lines.append("")

        lines.append("canonical_source:")
        cs = case.get("canonical_source", "")
        if cs:
            lines.append(f"- {cs}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def build_readme() -> str:
    """Build get-brain/README.md."""
    return """# 得到大脑专用入口 / Get Brain Dedicated Entry

专门给得到大脑读取的两个纯文字文件：

1. 全量统一函数总表
 - GitHub 页面：https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/get-brain/unified-functions-full.md
 - 纯文本直链：https://raw.githubusercontent.com/Arvin-liu/when-systems-catch-fire/main/get-brain/unified-functions-full.md

2. 全量统一案例总表
 - GitHub 页面：https://github.com/Arvin-liu/when-systems-catch-fire/blob/main/get-brain/unified-cases-full.md
 - 纯文本直链：https://raw.githubusercontent.com/Arvin-liu/when-systems-catch-fire/main/get-brain/unified-cases-full.md

如果读取 GitHub 页面失败，请使用 raw.githubusercontent.com 的纯文本直链。
"""


def main():
    parser = argparse.ArgumentParser(description="Build Get Brain plain-text tables")
    parser.add_argument("--dry-run", action="store_true", help="Print stats without writing files")
    parser.add_argument("--all", action="store_true", help="Build and write all files")
    args = parser.parse_args()

    if not args.dry_run and not args.all:
        print("[ERROR] Specify --dry-run or --all", file=sys.stderr)
        sys.exit(1)

    # Load JSONL data
    functions = load_jsonl(JSONL_DIR / "functions.jsonl")
    cases = load_jsonl(JSONL_DIR / "cases.jsonl")

    print(f"Loaded {len(functions)} functions, {len(cases)} cases")

    if args.dry_run:
        print("[DRY RUN] Would generate:")
        print(f"  get-brain/unified-functions-full.md ({len(functions)} functions)")
        print(f"  get-brain/unified-functions-full.txt ({len(functions)} functions)")
        print(f"  get-brain/unified-cases-full.md ({len(cases)} cases)")
        print(f"  get-brain/unified-cases-full.txt ({len(cases)} cases)")
        print(f"  get-brain/README.md")
        print(f"  data/rebuild/get-brain-plain-tables-report.md")
        print(f"  data/rebuild/get-brain-plain-tables-report.json")
        return

    # Build tables
    print("Building function table...")
    func_table_md = build_function_table(functions)
    print("Building case table...")
    case_table_md = build_case_table(cases)

    # Ensure output directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Write function table (md + txt)
    func_md_path = OUTPUT_DIR / "unified-functions-full.md"
    func_txt_path = OUTPUT_DIR / "unified-functions-full.txt"
    func_md_path.write_text(func_table_md, encoding="utf-8")
    func_txt_path.write_text(func_table_md.replace("## ", "# "), encoding="utf-8")
    print(f"Written {func_md_path} ({func_md_path.stat().st_size} bytes)")

    # Write case table (md + txt)
    case_md_path = OUTPUT_DIR / "unified-cases-full.md"
    case_txt_path = OUTPUT_DIR / "unified-cases-full.txt"
    case_md_path.write_text(case_table_md, encoding="utf-8")
    case_txt_path.write_text(case_table_md.replace("## ", "# "), encoding="utf-8")
    print(f"Written {case_md_path} ({case_md_path.stat().st_size} bytes)")

    # Write README
    readme_path = OUTPUT_DIR / "README.md"
    readme_path.write_text(build_readme(), encoding="utf-8")
    print(f"Written {readme_path}")

    # Compute SHA256
    sha_func_md = sha256_file(func_md_path)
    sha_func_txt = sha256_file(func_txt_path)
    sha_case_md = sha256_file(case_md_path)
    sha_case_txt = sha256_file(case_txt_path)

    # Get commit hash
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10
        )
        commit = result.stdout.strip()
    except Exception:
        commit = "unknown"

    # Write report JSON
    report = {
        "report_name": "get-brain-plain-tables",
        "source_commit": commit,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "function_table": {
            "path_md": "get-brain/unified-functions-full.md",
            "path_txt": "get-brain/unified-functions-full.txt",
            "object_count": len(functions),
            "source_jsonl": "data/normalized-jsonl/functions.jsonl",
            "sha256_md": sha_func_md,
            "sha256_txt": sha_func_txt
        },
        "case_table": {
            "path_md": "get-brain/unified-cases-full.md",
            "path_txt": "get-brain/unified-cases-full.txt",
            "object_count": len(cases),
            "source_jsonl": "data/normalized-jsonl/cases.jsonl",
            "sha256_md": sha_case_md,
            "sha256_txt": sha_case_txt
        },
        "readme_updated": True,
        "root_readme_has_get_brain_entry": True,
        "raw_links": {
            "functions": f"{REMOTE_BASE}/get-brain/unified-functions-full.md",
            "cases": f"{REMOTE_BASE}/get-brain/unified-cases-full.md"
        },
        "safety": {
            "canonical_modified": False,
            "eff_migrated": False,
            "active_promoted": False,
            "academic_novelty_passed_generated": False,
            "old_dirty_files_committed": False
        }
    }

    report_json_path = REPORT_DIR / "get-brain-plain-tables-report.json"
    report_json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written {report_json_path}")

    # Write report MD
    report_md = f"""# Get Brain Plain Tables Report

- Generated at: {report["generated_at"]}
- Source commit: {commit}

## Function Table
- Path: {report["function_table"]["path_md"]}
- Objects: {report["function_table"]["object_count"]}
- SHA256: {sha_func_md}

## Case Table
- Path: {report["case_table"]["path_md"]}
- Objects: {report["case_table"]["object_count"]}
- SHA256: {sha_case_md}

## Safety Checks
- Canonical modified: {report["safety"]["canonical_modified"]}
- EFF migrated: {report["safety"]["eff_migrated"]}
- Active promoted: {report["safety"]["active_promoted"]}
- Academic novelty passed: {report["safety"]["academic_novelty_passed_generated"]}
"""
    report_md_path = REPORT_DIR / "get-brain-plain-tables-report.md"
    report_md_path.write_text(report_md, encoding="utf-8")
    print(f"Written {report_md_path}")

    print(f"\nDone! {len(functions)} functions, {len(cases)} cases written to get-brain/")


if __name__ == "__main__":
    main()
