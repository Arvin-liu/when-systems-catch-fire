#!/usr/bin/env python3
"""render_linked_related_sections.py — Fix all Related Objects sections in markdown pages.

Usage:
  python3 scripts/render_linked_related_sections.py --dry-run
  python3 scripts/render_linked_related_sections.py
  python3 scripts/render_linked_related_sections.py --check
"""

import argparse
import json
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
LINK_DIR = BASE / "data" / "links"
REGISTRY_PATH = LINK_DIR / "object-link-registry.json"


def load_registry():
    if REGISTRY_PATH.exists():
        with REGISTRY_PATH.open() as f:
            return json.load(f)
    return {}


def fix_relative_links_in_text(text, source_file):
    """Fix markdown links that use repo-relative paths to be relative to source_file."""
    fixed_count = 0
    source_file = source_file.resolve()

    def fix_link(match):
        nonlocal fixed_count
        link_text = match.group(1)
        link_path = match.group(2)

        # Skip external URLs and anchor-only links
        if link_path.startswith('http') or link_path.startswith('#'):
            return match.group(0)

        # Check if it's an absolute repo path (like docs/zh/functions/items/D1.md)
        if link_path.startswith('docs/') or link_path.startswith('data/') or link_path.startswith('FUNCTIONS.md'):
            resolved = (BASE / link_path).resolve()
            if resolved.exists():
                # Compute relative path from source file
                try:
                    target_rel = os.path.relpath(str(resolved), str(source_file.parent))
                except Exception:
                    target_rel = link_path  # keep original
                fixed_count += 1
                return f'[{link_text}]({target_rel})'
        return match.group(0)

    new_text = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', fix_link, text)
    return new_text, fixed_count


def fix_bare_bullets(text, registry):
    """Replace bare object IDs in bullets with links."""
    fixed_count = 0
    BARE_BULLET_RE = re.compile(r"^(\s*[-*•]\s+)([A-Z]{1,4}[\d-]+)(\s*)$", re.MULTILINE)

    def replace_bare(match):
        nonlocal fixed_count
        prefix = match.group(1)
        obj_id = match.group(2)
        suffix = match.group(3)
        if obj_id in registry:
            r = registry[obj_id]
            path = r["canonical_path"]
            link_text = r.get("link_text", obj_id)
            fixed_count += 1
            return f"{prefix}[{link_text}]({path}){suffix}"
        return match.group(0)

    new_text = BARE_BULLET_RE.sub(replace_bare, text)
    return new_text, fixed_count


def fix_inline_related(text, registry):
    """Fix 'Related functions: T20' style inline references."""
    fixed_count = 0
    INLINE_RELATED_RE = re.compile(r"(Related\s+\w+\s*:\s*)([A-Z]{1,4}[\d-]+)", re.IGNORECASE)

    def replace_inline(match):
        nonlocal fixed_count
        prefix = match.group(1)
        obj_id = match.group(2)
        if obj_id in registry:
            r = registry[obj_id]
            path = r["canonical_path"]
            link_text = r.get("link_text", obj_id)
            fixed_count += 1
            return f"{prefix}[{link_text}]({path})"
        return match.group(0)

    new_text = INLINE_RELATED_RE.sub(replace_inline, text)
    return new_text, fixed_count


def fix_empty_bullets(text):
    """Replace empty bullets with proper text."""
    fixed_count = 0
    EMPTY_BULLET_RE = re.compile(r"^(\s*[-*•])(\s*)$", re.MULTILINE)

    def replace_empty(match):
        nonlocal fixed_count
        fixed_count += 1
        return f"{match.group(1)} 暂无。 / None."

    new_text = EMPTY_BULLET_RE.sub(replace_empty, text)
    return new_text, fixed_count


def fix_related_section_format(text, registry):
    """Standardize related objects section format into subsections."""
    fixed_count = 0

    # Pattern: ## Related Objects followed by mixed content
    RELATED_BLOCK_RE = re.compile(
        r'(##\s+Related\s+Objects\s*\n)'
        r'((?:(?!##\s)[\s\S]*?))'
        r'(?=##\s|\Z)',
        re.MULTILINE
    )

    def standardize_block(match):
        nonlocal fixed_count
        header = match.group(1)
        content = match.group(2)
        lines = content.strip().split("\n")

        related_funcs = []
        related_cases = []
        related_effects = []
        related_discoveries = []
        related_predictions = []
        related_answers = []
        related_analytics = []
        other_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            lower = stripped.lower()

            # Parse inline format: "- Related functions: [link]" or "- related functions: [link]"
            m_lower = re.match(r'-\s*related\s+functions\s*:\s*(.*)', lower)
            if m_lower:
                # Use original case to slice: find where ":" ends in original line
                colon_idx = stripped.find(":")
                rest = stripped[colon_idx+1:].strip() if colon_idx >= 0 else ""
                if rest and not rest.startswith("None") and not rest.startswith("暂无"):
                    related_funcs.append(rest)
                else:
                    related_funcs.append(None)
                continue

            m_lower = re.match(r'-\s*related\s+cases\s*:\s*(.*)', lower)
            if m_lower:
                colon_idx = stripped.find(":")
                rest = stripped[colon_idx+1:].strip() if colon_idx >= 0 else ""
                if rest and not rest.startswith("None") and not rest.startswith("暂无"):
                    related_cases.append(rest)
                else:
                    related_cases.append(None)
                continue

            m_lower = re.match(r'-\s*related\s+effects\s*:\s*(.*)', lower)
            if m_lower:
                colon_idx = stripped.find(":")
                rest = stripped[colon_idx+1:].strip() if colon_idx >= 0 else ""
                if rest and not rest.startswith("None") and not rest.startswith("暂无"):
                    related_effects.append(rest)
                else:
                    related_effects.append(None)
                continue

            m_lower = re.match(r'-\s*related\s+discoveries\s*:\s*(.*)', lower)
            if m_lower:
                colon_idx = stripped.find(":")
                rest = stripped[colon_idx+1:].strip() if colon_idx >= 0 else ""
                if rest and not rest.startswith("None") and not rest.startswith("暂无"):
                    related_discoveries.append(rest)
                else:
                    related_discoveries.append(None)
                continue

            m_lower = re.match(r'-\s*related\s+predictions\s*:\s*(.*)', lower)
            if m_lower:
                colon_idx = stripped.find(":")
                rest = stripped[colon_idx+1:].strip() if colon_idx >= 0 else ""
                if rest and not rest.startswith("None") and not rest.startswith("暂无"):
                    related_predictions.append(rest)
                else:
                    related_predictions.append(None)
                continue

            m_lower = re.match(r'-\s*related\s+answers\s*:\s*(.*)', lower)
            if m_lower:
                colon_idx = stripped.find(":")
                rest = stripped[colon_idx+1:].strip() if colon_idx >= 0 else ""
                if rest and not rest.startswith("None") and not rest.startswith("暂无"):
                    related_answers.append(rest)
                else:
                    related_answers.append(None)
                continue

            m_lower = re.match(r'-\s*related\s+analytic\s+solutions?\s*:\s*(.*)', lower)
            if m_lower:
                colon_idx = stripped.find(":")
                rest = stripped[colon_idx+1:].strip() if colon_idx >= 0 else ""
                if rest and not rest.startswith("None") and not rest.startswith("暂无"):
                    related_analytics.append(rest)
                else:
                    related_analytics.append(None)
                continue

            # Bullet format: "- [link]"
            m = re.match(r'^[-*•]\s+\[', stripped)
            if m:
                other_lines.append(stripped)
                continue

            # Plain text
            other_lines.append(stripped)

        # Build standardized output
        parts = [header]

        if related_funcs or other_lines:
            parts.append("")
            parts.append("### 相关函数 / Related Functions")
            parts.append("")
            if related_funcs and related_funcs[0]:
                for item in related_funcs:
                    if item:
                        parts.append(f"- {item}")
            elif not related_funcs or not related_funcs[0]:
                parts.append("暂无。")
                parts.append("None.")
            else:
                for item in other_lines:
                    parts.append(item)

        if related_cases is not None or related_cases == []:
            parts.append("")
            parts.append("### 相关案例 / Related Cases")
            parts.append("")
            if related_cases and related_cases[0]:
                for item in related_cases:
                    if item:
                        parts.append(f"- {item}")
            else:
                parts.append("暂无。")
                parts.append("None.")

        if related_discoveries is not None or related_discoveries == []:
            parts.append("")
            parts.append("### 相关发现 / Related Discoveries")
            parts.append("")
            if related_discoveries and related_discoveries[0]:
                for item in related_discoveries:
                    if item:
                        parts.append(f"- {item}")
            else:
                parts.append("暂无。")
                parts.append("None.")

        if related_predictions is not None or related_predictions == []:
            parts.append("")
            parts.append("### 相关预测 / Related Predictions")
            parts.append("")
            if related_predictions and related_predictions[0]:
                for item in related_predictions:
                    if item:
                        parts.append(f"- {item}")
            else:
                parts.append("暂无。")
                parts.append("None.")

        if related_answers is not None or related_answers == []:
            parts.append("")
            parts.append("### 相关答案 / Related Answers")
            parts.append("")
            if related_answers and related_answers[0]:
                for item in related_answers:
                    if item:
                        parts.append(f"- {item}")
            else:
                parts.append("暂无。")
                parts.append("None.")

        if related_analytics is not None or related_analytics == []:
            parts.append("")
            parts.append("### 相关解析解 / Related Analytic Solutions")
            parts.append("")
            if related_analytics and related_analytics[0]:
                for item in related_analytics:
                    if item:
                        parts.append(f"- {item}")
            else:
                parts.append("暂无。")
                parts.append("None.")

        fixed_count += 1
        return "\n".join(parts)

    new_text = RELATED_BLOCK_RE.sub(standardize_block, text)
    return new_text, fixed_count


def process_file(filepath, registry):
    """Process a single file. Returns (modified, fixes_count)."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False, 0

    original = text
    total_fixes = 0

    text, n = fix_bare_bullets(text, registry)
    total_fixes += n

    text, n = fix_inline_related(text, registry)
    total_fixes += n

    # Fix relative paths in markdown links
    text, n = fix_relative_links_in_text(text, filepath)
    total_fixes += n

    text, n = fix_empty_bullets(text)
    total_fixes += n

    text, n = fix_related_section_format(text, registry)
    total_fixes += n

    modified = text != original
    if modified:
        filepath.write_text(text, encoding="utf-8")
        return True, total_fixes
    return False, 0


def main():
    parser = argparse.ArgumentParser(description="Fix related objects sections")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    registry = load_registry()
    if not registry:
        print("ERROR: No registry found. Run build_object_link_registry.py first.")
        return 1

    pages_to_process = []
    for base_dir in ["docs/zh/functions/items", "docs/zh/cases/items",
                      "docs/zh/analytic-solutions/items", "docs/zh/discoveries/items",
                      "docs/zh/predictions/items", "docs/zh/answers/items",
                      "data/rebuild", "data/relations", "data/object-classification",
                      "data/project-identity"]:
        base = BASE / base_dir
        if base.exists():
            pages_to_process.extend(base.rglob("*.md"))

    for f in BASE.glob("*.md"):
        pages_to_process.append(f)

    total_scanned = 0
    total_modified = 0
    total_fixes = 0

    for page in sorted(set(pages_to_process)):
        total_scanned += 1
        modified, fixes = process_file(page, registry)
        if modified:
            total_modified += 1
            total_fixes += fixes
            if args.dry_run:
                print(f"[DRY-RUN] Would fix {fixes} issues in {page.relative_to(BASE)}")
            else:
                print(f"Fixed {fixes} issues in {page.relative_to(BASE)}")

    print(f"\nSummary: scanned={total_scanned}, modified={total_modified}, total_fixes={total_fixes}")

    if args.check:
        bare_hits = 0
        empty_hits = 0
        for page in pages_to_process:
            try:
                text = page.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r"^(\s*[-*•]\s+)([A-Z]{1,4}[\d-]+)(\s*)$", text, re.MULTILINE):
                    obj_id = m.group(2)
                    if obj_id not in registry:
                        bare_hits += 1
                for line in text.split("\n"):
                    if re.match(r"^\s*[-*•]\s*$", line):
                        empty_hits += 1
            except Exception:
                pass

        if bare_hits == 0 and empty_hits == 0:
            print("CHECK PASS: No remaining bare IDs or empty bullets")
            return 0
        else:
            print(f"CHECK FAIL: {bare_hits} bare IDs, {empty_hits} empty bullets remain")
            return 1
    return 0


if __name__ == "__main__":
    exit(main())
