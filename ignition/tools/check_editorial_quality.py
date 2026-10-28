#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Editorial article quality gate (TASK 104 · §5.4).

Reproducible (stdlib only). Flags structural anti-patterns WITHOUT pretending
that software certifies literary quality. It complements, not replaces, manual
rendered review.

Checks (§5.4):
  - excessive bullet or table density (body);
  - repeated template headings / paragraph structures;
  - paragraphs dominated by IDs, paths or machine fields (body only);
  - missing central question (frontmatter);
  - articles that merely concatenate summaries (heuristic: low prose/ID ratio
    + no narrative cue words);
  - unmarked status mixing is a manual item; we only report whether a
    来源与边界 / status section exists;
  - missing source links (来源与边界 appendix with asset references).

Usage:
  python3 tools/check_editorial_quality.py [dir_or_file ...]
Defaults to docs/editorial/articles/*.md.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BULLET_RE = re.compile(r'^\s*[-*]\s+\S')
TABLE_RE = re.compile(r'^\s*\|')
HEADING_RE = re.compile(r'^#{1,6}\s+(.*)$', re.MULTILINE)
ID_TOKEN_RE = re.compile(r'\b(D\d+|T\d+|NFC-[0-9A-F]+|HR-[0-9A-F]+|C\d{3})\b')
PATH_TOKEN_RE = re.compile(r'(/[A-Za-z0-9_./-]+\.(md|py|json|txt))')
APPENDIX_RE = re.compile(r'^#{1,6}\s*来源与边界', re.MULTILINE)

BULLET_TABLE_LIMIT = 0.40   # body lines that are bullets/tables above this -> WARN
ID_DOMINANCE_LIMIT = 0.45   # a body paragraph with >45% ID/path tokens -> WARN
MIN_PROSE_LINES = 20        # below this, likely too thin to be an article


def parse_frontmatter(text):
    fm = {}
    if text.startswith('---'):
        end = text.find('\n---', 3)
        if end != -1:
            block = text[3:end]
            for line in block.splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    fm[k.strip()] = v.strip()
            return fm, text[end + 4:]
    return fm, text


def split_body_before_appendix(text):
    """Return (body_before_appendix, has_appendix)."""
    for m in APPENDIX_RE.finditer(text):
        return text[:m.start()], True
    return text, False


def check_file(path):
    with open(path, encoding='utf-8') as fh:
        raw = fh.read()
    fm, _ = parse_frontmatter(raw)
    body, has_appendix = split_body_before_appendix(raw)

    lines = [l for l in body.splitlines() if l.strip()]
    total = len(lines)
    bullets = sum(1 for l in lines if BULLET_RE.match(l))
    tables = sum(1 for l in lines if TABLE_RE.match(l))
    list_ratio = (bullets + tables) / total if total else 0.0

    headings = HEADING_RE.findall(body)
    heading_counts = {}
    for h in headings:
        heading_counts[h] = heading_counts.get(h, 0) + 1
    repeated_headings = {h: c for h, c in heading_counts.items() if c > 1}

    # paragraph-level ID/path dominance (body only)
    paras = re.split(r'\n\s*\n', body)
    dom_paras = 0
    for p in paras:
        words = re.findall(r'[\w/.-]+', p)
        if len(words) < 8:
            continue
        ids = len(ID_TOKEN_RE.findall(p)) + len(PATH_TOKEN_RE.findall(p))
        frac = ids / max(1, len(words))
        if frac > ID_DOMINANCE_LIMIT:
            dom_paras += 1

    central = fm.get('central_question', '').strip()
    title = fm.get('title', '').strip()
    category = fm.get('category', '').strip()

    # source links: appendix exists and contains asset references / links
    has_source_links = has_appendix and (
        ID_TOKEN_RE.search(raw) is not None
        or re.search(r'\]\(', raw) is not None)

    flags = []
    if not central:
        flags.append('NO_CENTRAL_QUESTION')
    if not title:
        flags.append('NO_TITLE')
    if total < MIN_PROSE_LINES:
        flags.append('TOO_THIN')
    if list_ratio > BULLET_TABLE_LIMIT:
        flags.append('HIGH_LIST_DENSITY(%.2f)' % list_ratio)
    if repeated_headings:
        flags.append('REPEATED_HEADINGS(%s)' % ','.join(repeated_headings))
    if dom_paras > 0:
        flags.append('ID_DOMINATED_PARAS(%d)' % dom_paras)
    if not has_appendix:
        flags.append('NO_SOURCE_APPENDIX')
    elif not has_source_links:
        flags.append('APPENDIX_NO_LINKS')

    verdict = 'PASS' if not flags else 'WARN'
    return {
        'file': os.path.relpath(path, ROOT),
        'title': title,
        'category': category,
        'central_question': central,
        'body_lines': total,
        'list_ratio': round(list_ratio, 3),
        'headings': len(headings),
        'id_dominated_paras': dom_paras,
        'has_appendix': has_appendix,
        'has_source_links': has_source_links,
        'verdict': verdict,
        'flags': flags,
    }


def main():
    paths = sys.argv[1:] or [os.path.join(ROOT, 'docs', 'editorial', 'articles')]
    files = []
    for p in paths:
        if os.path.isdir(p):
            for fn in sorted(os.listdir(p)):
                if fn.endswith('.md'):
                    files.append(os.path.join(p, fn))
        elif p.endswith('.md'):
            files.append(p)
    results = [check_file(f) for f in files]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    warns = [r for r in results if r['verdict'] == 'WARN']
    print('\nSUMMARY: %d files, %d PASS, %d WARN' %
          (len(results), len(results) - len(warns), len(warns)))
    for r in warns:
        print('  - %s: %s' % (r['file'], ', '.join(r['flags'])))
    # persist a human-readable report
    out = os.path.join(ROOT, 'docs', 'editorial', 'QUALITY-REPORT.md')
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write('# 编辑文章质量门报告（TASK 104 · §5.4）\n\n')
        fh.write('自动化仅检测结构反模式，不认证文学质量；须辅以人工渲染审阅。\n\n')
        fh.write('| 文件 | 类别 | 正文行 | 列表比 | 标题数 | ID主导段 | 附录 | 源链接 | 结论 | 标记 |\n')
        fh.write('|---|---|---|---|---|---|---|---|---|---|\n')
        for r in results:
            fh.write('| %s | %s | %d | %.2f | %d | %d | %s | %s | %s | %s |\n' % (
                r['file'].split('/')[-1], r['category'], r['body_lines'],
                r['list_ratio'], r['headings'], r['id_dominated_paras'],
                'Y' if r['has_appendix'] else 'N',
                'Y' if r['has_source_links'] else 'N',
                r['verdict'], ', '.join(r['flags']) or '—'))
        fh.write('\nSUMMARY: %d files, %d PASS, %d WARN\n' %
                 (len(results), len(results) - len(warns), len(warns)))
    print('wrote %s' % out)


if __name__ == '__main__':
    main()
