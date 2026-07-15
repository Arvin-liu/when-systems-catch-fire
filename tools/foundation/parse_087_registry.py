#!/usr/bin/env python3
"""Parse UNESCO 4-digit discipline registry from source file."""
import json, hashlib, re, sys

SOURCE_FILE = "/Users/zhiyuan/我的笔记/全量学科理论报告/01_UNESCO_4位学科理论问题总表.md"

with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Parse table rows: | 大类 | 学科代码 | 学科名称 | 主要理论 | 经典问题 | 尚未解答的问题 |
disciplines = []
major_categories = {}
current_major = None

for i, line in enumerate(lines):
    line = line.strip()
    # Skip header and separator
    if line.startswith("#") or line.startswith("|---") or line.startswith("| 大类") or not line.startswith("|"):
        continue
    
    parts = [p.strip() for p in line.split("|")]
    # parts[0] is empty (before first |), parts[-1] is empty (after last |)
    if len(parts) < 7:
        continue
    
    major_cat = parts[1]
    code = parts[2]
    name = parts[3]
    theories = parts[4]
    classic_problems = parts[5]
    unresolved = parts[6]
    
    # Parse major category
    if major_cat:
        m = re.match(r"(\d{2})\s+(.+)", major_cat)
        if m:
            current_major = m.group(1)
            if current_major not in major_categories:
                major_categories[current_major] = {
                    "major_category_code": current_major,
                    "major_category_name": m.group(2),
                    "discipline_count": 0
                }
    
    # Parse discipline code
    if not code.isdigit():
        continue
    
    disc = {
        "discipline_code": code,
        "discipline_name_zh": name,
        "major_category_code": current_major or "",
        "major_category_name": major_categories.get(current_major, {}).get("major_category_name", ""),
        "source_file": SOURCE_FILE,
        "source_line_start": i + 1,
        "source_line_end": i + 1,
        "source_excerpt_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
        "source_entry_status": "PARSED",
        "theories_from_source": theories,
        "classic_problems_from_source": classic_problems,
        "unresolved_from_source": unresolved
    }
    disciplines.append(disc)
    if current_major in major_categories:
        major_categories[current_major]["discipline_count"] += 1

# Write registry
with open("data/discipline-projection/087-discipline-registry.jsonl", "w", encoding="utf-8") as f:
    for d in disciplines:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")

with open("data/discipline-projection/087-major-category-registry.jsonl", "w", encoding="utf-8") as f:
    for mc in sorted(major_categories.keys()):
        f.write(json.dumps(major_categories[mc], ensure_ascii=False) + "\n")

# Summary
print(f"Total disciplines: {len(disciplines)}")
print(f"Major categories: {len(major_categories)}")
for mc in sorted(major_categories.keys()):
    print(f"  {mc} {major_categories[mc]['major_category_name']}: {major_categories[mc]['discipline_count']}")
# Check uniqueness
codes = [d["discipline_code"] for d in disciplines]
dupes = [c for c in codes if codes.count(c) > 1]
if dupes:
    print(f"DUPLICATE CODES: {set(dupes)}")
else:
    print("All discipline codes unique: YES")
