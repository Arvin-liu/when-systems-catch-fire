#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_corpus_relation_graph.py — Reproducible internal-relation analysis over the
governed knowledge corpus of the "when-systems-catch-fire" formal repository.

This is TASK 104 (IGNITION NARRATIVE SYNTHESIS AND LIVE SYSTEM MAP R1) deliverable
for contract section 4 ("Corpus relation analysis"). It is deterministic, has no
network access, and depends only on the Python standard library.

Design principles (from contract §4):
  * Do NOT group only by directory, filename or broad topic labels.
  * Every ACCEPTED relation declares: type, evidence (source location), confidence.
  * Semantic similarity and citation overlap are CANDIDATE signals only; they are
    recorded separately and never become canonical edges.
  * The algorithm must detect clusters that are too broad, too heterogeneous,
    merely taxonomic, or lack a coherent article question, and must split / reject
    / retain them only as reference collections.

Inputs (governed assets):
  * KNOWLEDGE/cards/part-*.md        — 339 curated asset cards (result/article,
                                        function, non-function claim) with explicit
                                        依赖 / 被引用 / 相关 / 主题 fields.
  * KNOWLEDGE/MAP.md                 — research-question organisation (subject hubs).
  * RESULTS/CORRECTIONS.md           — supersession / correction / withdrawal / alias.
  * KNOWLEDGE/EVOLUTION.md           — alias / rebound lineages.
  * RESULTS/OPEN-QUESTIONS.md        — open obligations / missing evidence.
  * RESULTS/EVIDENCE-LINEAGE.md      — evidence lineage references.

Outputs (under --out, default analysis/corpus-relation/):
  * corpus_relation_graph.json       — nodes + typed accepted edges + candidate signals.
  * article_cluster_candidates.json  — clusters with disposition + proposed central question.
  * RELATION-ANALYSIS.md             — human-readable report.

Usage:
  python3 tools/build_corpus_relation_graph.py --root . --out analysis/corpus-relation
"""

import os
import re
import json
import math
import argparse
from collections import defaultdict, Counter

# ---------------------------------------------------------------------------
# Asset-id extraction
# ---------------------------------------------------------------------------
ID_RE = re.compile(r'(?:[DT]\d+|NFC-[0-9a-f]+|HR-[0-9A-F]+)', re.IGNORECASE)
TYPE_TOKENS = ('FUNCTION_ASSET', 'NONFUNCTION_CLAIM', 'RESULT_OR_ARTICLE')
TYPE_RE = re.compile(r'`(' + '|'.join(TYPE_TOKENS) + r')`')


def extract_ids(text):
    """Return upper-cased, de-duplicated asset ids found in text."""
    out = []
    seen = set()
    for m in ID_RE.finditer(text or ''):
        tok = m.group(0).upper()
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out


def norm_id(tok):
    return tok.lower()


# ---------------------------------------------------------------------------
# Card parsing
# ---------------------------------------------------------------------------
ANCHOR_RE = re.compile(r'<a id="asset-([^"]+)"></a>')
HEADING_RE = re.compile(r'^\s*##\s+(.*)$')
FIELD_RE = re.compile(r'^\s*-\s*\*\*(.+?)[：:]\*\*\s*(.*)$')


def parse_card_block(anchor, body):
    m = ANCHOR_RE.match(anchor)
    anchor_id = m.group(1) if m else ''
    node = {
        'anchor_id': anchor_id,
        'title': None,
        'asset_type': None,
        'asset_id': None,
        'status': None,
        'dependencies': [],
        'reverse_dependencies': [],
        'related': [],
        'topics': [],
        'maturity_m': None,
        'maturity_e': None,
        'evidence_sources': [],
        'primary_source': None,
        'last_adjudicated': None,
        'why': None,
        'current_result': None,
        'ceiling': None,
        'not_established': None,
        'next_step': None,
        'body': '',
        'semantic_text': '',
    }
    lines = body.splitlines()
    cur_field = None
    body_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        hm = HEADING_RE.match(line)
        if hm and node['title'] is None:
            node['title'] = hm.group(1).strip()
            cur_field = None
            i += 1
            continue
        fm = FIELD_RE.match(line)
        if fm:
            key = fm.group(1).strip()
            val = fm.group(2).strip()
            cur_field = key
            _handle_field(node, key, val)
            i += 1
            continue
        # continuation of previous multi-line field (e.g. 来源与证据)
        if (cur_field == '来源与证据' and line.strip()
                and not line.strip().startswith('#')
                and not line.strip().startswith('<a')):
            more = re.findall(r'`([^`]+)`', line)
            if more:
                node['evidence_sources'].extend(more)
            i += 1
            continue
        if (line.strip() and not line.strip().startswith('<a')
                and not line.strip().startswith('##')):
            body_lines.append(line.strip())
        i += 1
    node['body'] = ' '.join(body_lines)
    # rich text for the (candidate-only) semantic signal: structured prose
    # fields carry the actual intellectual content, not the empty free body.
    node['semantic_text'] = ' '.join(filter(None, [
        node['title'] or '',
        node.get('why') or '',
        node.get('current_result') or '',
        node.get('ceiling') or '',
        node.get('not_established') or '',
        node.get('next_step') or '',
        ' '.join(node.get('topics') or []),
    ]))
    return node


def _handle_field(node, key, val):
    if key == '身份/来源':
        tm = TYPE_RE.search(val)
        if tm:
            node['asset_type'] = tm.group(1)
        # id token right after the type token
        im = re.search(r'`(?:' + '|'.join(TYPE_TOKENS) + r')`\s*·\s*`([^`]+)`', val)
        if im:
            node['asset_id'] = im.group(1).strip()
        else:
            for t in re.findall(r'`([^`]+)`', val):
                if ID_RE.fullmatch(t):
                    node['asset_id'] = t.strip()
                    break
        # primary source document from the markdown link
        lm = re.search(r'\[[^\]]*\]\(([^)]+)\)', val)
        if lm:
            node['primary_source'] = lm.group(1).strip()
    elif '当前状态' in key:
        sm = re.search(r'`([^`]+)`', val)
        if sm:
            node['status'] = sm.group(1)
    elif '依赖' in key and '反向' not in key and '相关' not in key:
        node['dependencies'] = extract_ids(val)
    elif '反向依赖' in key or '被引用' in key:
        node['reverse_dependencies'] = extract_ids(val)
    elif '相关文章' in key or '相关资产' in key:
        node['related'] = extract_ids(val)
    elif '主题' in key:
        node['topics'] = [t.strip().upper() for t in re.findall(r'`([^`]+)`', val)]
    elif '成熟度' in key:
        mm = re.search(r'数学\s*`?([A-Z]\d+)`?', val)
        em = re.search(r'外部证据\s*`?([A-Z]\d+)`?', val)
        if mm:
            node['maturity_m'] = mm.group(1)
        if em:
            node['maturity_e'] = em.group(1)
    elif '演化历史' in key:
        am = re.search(r'Last adjudicated:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})', val)
        if am:
            node['last_adjudicated'] = am.group(1)
    elif '来源与证据' in key:
        node['evidence_sources'] = re.findall(r'`([^`]+)`', val)
    elif '为什么产生' in key:
        node['why'] = val.strip()
    elif '当前结果' in key:
        node['current_result'] = val.strip()
    elif '假设与表述上限' in key:
        node['ceiling'] = val.strip()
    elif '未建立' in key:
        node['not_established'] = val.strip()
    elif '下一步' in key:
        node['next_step'] = val.strip()


def load_cards(root):
    cards_dir = os.path.join(root, 'KNOWLEDGE', 'cards')
    nodes = []
    by_lower = {}
    if not os.path.isdir(cards_dir):
        return nodes, by_lower
    for fn in sorted(os.listdir(cards_dir)):
        if not fn.startswith('part-') or not fn.endswith('.md'):
            continue
        path = os.path.join(cards_dir, fn)
        with open(path, 'r', encoding='utf-8') as fh:
            text = fh.read()
        blocks = re.split(r'(<a id="asset-[^"]+"></a>)', text)
        for i in range(1, len(blocks), 2):
            anchor = blocks[i]
            body = blocks[i + 1] if i + 1 < len(blocks) else ''
            node = parse_card_block(anchor, body)
            if not node['asset_id']:
                # fall back to anchor-derived id
                node['asset_id'] = node['anchor_id'].upper()
            node['id'] = node['asset_id']
            node['node_kind'] = 'card'
            node['file'] = os.path.join('KNOWLEDGE', 'cards', fn)
            nodes.append(node)
            by_lower[norm_id(node['asset_id'])] = node
    return nodes, by_lower


# ---------------------------------------------------------------------------
# MAP subject hubs
# ---------------------------------------------------------------------------
SUBJECT_RE = re.compile(r'<a id="(subject-[^"]+)"></a>')
SUBJECT_HEAD_RE = re.compile(r'^\s*##\s+(.*)$')
GUIDE_RE = re.compile(r'\*\*引导问题：\*\*\s*(.*)')
MAP_ANCHOR_RE = re.compile(r'ASSET-CARDS\.md#asset-([^)\s]+)')


def load_map_subjects(root, by_lower):
    """Return list of (subject_id, title, guiding_question, [card_ids])."""
    path = os.path.join(root, 'KNOWLEDGE', 'MAP.md')
    if not os.path.isfile(path):
        return []
    with open(path, 'r', encoding='utf-8') as fh:
        text = fh.read()
    subjects = []
    cur = None
    for line in text.splitlines():
        sm = SUBJECT_RE.search(line)
        if sm:
            if cur:
                subjects.append(cur)
            cur = {'id': sm.group(1), 'title': None,
                   'guiding_question': None, 'cards': []}
            continue
        if cur is None:
            continue
        hm = SUBJECT_HEAD_RE.match(line)
        if hm and cur['title'] is None:
            cur['title'] = hm.group(1).strip()
            continue
        gm = GUIDE_RE.search(line)
        if gm and cur['guiding_question'] is None:
            cur['guiding_question'] = gm.group(1).strip()
        for ma in MAP_ANCHOR_RE.finditer(line):
            cid = norm_id(ma.group(1))
            if cid in by_lower and cid not in cur['cards']:
                cur['cards'].append(cid)
    if cur:
        subjects.append(cur)
    return subjects


# ---------------------------------------------------------------------------
# Correction / evolution tables
# ---------------------------------------------------------------------------
TABLE_ROW_RE = re.compile(r'^\s*\|(.*)\|\s*$')


def _split_row(line):
    cells = line.strip().strip('|').split('|')
    return [c.strip() for c in cells]


def load_corrections(root, by_lower):
    """Return (correction_edges, doc_node_id). Each edge: (id_a, id_b, subtype)."""
    path = os.path.join(root, 'RESULTS', 'CORRECTIONS.md')
    edges = []
    if not os.path.isfile(path):
        return edges
    with open(path, 'r', encoding='utf-8') as fh:
        text = fh.read()
    for line in text.splitlines():
        if not TABLE_ROW_RE.match(line):
            continue
        cells = _split_row(line)
        if len(cells) < 2:
            continue
        if set(cells[0]) <= set('-: '):  # separator
            continue
        if cells[0].startswith('旧说法') or '旧说法' in cells[0]:
            continue
        joined = ' | '.join(cells)
        ids = extract_ids(joined)
        # subtype from disposition cell (second column)
        disp = cells[1] if len(cells) > 1 else ''
        subtype = 'correction'
        if '撤回' in disp:
            subtype = 'withdrawal'
        elif '阻断' in disp:
            subtype = 'blocked_alias'
        elif '身份纠正' in disp:
            subtype = 'identity_correction'
        elif '限定' in disp:
            subtype = 'scope_limitation'
        elif '重写' in disp:
            subtype = 'rewrite'
        elif '撤销' in disp:
            subtype = 'withdrawal_of_surface'
        resolved = [i for i in ids if norm_id(i) in by_lower]
        for a in range(len(resolved)):
            for b in range(a + 1, len(resolved)):
                edges.append((norm_id(resolved[a]), norm_id(resolved[b]), subtype))
    return edges


def load_evolution(root, by_lower):
    path = os.path.join(root, 'KNOWLEDGE', 'EVOLUTION.md')
    edges = []
    if not os.path.isfile(path):
        return edges
    with open(path, 'r', encoding='utf-8') as fh:
        text = fh.read()
    for line in text.splitlines():
        if not TABLE_ROW_RE.match(line):
            continue
        cells = _split_row(line)
        if len(cells) < 2 or set(cells[0]) <= set('-: '):
            continue
        if cells[0].startswith('旧称') or '旧称' in cells[0]:
            continue
        joined = ' | '.join(cells)
        ids = extract_ids(joined)
        resolved = [i for i in ids if norm_id(i) in by_lower]
        for a in range(len(resolved)):
            for b in range(a + 1, len(resolved)):
                edges.append((norm_id(resolved[a]), norm_id(resolved[b]), 'alias_or_correction'))
    return edges


def load_open_questions(root, by_lower):
    """Return set of lower card ids explicitly mentioned in OPEN-QUESTIONS.md."""
    path = os.path.join(root, 'RESULTS', 'OPEN-QUESTIONS.md')
    mentioned = set()
    if not os.path.isfile(path):
        return mentioned
    with open(path, 'r', encoding='utf-8') as fh:
        text = fh.read()
    for tid in extract_ids(text):
        if norm_id(tid) in by_lower:
            mentioned.add(norm_id(tid))
    return mentioned


def load_evidence_lineage(root, by_lower):
    path = os.path.join(root, 'RESULTS', 'EVIDENCE-LINEAGE.md')
    mentioned = set()
    if not os.path.isfile(path):
        return mentioned
    with open(path, 'r', encoding='utf-8') as fh:
        text = fh.read()
    for tid in extract_ids(text):
        if norm_id(tid) in by_lower:
            mentioned.add(norm_id(tid))
    return mentioned


# ---------------------------------------------------------------------------
# Cross-domain mapping detection (conservative, evidence-quoted)
# ---------------------------------------------------------------------------
CROSS_DOMAIN_KW = re.compile(r'跨域|类比|同构|映射|对应|桥接')


def detect_cross_domain(root, by_lower, nodes):
    """Flag cards whose body text explicitly discusses a cross-domain mapping,
    and pair them with a synthetic cross-domain hub (low-confidence edge)."""
    flagged = set()
    for node in nodes:
        if CROSS_DOMAIN_KW.search(node.get('body', '')):
            # require that the body also names at least two distinct domains
            toks = set(node.get('topics', []))
            if len(toks) >= 2:
                flagged.add(norm_id(node['asset_id']))
    return flagged


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------
EDGE_CONFIDENCE = {
    'depends_on': 0.95,
    'reverse_depends': 0.90,
    'related': 0.70,
    'shared_research_question': 0.60,
    'correction': 0.90,
    'withdrawal': 0.92,
    'blocked_alias': 0.90,
    'identity_correction': 0.90,
    'scope_limitation': 0.85,
    'rewrite': 0.88,
    'withdrawal_of_surface': 0.88,
    'alias_or_correction': 0.85,
    'correction_source': 0.60,
    'evidence_source': 0.55,
    'open_obligation': 0.40,
    'cross_domain_mapping': 0.40,
}

# Genuine asset-to-asset relations used for cluster connectivity. Hub/doc edges
# (shared_research_question, *_source, open_obligation, cross_domain_mapping) are
# recorded as accepted relations but excluded from connectivity on purpose.
CARD_CARD_TYPES = {
    'depends_on', 'reverse_depends', 'related', 'correction', 'withdrawal',
    'blocked_alias', 'identity_correction', 'scope_limitation', 'rewrite',
    'withdrawal_of_surface', 'alias_or_correction',
}


def build_graph(nodes, by_lower, map_subjects, correction_edges, evolution_edges,
                oq_mentioned, ev_mentioned, cross_domain_flagged):
    graph_nodes = {}     # key -> node-record (cards + hubs + doc nodes)
    edges = []           # accepted typed edges

    def ensure(key, kind, title=None, meta=None):
        if key not in graph_nodes:
            rec = {'id': key, 'node_kind': kind, 'title': title or key}
            if meta:
                rec.update(meta)
            graph_nodes[key] = rec
        return graph_nodes[key]

    for n in nodes:
        key = norm_id(n['asset_id'])
        ensure(key, 'card', n.get('title'), {
            'asset_type': n['asset_type'],
            'status': n['status'],
            'topics': n['topics'],
            'maturity_m': n['maturity_m'],
            'maturity_e': n['maturity_e'],
            'file': n['file'],
            'primary_source': n['primary_source'],
        })

    # hubs + doc nodes
    for s in map_subjects:
        hub_key = 'subject:' + s['id']
        ensure(hub_key, 'map_subject', s.get('title'),
               {'guiding_question': s.get('guiding_question')})
        for cid in s['cards']:
            edges.append({
                'source': cid, 'target': hub_key,
                'type': 'shared_research_question',
                'evidence': 'KNOWLEDGE/MAP.md subject ' + s['id'],
                'confidence': EDGE_CONFIDENCE['shared_research_question'],
            })

    # NOTE: topic/domain membership is stored as a node attribute (see ensure()
    # above) and used for coherence evaluation, but it is deliberately NOT turned
    # into connectivity edges. Connecting every card to a topic hub would merge
    # the entire corpus into one component — the exact "group only by topic
    # label" anti-pattern that contract §4 forbids. Cluster connectivity uses
    # only genuine card->card relations; research-question grouping is applied
    # explicitly via MAP subjects in the clustering pass.

    doc_corrections = ensure('doc:RESULTS/CORRECTIONS.md', 'synthesis_doc',
                             'RESULTS/CORRECTIONS.md')
    doc_evolution = ensure('doc:KNOWLEDGE/EVOLUTION.md', 'synthesis_doc',
                           'KNOWLEDGE/EVOLUTION.md')
    doc_oq = ensure('doc:RESULTS/OPEN-QUESTIONS.md', 'synthesis_doc',
                    'RESULTS/OPEN-QUESTIONS.md')
    doc_ev = ensure('doc:RESULTS/EVIDENCE-LINEAGE.md', 'synthesis_doc',
                    'RESULTS/EVIDENCE-LINEAGE.md')
    hub_xd = ensure('cross_domain', 'cross_domain_hub', 'cross-domain mappings')

    # explicit card-to-card edges
    for n in nodes:
        src = norm_id(n['asset_id'])
        for t in n['dependencies']:
            if norm_id(t) in by_lower:
                edges.append({'source': src, 'target': norm_id(t),
                              'type': 'depends_on',
                              'evidence': '依赖 field in ' + n['file'],
                              'confidence': EDGE_CONFIDENCE['depends_on']})
        for t in n['reverse_dependencies']:
            if norm_id(t) in by_lower:
                edges.append({'source': src, 'target': norm_id(t),
                              'type': 'reverse_depends',
                              'evidence': '被引用/反向依赖 field in ' + n['file'],
                              'confidence': EDGE_CONFIDENCE['reverse_depends']})
        for t in n['related']:
            if norm_id(t) in by_lower:
                edges.append({'source': src, 'target': norm_id(t),
                              'type': 'related',
                              'evidence': '相关文章/资产 field in ' + n['file'],
                              'confidence': EDGE_CONFIDENCE['related']})

    # correction / evolution edges
    for (a, b, sub) in correction_edges:
        edges.append({'source': a, 'target': b, 'type': sub,
                      'evidence': 'RESULTS/CORRECTIONS.md',
                      'confidence': EDGE_CONFIDENCE.get(sub, 0.85)})
        edges.append({'source': a, 'target': 'doc:RESULTS/CORRECTIONS.md',
                      'type': 'correction_source',
                      'evidence': 'RESULTS/CORRECTIONS.md',
                      'confidence': EDGE_CONFIDENCE['correction_source']})
        edges.append({'source': b, 'target': 'doc:RESULTS/CORRECTIONS.md',
                      'type': 'correction_source',
                      'evidence': 'RESULTS/CORRECTIONS.md',
                      'confidence': EDGE_CONFIDENCE['correction_source']})
    for (a, b, sub) in evolution_edges:
        edges.append({'source': a, 'target': b, 'type': sub,
                      'evidence': 'KNOWLEDGE/EVOLUTION.md',
                      'confidence': EDGE_CONFIDENCE.get(sub, 0.85)})
        edges.append({'source': a, 'target': 'doc:KNOWLEDGE/EVOLUTION.md',
                      'type': 'correction_source',
                      'evidence': 'KNOWLEDGE/EVOLUTION.md',
                      'confidence': EDGE_CONFIDENCE['correction_source']})
        edges.append({'source': b, 'target': 'doc:KNOWLEDGE/EVOLUTION.md',
                      'type': 'correction_source',
                      'evidence': 'KNOWLEDGE/EVOLUTION.md',
                      'confidence': EDGE_CONFIDENCE['correction_source']})

    # open-obligation + evidence-source links
    for cid in oq_mentioned:
        edges.append({'source': cid, 'target': 'doc:RESULTS/OPEN-QUESTIONS.md',
                      'type': 'open_obligation',
                      'evidence': 'explicit mention in RESULTS/OPEN-QUESTIONS.md',
                      'confidence': EDGE_CONFIDENCE['open_obligation']})
    for cid in ev_mentioned:
        edges.append({'source': cid, 'target': 'doc:RESULTS/EVIDENCE-LINEAGE.md',
                      'type': 'evidence_source',
                      'evidence': 'explicit mention in RESULTS/EVIDENCE-LINEAGE.md',
                      'confidence': EDGE_CONFIDENCE['evidence_source']})

    # cross-domain
    for cid in cross_domain_flagged:
        edges.append({'source': cid, 'target': 'cross_domain',
                      'type': 'cross_domain_mapping',
                      'evidence': 'explicit cross-domain wording + >=2 topic domains in card body',
                      'confidence': EDGE_CONFIDENCE['cross_domain_mapping']})

    return graph_nodes, edges


# ---------------------------------------------------------------------------
# Candidate signals (NOT accepted relations)
# ---------------------------------------------------------------------------
STOP = set('的 了 是 在 和 与 或 一个 一种 这 那 不 也 都 就 而 及 等 被 把 对 从 以 为 其 该 各 中 上 下 内 外 我们 他们 它们 一种 通过 由于 因此 但是 如果 可以 没有 不是 以及 以及'.split())


def tokenize(text):
    toks = []
    # ascii words
    for w in re.findall(r'[a-zA-Z][a-zA-Z0-9_\-]{2,}', text):
        toks.append(w.lower())
    # CJK unigrams
    for ch in re.findall(r'[一-鿿]', text):
        toks.append('c:' + ch)
    return toks


def build_semantic_candidates(nodes, threshold=0.25, cap=200):
    """TF-IDF cosine over card semantic_text (structured prose fields).
    Candidate signal ONLY — never an accepted relation."""
    docs = [(norm_id(n['asset_id']), tokenize(n.get('semantic_text', '') or n.get('body', ''))) for n in nodes]
    df = Counter()
    for _, toks in docs:
        for t in set(toks):
            df[t] += 1
    n_docs = len(docs)
    # drop overly common / stop tokens
    vocab = {t for t, c in df.items() if c <= max(2, n_docs * 0.4) and t not in STOP}
    # build tf-idf vectors (dicts)
    vectors = []
    for _, toks in docs:
        tf = Counter(t for t in toks if t in vocab)
        total = sum(tf.values()) or 1
        vec = {}
        for t, c in tf.items():
            idf = math.log((1 + n_docs) / (1 + df[t])) + 1
            vec[t] = (c / total) * idf
        vectors.append(vec)
    # cosine
    pairs = []
    for i in range(n_docs):
        for j in range(i + 1, n_docs):
            vi, vj = vectors[i], vectors[j]
            if not vi or not vj:
                continue
            common = set(vi) & set(vj)
            if not common:
                continue
            dot = sum(vi[t] * vj[t] for t in common)
            ni = math.sqrt(sum(v * v for v in vi.values()))
            nj = math.sqrt(sum(v * v for v in vj.values()))
            if ni == 0 or nj == 0:
                continue
            cos = dot / (ni * nj)
            if cos >= threshold:
                pairs.append({
                    'a': docs[i][0], 'b': docs[j][0],
                    'cosine': round(cos, 4),
                })
    pairs.sort(key=lambda p: p['cosine'], reverse=True)
    return pairs[:cap]


def build_citation_overlap(nodes, cap=200):
    """Cards sharing >=1 explicit evidence source file. Candidate signal ONLY."""
    src_to_cards = defaultdict(list)
    for n in nodes:
        for s in n.get('evidence_sources', []):
            # normalise to a short key
            key = s.split('/')[-1]
            src_to_cards[key].append(norm_id(n['asset_id']))
    groups = []
    for src, cards in src_to_cards.items():
        cards = sorted(set(cards))
        if len(cards) >= 2:
            groups.append({'source': src, 'cards': cards,
                           'count': len(cards)})
    groups.sort(key=lambda g: g['count'], reverse=True)
    return groups[:cap]


# ---------------------------------------------------------------------------
# Clustering + coherence evaluation
# ---------------------------------------------------------------------------
TOPIC_QUESTION = {
    'MATHEMATICS': '对象、运算、定义域、证明与反例在数学上究竟完成到哪一步？',
    'PHYSICS': '门控模型能支持什么有界物理投影，哪些统一与观测义务仍未完成？',
    'SYSTEMS': '系统论与机制建模在何处提供了可检验的机制，而非仅命名？',
    'COGNITION': '关于认知、Agent 与行动的断言，哪些越过了事实边界？',
    'ARCHITECTURE_GOVERNANCE': '架构、治理与自我纠错机制如何保证仓库主张不被悄悄升级？',
    'WRITING_PUBLICATION': '面向公众的表达如何在可读与不越界之间取得平衡？',
    'OPERATIONS_EVIDENCE': '迭代、验证与证据工程如何使结论可复现、可 adjudicate？',
}


def connected_components(graph_nodes, edges):
    adj = defaultdict(set)
    for e in edges:
        if e['source'] in graph_nodes and e['target'] in graph_nodes:
            adj[e['source']].add(e['target'])
            adj[e['target']].add(e['source'])
    seen = set()
    comps = []
    for key in graph_nodes:
        if key in seen:
            continue
        stack = [key]
        comp = set()
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            comp.add(cur)
            for nb in adj[cur]:
                if nb not in seen:
                    stack.append(nb)
        comps.append(comp)
    return comps


def evaluate_cluster(member_keys, graph_nodes, comp_edges, map_subjects, sub_index):
    cards = [graph_nodes[k] for k in member_keys if graph_nodes[k]['node_kind'] == 'card']
    cards.sort(key=lambda c: c['id'])  # deterministic member order
    n = len(cards)
    if n == 0:
        return None
    topics = Counter()
    for c in cards:
        for t in c.get('topics', []):
            topics[t] += 1
    distinct_domains = len(topics)
    dominant_topic, dominant_count = (topics.most_common(1)[0] if topics else (None, 0))

    # edge-type presence among member-member / member-hub edges
    etypes = set()
    has_correction = False
    has_dependency = False
    has_card_card = False
    subject_hubs = set()
    for e in comp_edges:
        if e['source'] in member_keys or e['target'] in member_keys:
            etypes.add(e['type'])
            if e['type'] in ('correction', 'withdrawal', 'blocked_alias',
                             'identity_correction', 'scope_limitation',
                             'rewrite', 'withdrawal_of_surface', 'alias_or_correction'):
                has_correction = True
            if e['type'] in ('depends_on', 'reverse_depends'):
                has_dependency = True
            if (e['source'] in member_keys and e['target'] in member_keys
                    and graph_nodes[e['source']]['node_kind'] == 'card'
                    and graph_nodes[e['target']]['node_kind'] == 'card'):
                has_card_card = True
            if e['target'].startswith('subject:') or e['source'].startswith('subject:'):
                subject_hubs.add(e['target'] if e['target'].startswith('subject:') else e['source'])

    has_internal_structure = has_card_card or has_correction
    dominant_ratio = (dominant_count / n) if n else 0

    # disposition logic
    disposition = 'ARTICLE_CANDIDATE'
    rationale = ''
    if n == 1:
        disposition = 'REFERENCE_LEAF'
        rationale = '单卡孤立节点：无足够内部关系支撑独立文章，宜并入相关簇或作参考。'
    elif n > 40 and (not has_internal_structure):
        disposition = 'SPLIT_TOO_BROAD'
        rationale = ('簇过大(%d 卡)且缺乏卡间依赖/纠正主轴，仅由研究问题中枢或主题聚合，'
                     '按来源族/研究问题拆分以防止"按主题标签"式笼统成篇。' % n)
    elif distinct_domains >= 4 and dominant_ratio < 0.4 and (not has_correction):
        disposition = 'REFERENCE_HETEROGENEOUS'
        rationale = ('跨 %d 个主题域且主导主题占比<0.4、无纠正主轴，'
                     '属异质杂凑，不宜合为一篇文章，保留为参考集合。' % distinct_domains)
    elif n >= 2 and (not has_internal_structure) and distinct_domains <= 1:
        disposition = 'REFERENCE_TAXONOMIC'
        rationale = ('仅由中枢(主题/研究问题)边连接、单一主题、无卡间依赖/证据/纠正结构，'
                     '属纯分类罗列，保留为参考集合而非文章；文章须由连贯问题定义。')

    # central question
    guiding = None
    if len(subject_hubs) == 1:
        hid = next(iter(subject_hubs))
        guiding = graph_nodes.get(hid, {}).get('guiding_question')
    if not guiding:
        if has_correction:
            guiding = '这里发生了什么纠正、撤回或回弹？当前的断言上限是什么？'
        elif dominant_topic and dominant_topic in TOPIC_QUESTION:
            guiding = TOPIC_QUESTION[dominant_topic]
        else:
            guiding = '这些资产共同回答什么连贯问题？（需编辑进一步界定）'

    return {
        'size': n,
        'disposition': disposition,
        'rationale': rationale,
        'dominant_topic': dominant_topic,
        'dominant_ratio': round(dominant_ratio, 3),
        'distinct_domains': distinct_domains,
        'topic_distribution': dict(topics.most_common()),
        'map_subjects': [s[len('subject:'):] for s in subject_hubs],
        'has_correction': has_correction,
        'has_dependency': has_dependency,
        'edge_types': sorted(etypes),
        'proposed_central_question': guiding,
        'members': [{
            'id': c['id'], 'title': c.get('title'),
            'asset_type': c.get('asset_type'), 'status': c.get('status'),
            'topics': c.get('topics'),
        } for c in cards],
    }


def source_family(node):
    ps = node.get('primary_source') or ''
    parts = ps.split('/')
    if len(parts) >= 2:
        return parts[0] + '/' + parts[1]
    return ps or 'UNCLASSIFIED'


def split_too_broad(member_keys, graph_nodes, map_subj_membership):
    """Split a too-broad component by (1) MAP research-subject, then (2) source
    family (first two path segments of primary_source). This avoids splitting
    merely by topic label while keeping the subdivision defensible."""
    by_subj = defaultdict(list)
    no_subj = []
    for k in member_keys:
        node = graph_nodes[k]
        if node['node_kind'] != 'card':
            continue
        subs = map_subj_membership.get(k)
        if subs:
            for s in subs:
                by_subj[s].append(k)
        else:
            no_subj.append(k)
    groups = []
    for s, keys in sorted(by_subj.items()):
        groups.append(('subject:' + s, keys))
    by_fam = defaultdict(list)
    for k in no_subj:
        by_fam[source_family(graph_nodes[k])].append(k)
    for fam, keys in sorted(by_fam.items()):
        groups.append((fam, keys))
    return groups


def apply_split(ev, keys, graph_nodes, edges, map_subjects, map_subj_membership,
               register, note):
    """Attempt to split a too-broad cluster. If it cannot be subdivided (only one
    resulting group), the parent itself is demoted to REFERENCE_TAXONOMIC rather
    than emitting a redundant duplicate child."""
    subs = split_too_broad(keys, graph_nodes, map_subj_membership)
    if len(subs) <= 1:
        ev['disposition'] = 'REFERENCE_TAXONOMIC'
        ev['rationale'] += note
        register(ev)
        return False
    sub_ids = []
    for topic, sk in subs:
        se = [e for e in edges if e['source'] in set(sk) and e['target'] in set(sk)]
        sub_ev = evaluate_cluster(sk, graph_nodes, se, map_subjects, None)
        if sub_ev is None:
            continue
        if sub_ev['disposition'] == 'SPLIT_TOO_BROAD':
            sub_ev['disposition'] = 'REFERENCE_TAXONOMIC'
            sub_ev['rationale'] += '（已拆分一次仍过大，保留为参考。）'
        sub_ev['split_group'] = topic
        register(sub_ev)
        sub_ids.append(sub_ev['id'])
    ev['sub_clusters'] = sub_ids
    register(ev)
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='analysis/corpus-relation')
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    nodes, by_lower = load_cards(root)
    map_subjects = load_map_subjects(root, by_lower)
    correction_edges = load_corrections(root, by_lower)
    evolution_edges = load_evolution(root, by_lower)
    oq_mentioned = load_open_questions(root, by_lower)
    ev_mentioned = load_evidence_lineage(root, by_lower)
    cross_domain_flagged = detect_cross_domain(root, by_lower, nodes)

    graph_nodes, edges = build_graph(
        nodes, by_lower, map_subjects, correction_edges, evolution_edges,
        oq_mentioned, ev_mentioned, cross_domain_flagged)

    # candidate signals
    semantic = build_semantic_candidates(nodes)
    semantic.sort(key=lambda p: (-p['cosine'], p['a'], p['b']))
    citation = build_citation_overlap(nodes)
    citation.sort(key=lambda g: (-g['count'], g['source']))

    # clustering
    # map subject membership: card_lower -> [subject_id, ...]
    map_subj_membership = defaultdict(list)
    subject_guide = {}
    for s in map_subjects:
        subject_guide[s['id']] = s.get('guiding_question')
        for cid_l in s['cards']:
            map_subj_membership[cid_l].append(s['id'])

    # Pass A: connected components over GENUINE card->card relations only.
    comp_edges_conn = [e for e in edges
                       if e['source'] in by_lower and e['target'] in by_lower
                       and e['type'] in CARD_CARD_TYPES]
    adj = defaultdict(set)
    for e in comp_edges_conn:
        adj[e['source']].add(e['target'])
        adj[e['target']].add(e['source'])
    seen = set()
    card_comps = []
    for k in by_lower:
        if k in seen or graph_nodes.get(k, {}).get('node_kind') != 'card':
            continue
        stack = [k]
        comp = set()
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            comp.add(cur)
            for nb in adj[cur]:
                if nb not in seen:
                    stack.append(nb)
        card_comps.append(comp)

    clusters = []
    assigned = set()
    cid = 0

    def register(ev):
        nonlocal cid
        ev['id'] = 'C%03d' % cid
        clusters.append(ev)
        cid += 1

    # Pass A evaluation + split (only multi-card components; true singletons
    # are left for Pass B grouping).
    for comp in card_comps:
        card_members = [k for k in comp if graph_nodes[k]['node_kind'] == 'card']
        if not card_members:
            continue
        if len(card_members) >= 2:
            assigned.update(card_members)
        comp_edges = [e for e in edges
                      if e['source'] in comp and e['target'] in comp]
        ev = evaluate_cluster(card_members, graph_nodes, comp_edges, map_subjects, None)
        if ev is None:
            continue
        if len(card_members) < 2:
            # singleton: leave for Pass B grouping (do not register here)
            continue
        if ev['disposition'] == 'SPLIT_TOO_BROAD':
            apply_split(ev, card_members, graph_nodes, edges, map_subjects,
                       map_subj_membership, register,
                       '（按来源族/研究问题尝试拆分，但来源族未分化，无法进一步细分；'
                       '保留为参考，待编辑界定子问题。）')
        else:
            register(ev)

    # Pass B: unconnected cards -> group by MAP research-subject (has guiding
    # question) or by topic-domain (thematic; flagged as needing question def).
    unassigned = [k for k in by_lower
                  if graph_nodes.get(k, {}).get('node_kind') == 'card' and k not in assigned]
    by_subj = defaultdict(list)
    no_subj = []
    for k in unassigned:
        subs = map_subj_membership.get(k)
        if subs:
            for s in subs:
                by_subj[s].append(k)
        else:
            no_subj.append(k)
    for s, keys in sorted(by_subj.items()):
        ce = [e for e in edges if e['source'] in set(keys) and e['target'] in set(keys)]
        ev = evaluate_cluster(keys, graph_nodes, ce, map_subjects, None)
        if ev is None:
            continue
        ev['cluster_basis'] = 'map_subject:' + s
        gq = subject_guide.get(s)
        if gq:
            ev['proposed_central_question'] = gq
        if ev['disposition'] == 'SPLIT_TOO_BROAD':
            apply_split(ev, keys, graph_nodes, edges, map_subjects,
                       map_subj_membership, register,
                       '（按来源族/研究问题尝试拆分，但来源族未分化，无法进一步细分；'
                       '保留为参考，待编辑界定子问题。）')
        else:
            register(ev)
    by_topic = defaultdict(list)
    for k in no_subj:
        tops = graph_nodes[k].get('topics') or ['UNCLASSIFIED']
        by_topic[tops[0]].append(k)
    for t, keys in sorted(by_topic.items()):
        ce = [e for e in edges if e['source'] in set(keys) and e['target'] in set(keys)]
        ev = evaluate_cluster(keys, graph_nodes, ce, map_subjects, None)
        if ev is None:
            continue
        ev['cluster_basis'] = 'topic:' + t
        if ev['disposition'] == 'SPLIT_TOO_BROAD':
            apply_split(ev, keys, graph_nodes, edges, map_subjects,
                       map_subj_membership, register,
                       '（按来源族/研究问题尝试拆分，但来源族未分化，无法进一步细分；'
                       '保留为参考，待编辑界定子问题。）')
        else:
            # thematic grouping by topic label alone: honest flag
            if ev['disposition'] == 'ARTICLE_CANDIDATE':
                ev['disposition'] = 'REFERENCE_TAXONOMIC'
                ev['rationale'] = ('仅按主题标签聚合(%s)、无研究问题中枢或卡间结构；'
                                   '保留为参考集合，文章须先由编辑界定连贯问题。' % t)
            register(ev)

    # stats
    type_counter = Counter(n['asset_type'] for n in nodes)
    # deterministic edge ordering (independent of set-iteration hash seed)
    edges.sort(key=lambda e: (e['type'], e['source'], e['target']))
    edge_counter = Counter(e['type'] for e in edges)
    disp_counter = Counter(c['disposition'] for c in clusters)
    n_singletons = sum(1 for c in clusters if c['size'] == 1)

    graph_doc = {
        'generated_by': 'tools/build_corpus_relation_graph.py',
        'repo_root': root,
        'node_count': len(graph_nodes),
        'card_node_count': len(nodes),
        'edge_count': len(edges),
        'nodes': [graph_nodes[k] for k in sorted(graph_nodes)],
        'edges': edges,
        'candidate_signals': {
            'semantic_similarity': {
                'note': 'CANDIDATE SIGNAL ONLY — never an accepted relation.',
                'pair_count': len(semantic),
                'pairs': semantic,
            },
            'citation_overlap': {
                'note': 'CANDIDATE SIGNAL ONLY — shared evidence source; not an accepted relation.',
                'group_count': len(citation),
                'groups': citation,
            },
        },
    }
    cluster_doc = {
        'cluster_count': len(clusters),
        'disposition_summary': dict(disp_counter),
        'singleton_count': n_singletons,
        'clusters': clusters,
    }
    with open(os.path.join(out_dir, 'corpus_relation_graph.json'), 'w', encoding='utf-8') as fh:
        json.dump(graph_doc, fh, ensure_ascii=False, indent=2, sort_keys=True)
    with open(os.path.join(out_dir, 'article_cluster_candidates.json'), 'w', encoding='utf-8') as fh:
        json.dump(cluster_doc, fh, ensure_ascii=False, indent=2, sort_keys=True)

    # markdown report
    lines = []
    lines.append('# 受治理语料关系分析（TASK 104 · §4）\n')
    lines.append('本分析由 `tools/build_corpus_relation_graph.py` 确定性生成，'
                 '无网络依赖，仅使用 Python 标准库。\n')
    lines.append('## 规模统计\n')
    lines.append('- 资产卡节点：%d（%s）' % (
        len(nodes),
        ', '.join('%s=%d' % (k, v) for k, v in sorted(type_counter.items()))))
    lines.append('- 图节点总数：%d（含 MAP 主题中枢、合成文档节点、跨域中枢）' % len(graph_nodes))
    lines.append('- 受治理边总数：%d' % len(edges))
    lines.append('- 边类型分布：%s' % ', '.join(
        '%s=%d' % (k, v) for k, v in sorted(edge_counter.items())))
    lines.append('- 候选簇总数：%d；单卡叶节点：%d' % (len(clusters), n_singletons))
    lines.append('- 簇处置分布：%s' % ', '.join(
        '%s=%d' % (k, v) for k, v in sorted(disp_counter.items())))
    lines.append('\n## 关系类型与证据（受治理边）\n')
    lines.append('每条被接受的关系都声明 type / evidence / confidence。'
                 '语义相似与引用重叠仅作候选信号，记录于 `corpus_relation_graph.json` 的 '
                 '`candidate_signals`，**不**构成规范关系。\n')
    lines.append('## 文章簇候选（按处置分类）\n')
    for disp in ('ARTICLE_CANDIDATE', 'SPLIT_TOO_BROAD', 'REFERENCE_HETEROGENEOUS',
                 'REFERENCE_TAXONOMIC', 'REFERENCE_LEAF'):
        grp = [c for c in clusters if c['disposition'] == disp]
        if not grp:
            continue
        lines.append('\n### %s（%d）\n' % (disp, len(grp)))
        for c in grp:
            lines.append('- **%s** 规模=%d 主导主题=%s(%.2f) 域数=%d' % (
                c['id'], c['size'], c['dominant_topic'], c['dominant_ratio'],
                c['distinct_domains']))
            lines.append('  - 中心问题候选：%s' % c['proposed_central_question'])
            lines.append('  - 处置理由：%s' % c['rationale'])
            if c.get('map_subjects'):
                lines.append('  - MAP 主题：%s' % ', '.join(c['map_subjects']))
            if c['size'] <= 25:
                members = ', '.join(m['id'] for m in c['members'])
                lines.append('  - 成员：%s' % members)
    lines.append('\n## 候选信号（非规范关系，仅供编辑参考）\n')
    lines.append('- 语义相似候选对：%d（最高 cosine=%.3f）' % (
        len(semantic), semantic[0]['cosine'] if semantic else 0.0))
    lines.append('- 引用重叠组：%d' % len(citation))
    lines.append('\n## 方法与局限\n')
    lines.append('- 资产单元 = 339 张重点卡（284 结果/文章 + 12 函数 + 43 非函数断言）。')
    lines.append('- 显式边来自卡的 `依赖`/`被引用`/`相关`/`主题` 字段，'
                 '以及 MAP 主题中枢、CORRECTIONS/EVOLUTION 表、OPEN-QUESTIONS/EVIDENCE-LINEAGE 显式提及。')
    lines.append('- 跨域映射仅当卡体显式出现跨域措辞且 ≥2 主题域时才标记，低置信。')
    lines.append('- 簇处置启发式检测：过大拆分、异质拒绝、纯分类保留为参考、单卡叶节点。')
    lines.append('- 机器无法判定文学质量；文章是否成篇仍需编辑按 §5 准则人工裁定。')
    with open(os.path.join(out_dir, 'RELATION-ANALYSIS.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')

    # console summary
    print('nodes=%d cards=%d edges=%d clusters=%d singletons=%d' % (
        len(graph_nodes), len(nodes), len(edges), len(clusters), n_singletons))
    print('dispositions: ' + ', '.join('%s=%d' % (k, v) for k, v in sorted(disp_counter.items())))
    print('outputs -> ' + out_dir)


if __name__ == '__main__':
    main()
