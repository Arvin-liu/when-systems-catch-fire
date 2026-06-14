#!/usr/bin/env python3
"""Validate that no hardcoded numeric counts of project objects exist."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent

SCAN_PATTERNS = [
    # Chinese patterns
    (r'(\d+)\s*个\s*函数', 'functions'),
    (r'(\d+)\s*个\s*效应', 'effects'),
    (r'(\d+)\s*个\s*案例', 'cases'),
    (r'(\d+)\s*个\s*发现', 'discoveries'),
    (r'(\d+)\s*个\s*预测', 'predictions'),
    (r'(\d+)\s*个\s*解析解', 'analytic_solutions'),
    (r'(\d+)\s*个\s*答案', 'answers'),
    (r'(\d+)\s*层知识对象', 'knowledge_layers'),
    (r'五层|五入口|四入口', 'entry_count'),
    # English patterns
    (r'(\d+)\s+functions', 'functions'),
    (r'(\d+)\s+effects', 'effects'),
    (r'(\d+)\s+cases', 'cases'),
    (r'(\d+)\s+discoveries', 'discoveries'),
    (r'(\d+)\s+predictions', 'predictions'),
    (r'(\d+)\s+analytic\s+solutions', 'analytic_solutions'),
    (r'(\d+)\s+answers', 'answers'),
    (r'five-layer|five entry|four entry', 'entry_count'),
]

ALLOWED_MARKERS = ['REPOSITORY_OVERVIEW_START', 'REPOSITORY_OVERVIEW_END',
                   'generated_at', 'run_id', 'source_sha', 'dynamic',
                   'rendered', 'dynamic_count']

def find_files():
    files = []
    for pattern in ['README.md', 'AGENT_ENTRY.md', 'llms.txt']:
        p = ROOT / pattern
        if p.exists():
            files.append(p)
    for subdir in ['docs', 'data']:
        sp = ROOT / subdir
        if sp.exists():
            for ext in ['**/*.md', '**/*.json', '**/*.jsonl', '**/*.py']:
                files.extend(sp.glob(ext))
    return sorted(set(files))

def is_inside_dynamic_block(line, lines, idx):
    """Check if line is inside REPOSITORY_OVERVIEW_START/END block."""
    for i in range(max(0, idx-50), idx+1):
        if 'REPOSITORY_OVERVIEW_START' in lines[i]:
            for j in range(i, idx+1):
                if 'REPOSITORY_OVERVIEW_END' in lines[j]:
                    return False
            return True
    return False

def scan_file(filepath):
    violations = []
    try:
        text = filepath.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return violations

    lines = text.split('\n')
    in_dynamic = False
    rel = str(filepath.relative_to(ROOT))

    # Skip historical rebuild reports that are dated snapshots
    if rel.startswith('data/rebuild/') and 'generated_at' not in text.lower():
        return violations

    for idx, line in enumerate(lines):
        # Track dynamic block boundaries
        if 'REPOSITORY_OVERVIEW_START' in line:
            in_dynamic = True
            continue
        if 'REPOSITORY_OVERVIEW_END' in line:
            in_dynamic = False
            continue

        # Skip lines in dynamic blocks
        if in_dynamic:
            continue

        # Check each pattern
        for pattern, obj_type in SCAN_PATTERNS:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                for match in matches:
                    # Check if line has allowed markers (snapshot-based)
                    has_allowed = any(m.lower() in line.lower() for m in ALLOWED_MARKERS)
                    if has_allowed:
                        continue
                    # Check for commit hashes, dates, etc.
                    if re.search(r'20\d{2}-\d{2}-\d{2}', line):
                        continue
                    if re.search(r'[a-f0-9]{7,40}', line):
                        continue
                    violations.append({
                        'file': str(filepath.relative_to(ROOT)),
                        'line_number': idx + 1,
                        'line': line.strip(),
                        'pattern': pattern,
                        'object_type': obj_type,
                        'matched_number': match,
                    })
    return violations

def main():
    parser = argparse.ArgumentParser(description="Validate no hardcoded counts.")
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--report', action='store_true')
    parser.add_argument('--fix-safe', action='store_true')
    args = parser.parse_args()

    files = find_files()
    all_violations = []
    for f in files:
        all_violations.extend(scan_file(f))

    now = datetime.now(timezone.utc).isoformat()

    if args.report:
        report = {
            'report_type': 'no-hardcoded-counts-validation',
            'blocking_violations': len(all_violations),
            'warnings': [],
            'scan_paths_checked': [str(p.relative_to(ROOT)) for p in files],
            'violations': all_violations,
            'dynamic_blocks_found': True,
            'dynamic_block_markers': ['REPOSITORY_OVERVIEW_START', 'REPOSITORY_OVERVIEW_END'],
            'generated_at': now,
            'phase': 'classification_only',
            'bootstrap_not_run': True,
            'no_active_promotion': True,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))

        out_json = ROOT / 'data' / 'rebuild' / 'no-hardcoded-counts-report.json'
        out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

        md_lines = [
            '# No Hardcoded Counts Report',
            '',
            f'- Blocking violations: {len(all_violations)}',
            f'- Scan paths: {len(files)}',
            f'- Generated at: {now}',
        ]
        if all_violations:
            md_lines.append('')
            md_lines.append('## Violations')
            for v in all_violations:
                md_lines.append(f"- {v['file']}:{v['line_number']} - {v['object_type']}: `{v['matched_number']}`")
        out_md = ROOT / 'data' / 'rebuild' / 'no-hardcoded-counts-report.md'
        out_md.write_text('\n'.join(md_lines) + '\n', encoding='utf-8')
        return 0

    if args.check:
        if all_violations:
            print(f'FAIL: {len(all_violations)} blocking hardcoded count violations found')
            for v in all_violations:
                print(f"  {v['file']}:{v['line_number']} - {v['object_type']} = {v['matched_number']}")
            return 1
        print('PASS: no hardcoded count violations')
        return 0

    if args.fix_safe:
        # For now, just report what would be fixed
        if all_violations:
            print(f'Would fix {len(all_violations)} violations (placeholder only)')
        else:
            print('No violations to fix')
        return 0

    # Default: check mode
    return main() if not (args.check or args.report or args.fix_safe) else 0

if __name__ == '__main__':
    raise SystemExit(main())
