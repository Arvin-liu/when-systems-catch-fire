#!/usr/bin/env python3
"""Task162 longform-input and real-history research package.

This file is deliberately research-only.  The external track uses anonymous
factors and generic lexical/argument features until its own freeze is complete.
The history track reads only repository objects and neutralizes Task160 lead
labels before the two procedural adjudication passes.  Nothing here is imported
by canonical runtime code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path
from statistics import median
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pypdf import PdfReader


IGNITION = Path(__file__).resolve().parents[2]
REPO = IGNITION.parent
TASK = "IGNITION-20260907-162"
OUT = IGNITION / "data/research/longform-emergence-and-historical-adjudication-2026-09-07"
CACHE = Path(os.environ.get("TASK162_CORPUS_CACHE", "/tmp/ignition-20260907-162-corpus"))
PROTOCOL = OUT / "source-search-protocol.json"
SELECTION = OUT / "source-selection-freeze.json"
TASK160 = IGNITION / "data/research/basis-escape-v2-2026-09-07"
TASK161 = IGNITION / "data/research/state-vs-transition-semantics-2026-09-07"
UA = "IGNITION-20260907-162-research/1.0"

# This list is the output of the frozen, answer-independent source order.  The
# titles are metadata, not induction labels; all downstream candidate names are
# generated as EL-Xnn.
SOURCES = [
    {"work_id": "GUT-2009", "title": "The Origin of Species by Means of Natural Selection", "author": "Charles Darwin", "year": 1859, "domain": "natural_sciences_biology_evolution", "publication_type": "public_domain_book", "source_page": "https://www.gutenberg.org/ebooks/2009", "source_url": "https://www.gutenberg.org/cache/epub/2009/pg2009.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-2300", "title": "The Descent of Man, and Selection in Relation to Sex", "author": "Charles Darwin", "year": 1871, "domain": "natural_sciences_biology_evolution", "publication_type": "public_domain_book", "source_page": "https://www.gutenberg.org/ebooks/2300", "source_url": "https://www.gutenberg.org/cache/epub/2300/pg2300.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-15491", "title": "Micrographia", "author": "Robert Hooke", "year": 1665, "domain": "natural_sciences_biology_evolution", "publication_type": "public_domain_monograph", "source_page": "https://www.gutenberg.org/ebooks/15491", "source_url": "https://www.gutenberg.org/cache/epub/15491/pg15491.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-57493", "title": "The Natural History of Pliny, Volume 1 (of 6)", "author": "the Elder Pliny; translated by John Bostock and Henry T. Riley", "year": 1855, "domain": "natural_sciences_biology_evolution", "publication_type": "public_domain_monograph", "source_page": "https://www.gutenberg.org/ebooks/57493", "source_url": "https://www.gutenberg.org/cache/epub/57493/pg57493.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-27513", "title": "The Book of the National Parks", "author": "Robert Sterling Yard", "year": 1919, "domain": "ecology_complex_systems", "publication_type": "public_domain_book", "source_page": "https://www.gutenberg.org/ebooks/27513", "source_url": "https://www.gutenberg.org/cache/epub/27513/pg27513.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-66078", "title": "A Treatise on Mechanics", "author": "Henry Kater and Dionysius Lardner", "year": 1830, "domain": "engineering_safety_control", "publication_type": "public_domain_monograph", "source_page": "https://www.gutenberg.org/ebooks/66078", "source_url": "https://www.gutenberg.org/cache/epub/66078/pg66078.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-49445", "title": "Mechanics: The Science of Machinery", "author": "A. Russell Bond", "year": 1915, "domain": "engineering_safety_control", "publication_type": "public_domain_book", "source_page": "https://www.gutenberg.org/ebooks/49445", "source_url": "https://www.gutenberg.org/cache/epub/49445/pg49445.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-42602", "title": "The Steam Engine Explained and Illustrated", "author": "Dionysius Lardner", "year": 1858, "domain": "engineering_safety_control", "publication_type": "public_domain_monograph", "source_page": "https://www.gutenberg.org/ebooks/42602", "source_url": "https://www.gutenberg.org/cache/epub/42602/pg42602.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "NIST-800-37R2", "title": "Risk Management Framework for Information Systems and Organizations", "author": "National Institute of Standards and Technology", "year": 2018, "domain": "engineering_safety_control", "publication_type": "official_open_technical_handbook", "source_page": "https://csrc.nist.gov/pubs/sp/800/37/r2/final", "source_url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-37r2.pdf", "kind": "pdf", "license_basis": "United States government technical publication; official NIST full-text PDF"},
    {"work_id": "NIST-800-53R5", "title": "Security and Privacy Controls for Information Systems and Organizations", "author": "National Institute of Standards and Technology", "year": 2020, "domain": "computer_science_distributed_protocols", "publication_type": "official_open_technical_handbook", "source_page": "https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final", "source_url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf", "kind": "pdf", "license_basis": "United States government technical publication; official NIST full-text PDF"},
    {"work_id": "NIST-800-218", "title": "Secure Software Development Framework", "author": "National Institute of Standards and Technology", "year": 2022, "domain": "computer_science_distributed_protocols", "publication_type": "official_open_technical_handbook", "source_page": "https://csrc.nist.gov/pubs/sp/800/218/final", "source_url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf", "kind": "pdf", "license_basis": "United States government technical publication; official NIST full-text PDF"},
    {"work_id": "RFC-9000", "title": "QUIC: A UDP-Based Multiplexed and Secure Transport", "author": "IETF QUIC Working Group", "year": 2021, "domain": "computer_science_distributed_protocols", "publication_type": "official_open_standard", "source_page": "https://www.rfc-editor.org/rfc/rfc9000", "source_url": "https://www.rfc-editor.org/rfc/rfc9000.txt", "kind": "text", "license_basis": "IETF RFC Editor public full text under IETF Trust legal provisions"},
    {"work_id": "RFC-9110", "title": "HTTP Semantics", "author": "IETF HTTP Working Group", "year": 2022, "domain": "computer_science_distributed_protocols", "publication_type": "official_open_standard", "source_page": "https://www.rfc-editor.org/rfc/rfc9110", "source_url": "https://www.rfc-editor.org/rfc/rfc9110.txt", "kind": "text", "license_basis": "IETF RFC Editor public full text under IETF Trust legal provisions"},
    {"work_id": "GUT-3300", "title": "An Inquiry into the Nature and Causes of the Wealth of Nations", "author": "Adam Smith", "year": 1776, "domain": "economics_institutions_organization", "publication_type": "public_domain_book", "source_page": "https://www.gutenberg.org/ebooks/3300", "source_url": "https://www.gutenberg.org/cache/epub/3300/pg3300.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "OPENSTAX-ECON-3E", "title": "Principles of Economics 3e", "author": "Steven A. Greenlaw, David Shapiro, and Daniel MacDonald", "year": 2022, "domain": "economics_institutions_organization", "publication_type": "open_textbook", "source_page": "https://openstax.org/details/books/principles-economics-3e", "source_url": "https://assets.openstax.org/oscms-prodcms/media/documents/principles-economics-3e_-_WEB.pdf", "kind": "pdf", "license_basis": "OpenStax landing page states Creative Commons Attribution-NonCommercial-ShareAlike 4.0"},
    {"work_id": "GUT-1497", "title": "The Republic", "author": "Plato; translated by Benjamin Jowett", "year": -380, "domain": "philosophy_logic_science", "publication_type": "public_domain_monograph", "source_page": "https://www.gutenberg.org/ebooks/1497", "source_url": "https://www.gutenberg.org/cache/epub/1497/pg1497.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-4705", "title": "A Treatise of Human Nature", "author": "David Hume", "year": 1739, "domain": "philosophy_logic_science", "publication_type": "public_domain_monograph", "source_page": "https://www.gutenberg.org/ebooks/4705", "source_url": "https://www.gutenberg.org/cache/epub/4705/pg4705.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-4280", "title": "The Critique of Pure Reason", "author": "Immanuel Kant; translated by J. M. D. Meiklejohn", "year": 1781, "domain": "philosophy_logic_science", "publication_type": "public_domain_monograph", "source_page": "https://www.gutenberg.org/ebooks/4280", "source_url": "https://www.gutenberg.org/cache/epub/4280/pg4280.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-815", "title": "Democracy in America", "author": "Alexis de Tocqueville", "year": 1835, "domain": "history_social_systems", "publication_type": "public_domain_book", "source_page": "https://www.gutenberg.org/ebooks/815", "source_url": "https://www.gutenberg.org/cache/epub/815/pg815.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-7142", "title": "The History of the Peloponnesian War", "author": "Thucydides; translated by Richard Crawley", "year": -431, "domain": "history_social_systems", "publication_type": "public_domain_monograph", "source_page": "https://www.gutenberg.org/ebooks/7142", "source_url": "https://www.gutenberg.org/cache/epub/7142/pg7142.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "GUT-1232", "title": "The Prince", "author": "Niccolo Machiavelli; translated by W. K. Marriott", "year": 1532, "domain": "history_social_systems", "publication_type": "public_domain_monograph", "source_page": "https://www.gutenberg.org/ebooks/1232", "source_url": "https://www.gutenberg.org/cache/epub/1232/pg1232.txt", "kind": "text", "license_basis": "Project Gutenberg public-domain-in-USA notice and Project Gutenberg License"},
    {"work_id": "OPENSTAX-PSYCH-2E", "title": "Psychology 2e", "author": "Rose M. Spielman, William J. Jenkins, and Marilyn D. Lovett", "year": 2020, "domain": "cognition_psychology", "publication_type": "open_textbook", "source_page": "https://openstax.org/details/books/psychology-2e", "source_url": "https://assets.openstax.org/oscms-prodcms/media/documents/Psychology2e_WEB.pdf", "kind": "pdf", "license_basis": "OpenStax landing page states Creative Commons Attribution-NonCommercial-ShareAlike 4.0"},
    {"work_id": "OPENSTAX-CALC-V1", "title": "Calculus Volume 1", "author": "Gilbert Strang and Edwin Herman", "year": 2016, "domain": "mathematics_formal_systems", "publication_type": "open_textbook", "source_page": "https://openstax.org/details/books/calculus-volume-1", "source_url": "https://assets.openstax.org/oscms-prodcms/media/documents/calculus-volume-1_-_WEB.pdf", "kind": "pdf", "license_basis": "OpenStax landing page states Creative Commons Attribution-NonCommercial-ShareAlike 4.0"},
]

FEATURES = {
    "01": ("causal_explanation", ("cause", "because", "therefore", "effect", "result", "consequence", "why")),
    "02": ("constraint_condition", ("rule", "law", "constraint", "condition", "limit", "must", "cannot", "prohibit")),
    "03": ("ordered_procedure", ("order", "before", "after", "first", "then", "next", "sequence", "step", "stage")),
    "04": ("observation_support", ("evidence", "proof", "observe", "experiment", "test", "measure", "data")),
    "05": ("failure_exception", ("error", "failure", "fault", "exception", "problem", "risk", "wrong")),
    "06": ("reversal_repetition", ("return", "revert", "reverse", "restore", "undo", "again", "cycle")),
    "07": ("identity_particularity", ("same", "identity", "individual", "object", "person", "specific", "particular")),
    "08": ("scope_boundary", ("scope", "boundary", "domain", "context", "case", "under")),
    "09": ("regulation_response", ("feedback", "adjust", "regulate", "control", "response", "adapt")),
    "10": ("model_definition", ("model", "theory", "concept", "definition", "hypothesis", "explain")),
}
STOPWORDS = set("a an and are as at be by for from in into is it its of on or that the their this to was were with without we you your".split())
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+(?:['’\-][A-Za-zÀ-ÖØ-öø-ÿ0-9]+)?")
HEADING_RE = re.compile(r"^(?:(?:chapter|book|part|section|lecture|volume|appendix|rfc)\b|\d+(?:\.\d+){0,3}\s+)[^\n]{1,180}$", re.I)
LEAK_RE = re.compile(r"(?i)transition(?:[- ]over[- ]state)?|state[ -]vs[ -]transition|first[ -]class transition|\bMS\b|\bMT\b|BF-X\d+|V/S/E|64 meta-protocol|next leap|Task ?16[01]")


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def git_text(*args: str, check: bool = False) -> str:
    p = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=check)
    return p.stdout.strip()


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def normalized_text(raw: str) -> str:
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in raw.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def download(path: Path, url: str) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    if not path.exists() or path.stat().st_size == 0:
        request = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        last_error = None
        for attempt in range(1, 3):
            try:
                with urlopen(request, timeout=180) as response, path.open("wb") as out:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        out.write(chunk)
                last_error = None
                break
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                last_error = repr(exc)
                if path.exists():
                    path.unlink()
                time.sleep(attempt)
        if last_error:
            return {"status": "RETRIEVAL_FAILED", "error": last_error, "elapsed_seconds": round(time.time() - started, 3)}
    return {"status": "RETRIEVED", "bytes": path.stat().st_size, "sha256": file_digest(path), "elapsed_seconds": round(time.time() - started, 3)}


def extract_source(spec: dict[str, object], raw_path: Path) -> tuple[str, int | None, str]:
    if spec["kind"] == "pdf":
        reader = PdfReader(str(raw_path))
        pages = []
        for idx, page in enumerate(reader.pages, 1):
            pages.append(f"\n[PAGE {idx}]\n{page.extract_text() or ''}")
        return normalized_text("\n".join(pages)), len(reader.pages), "pypdf-page-extraction"
    return normalized_text(raw_path.read_text(encoding="utf-8", errors="replace")), None, "utf8-text-extraction"


def segment_ranges(text: str, tokens: list[str], kind: str) -> list[dict[str, object]]:
    lines = text.splitlines()
    offsets = []
    cursor = 0
    for line in lines:
        offsets.append((cursor, cursor + len(line)))
        cursor += len(line) + 1
    candidates = []
    line_token_positions = []
    running_tokens = 0
    for idx, line in enumerate(lines):
        line_token_positions.append(running_tokens)
        running_tokens += len(tokenize(line))
        compact = line.strip()
        if not compact or len(compact) > 180 or len(compact.split()) > 28:
            continue
        if HEADING_RE.match(compact) or (compact.isupper() and len(compact.split()) <= 14 and len(compact) > 3):
            candidates.append((line_token_positions[idx], compact))
    starts = []
    for token_pos, label in candidates:
        if not starts or token_pos - starts[-1][0] >= 80:
            starts.append((token_pos, label))
    if len(starts) < 4:
        starts = [(i, f"chunk-{i // 1200 + 1:03d}") for i in range(0, len(tokens), 1200)]
    elif starts and starts[0][0] > 0:
        starts.insert(0, (0, "preamble"))
    result = []
    for i, (start, label) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(tokens)
        if end <= start:
            continue
        result.append({"sequence": len(result) + 1, "label": label[:180], "start_word": start, "end_word": end, "word_count": end - start})
    return result


def feature_counts(tokens: list[str]) -> dict[str, int]:
    frequencies = Counter(tokens)
    counts = {}
    for fid, (_name, terms) in FEATURES.items():
        counts[fid] = sum(count for token, count in frequencies.items() if any(token == term or token.startswith(term) for term in terms))
    return counts


def generic_evidence(tokens: list[str], counts: dict[str, int]) -> dict[str, object]:
    evidence = {}
    for fid, (_name, terms) in FEATURES.items():
        loc = None
        for i, token in enumerate(tokens):
            if any(token == term or token.startswith(term) for term in terms):
                loc = {"token_index": i, "term": token}
                break
        evidence[fid] = loc
    return evidence


def ordered_signal(tokens: list[str]) -> dict[str, float | int]:
    pairs = (("because", "therefore"), ("if", "then"), ("however", "therefore"), ("for", "example"), ("first", "then"), ("before", "after"))
    right_to_left = defaultdict(set)
    for left, right in pairs:
        right_to_left[right].add(left)
    hits = 0
    window = deque(maxlen=60)
    for token in tokens:
        if token in right_to_left:
            hits += sum(left in window for left in right_to_left[token])
        window.append(token)
    block = 160
    overlaps = []
    for i in range(0, max(0, len(tokens) - block), block):
        a = set(t for t in tokens[i : i + block // 2] if t not in STOPWORDS and len(t) > 3)
        b = set(t for t in tokens[i + block // 2 : i + block] if t not in STOPWORDS and len(t) > 3)
        overlaps.append(len(a & b) / max(1, len(a | b)))
    return {"ordered_cue_pairs": hits, "adjacent_block_overlap_mean": round(sum(overlaps) / max(1, len(overlaps)), 8)}


def external_download_and_extract() -> list[dict[str, object]]:
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    access_rows = []
    manifests = []
    maps = []
    search_rows = []
    for q in read_json(PROTOCOL)["search_queries"]:  # type: ignore[index]
        search_rows.append({"query": q, "backend": "agent-reach-exa-or-official-catalog", "result_use": "candidate discovery ledger only", "answer_terms_used": False})
    for spec in SOURCES:
        raw_path = CACHE / f"{spec['work_id']}{'.pdf' if spec['kind'] == 'pdf' else '.txt'}"
        retrieval = download(raw_path, str(spec["source_url"]))
        access_rows.append({"work_id": spec["work_id"], "source_page": spec["source_page"], "source_url": spec["source_url"], "access_date": "2026-09-07", "retrieval": retrieval, "license_basis": spec["license_basis"], "eligible": retrieval.get("status") == "RETRIEVED", "exclusion_reason": None if retrieval.get("status") == "RETRIEVED" else "retrieval failure", "selection_order": len(access_rows) + 1})
        if retrieval.get("status") != "RETRIEVED":
            continue
        text_path = CACHE / f"{spec['work_id']}.normalized.txt"
        if text_path.exists() and text_path.stat().st_size > 0:
            text = text_path.read_text(encoding="utf-8")
            pages = len(PdfReader(str(raw_path)).pages) if spec["kind"] == "pdf" else None
            method = "cached-normalized-text"
        else:
            text, pages, method = extract_source(spec, raw_path)
            text_path.write_text(text, encoding="utf-8")
        tokens = tokenize(text)
        segments = segment_ranges(text, tokens, str(spec["kind"]))
        for seg in segments:
            maps.append({"work_id": spec["work_id"], **seg, "source_locator": f"{spec['source_url']}#{seg['label']}"})
        counts = feature_counts(tokens)
        manifests.append({"work_id": spec["work_id"], "title": spec["title"], "author": spec["author"], "year": spec["year"], "domain": spec["domain"], "publication_type": spec["publication_type"], "source_page": spec["source_page"], "source_url": spec["source_url"], "license_basis": spec["license_basis"], "kind": spec["kind"], "raw_file": str(raw_path), "raw_sha256": retrieval.get("sha256"), "raw_bytes": retrieval.get("bytes"), "normalized_text_sha256": file_digest(text_path), "word_count": len(tokens), "page_count": pages, "section_count": len(segments), "extraction_method": method, "meets_word_threshold": len(tokens) >= 25000, "meets_structure_threshold": len(segments) >= 4, "feature_counts": counts})
    write_jsonl(OUT / "source-access-ledger.jsonl", access_rows)
    write_jsonl(OUT / "source-manifest.jsonl", manifests)
    write_jsonl(OUT / "chapter-map.jsonl", maps)
    write_jsonl(OUT / "source-search-ledger.jsonl", search_rows)
    selected = [row for row in manifests if row["meets_word_threshold"] and row["meets_structure_threshold"]]
    selection = read_json(SELECTION)
    selection["manifest_digest_after_selection"] = digest(selected)
    selection["search_result_digest_after_selection"] = digest(search_rows)
    selection["selected_work_count"] = len(selected)
    selection["selected_word_count"] = sum(int(row["word_count"]) for row in selected)
    selection["selection_completed_at"] = "2026-09-07"
    write_json(SELECTION, selection)
    return selected


def external_split(manifests: list[dict[str, object]]) -> dict[str, object]:
    ordered = sorted(manifests, key=lambda row: hashlib.sha256(str(row["work_id"]).encode()).hexdigest())
    domains = sorted({str(row["domain"]) for row in ordered})
    holdout_n = max(1, round(len(ordered) * 0.25))
    holdout = []
    used = set()
    for domain in domains:
        candidates = [r for r in ordered if r["domain"] == domain and r["work_id"] not in used]
        if candidates and len(holdout) < holdout_n:
            holdout.append(candidates[0])
            used.add(candidates[0]["work_id"])
    for row in ordered:
        if len(holdout) >= holdout_n:
            break
        if row["work_id"] not in used:
            holdout.append(row)
            used.add(row["work_id"])
    holdout_ids = [str(row["work_id"]) for row in holdout]
    discovery_ids = [str(row["work_id"]) for row in ordered if row["work_id"] not in used]
    result = {"task_id": TASK, "split_rule": "hash-ordered source list, deterministic domain coverage then fill", "discovery_fraction_target": 0.75, "discovery_work_ids": discovery_ids, "holdout_work_ids": holdout_ids, "discovery_domains": sorted({str(r["domain"]) for r in ordered if r["work_id"] in discovery_ids}), "holdout_domains": sorted({str(r["domain"]) for r in ordered if r["work_id"] in holdout_ids}), "digest": digest({"discovery": discovery_ids, "holdout": holdout_ids})}
    write_json(OUT / "external-source-split.json", result)
    return result


def external_induction(manifests: list[dict[str, object]], split: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    discovery = set(split["discovery_work_ids"])
    for spec in manifests:
        text = (CACHE / f"{spec['work_id']}.normalized.txt").read_text(encoding="utf-8")
        tokens = tokenize(text)
        counts = feature_counts(tokens)
        evidence = generic_evidence(tokens, counts)
        rows.append({"work_id": spec["work_id"], "domain": spec["domain"], "split": "discovery" if spec["work_id"] in discovery else "holdout", "word_count": len(tokens), "anonymous_factors": [{"factor_id": f"EL-X{int(fid):02d}", "feature_key": fid, "observed_count": counts[fid], "density_per_10000_words": round(counts[fid] * 10000 / max(1, len(tokens)), 6), "evidence_locator": evidence[fid]} for fid in FEATURES], "ordered_signal": ordered_signal(tokens), "lineage": "independent per-work extraction before cross-work merge"})
    write_jsonl(OUT / "per-work-induction-results.jsonl", rows)
    return rows


def sentence_kind(sentence: str) -> str:
    lower = sentence.lower()
    if "?" in sentence:
        return "question"
    if re.search(r"\b(for example|e\.g\.|illustrat|instance)\b", lower):
        return "example"
    if re.search(r"\b(because|since|therefore|thus|hence|so that)\b", lower):
        return "reason"
    if re.search(r"\b(however|but|although|except|yet|nevertheless|revised|correction)\b", lower):
        return "qualification_or_revision"
    if re.search(r"\b(we show|we find|we conclude|it follows|the result is|in conclusion)\b", lower):
        return "claim"
    return "observation_or_definition"


def structured_longform_extraction(manifests: list[dict[str, object]]) -> None:
    """Keep a compact, ordered cross-block state rather than a summary bag."""
    section_rows = []
    manifest_rows = []
    for spec in manifests:
        text = (CACHE / f"{spec['work_id']}.normalized.txt").read_text(encoding="utf-8")
        tokens = tokenize(text)
        segments = segment_ranges(text, tokens, str(spec["kind"]))
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        kinds = [sentence_kind(s) for s in sentences]
        chain_count = sum(a == "claim" and b == "reason" or a == "reason" and b == "example" or a == "qualification_or_revision" and b == "claim" for a, b in zip(kinds, kinds[1:]))
        all_counts = feature_counts(tokens)
        section_term_sets = []
        for seg in segments:
            stokens = tokens[int(seg["start_word"]): int(seg["end_word"])]
            scounts = feature_counts(stokens)
            lower = " ".join(stokens)
            local_sentences = [s for s in re.split(r"(?<=[.!?])\s+", " ".join(stokens)) if s]
            section_term_sets.append(set(t for t in stokens if t not in STOPWORDS and len(t) > 4))
            section_rows.append({"work_id": spec["work_id"], "sequence": seg["sequence"], "label": seg["label"], "source_locator": f"{spec['source_url']}#{seg['label']}", "start_word": seg["start_word"], "end_word": seg["end_word"], "word_count": seg["word_count"], "feature_counts": scounts, "local_definition_count": sum(bool(re.search(r"\b(means|defined as|is called|we shall use|by .* we mean)\b", s.lower())) for s in local_sentences), "local_revision_count": sum(bool(re.search(r"\b(however|but|although|except|yet|revised|correction|instead)\b", s.lower())) for s in local_sentences), "local_question_count": sum("?" in s for s in local_sentences), "local_falsifier_count": sum(bool(re.search(r"\b(falsif|refut|disprov|unless|cannot|would fail|test)\b", s.lower())) for s in local_sentences), "top_terms": [t for t, _n in Counter(stokens).most_common(20) if t not in STOPWORDS and len(t) > 4][:10]})
        nonlocal_links = 0
        future_terms = set()
        next_terms = set()
        for terms in reversed(section_term_sets):
            nonlocal_links += len(terms & future_terms)
            future_terms |= next_terms
            next_terms = terms
        manifest_rows.append({"work_id": spec["work_id"], "order_preserved": True, "section_count": len(segments), "section_state_digest": digest([r for r in section_rows if r["work_id"] == spec["work_id"]]), "global_feature_counts": all_counts, "local_definition_count": sum(r["local_definition_count"] for r in section_rows if r["work_id"] == spec["work_id"]), "causal_or_constraint_edge_count": sum(bool(re.search(r"\b(because|therefore|thus|must|cannot|unless|constraint|rule)\b", s.lower())) and len(set(FEATURES) & set(fid for fid, n in feature_counts(tokenize(s)).items() if n)) >= 2 for s in sentences), "contradiction_revision_ledger_count": sum(bool(re.search(r"\b(however|but|although|except|yet|nevertheless|revised|correction)\b", s.lower())) for s in sentences), "question_count": sum("?" in s for s in sentences), "falsifier_count": sum(bool(re.search(r"\b(falsif|refut|disprov|unless|cannot|would fail|test)\b", s.lower())) for s in sentences), "cross_section_dependency_count": nonlocal_links, "claim_reason_example_counterexample_revision_chain_count": chain_count, "unresolved_premise_count": sum(bool(re.search(r"\b(if|assuming|provided|unless|depends on)\b", s.lower())) for s in sentences), "cross_block_state": "section propositions, unresolved premises, concept term sets, causal/constraint edges, revision ledger, and later question/falsifier counts are retained in ordered section rows"})
    write_jsonl(OUT / "longform-section-state.jsonl", section_rows)
    write_jsonl(OUT / "longform-extraction-manifest.jsonl", manifest_rows)


def candidate_freeze(rows: list[dict[str, object]], split: dict[str, object]) -> list[dict[str, object]]:
    discovery = [r for r in rows if r["split"] == "discovery"]
    counts = Counter()
    domains = defaultdict(set)
    densities = defaultdict(list)
    for row in discovery:
        for factor in row["anonymous_factors"]:
            if factor["observed_count"] >= 3:
                counts[factor["feature_key"]] += 1
                domains[factor["feature_key"]].add(row["domain"])
                densities[factor["feature_key"]].append(factor["density_per_10000_words"])
    eligible = [fid for fid in FEATURES if counts[fid] >= 4 and len(domains[fid]) >= 4]
    eligible.sort(key=lambda fid: (-counts[fid], fid))
    candidates = []
    for idx, fid in enumerate(eligible, 1):
        candidates.append({"candidate_id": f"EL-X{idx:02d}", "feature_key": fid, "anonymous_only": True, "discovery_work_recurrence": counts[fid], "discovery_domain_recurrence": len(domains[fid]), "density_threshold_per_10000_words": round(float(median(densities[fid])), 6), "selection_rule": "pre-frozen recurrence >=4 works and >=4 domains; no candidate vocabulary", "deletion_condition": "remove the feature extractor and the observed recurrence/transfer record disappears"})
    freeze = {"task_id": TASK, "status": "FROZEN", "frozen_after_per_work_results": True, "source_split_digest": split["digest"], "candidates": candidates, "candidate_digest": digest(candidates), "cognitive_independence": "not established; same Codex procedural separation only"}
    write_jsonl(OUT / "basis-free-candidate-freeze.jsonl", candidates)
    write_json(OUT / "basis-free-candidate-freeze.json", freeze)
    return candidates


def volume_ladder(rows: list[dict[str, object]], manifests: list[dict[str, object]], split: dict[str, object]) -> None:
    by_id = {r["work_id"]: r for r in rows}
    output = []
    for spec in manifests:
        tokens = tokenize((CACHE / f"{spec['work_id']}.normalized.txt").read_text(encoding="utf-8"))
        full_counts = feature_counts(tokens)
        full_present = {f"EL-X{int(fid):02d}" for fid, count in full_counts.items() if count >= 3}
        for fraction in (0.10, 0.25, 0.50, 0.75, 1.00):
            prefix = tokens[:max(1, round(len(tokens) * fraction))]
            counts = feature_counts(prefix)
            present = [f"EL-X{int(fid):02d}" for fid, count in counts.items() if count >= 3]
            output.append({"work_id": spec["work_id"], "split": by_id[spec["work_id"]]["split"], "fraction": fraction, "prefix_word_count": len(prefix), "factor_count": len(present), "present_anonymous_factors": present, "factor_stability_vs_full": round(len(set(present) & full_present) / max(1, len(full_present)), 6)})
    write_jsonl(OUT / "volume-ladder-results.jsonl", output)


def work_orders(manifests: list[dict[str, object]]) -> list[list[str]]:
    ids = [str(row["work_id"]) for row in manifests]
    return [
        sorted(ids, key=lambda x: hashlib.sha256(x.encode()).hexdigest()),
        sorted(ids, reverse=True),
        sorted(ids, key=lambda x: hashlib.sha256(("perm-3:" + x).encode()).hexdigest()),
    ]


def cross_book_accumulation(manifests: list[dict[str, object]]) -> None:
    all_features = {}
    for spec in manifests:
        tokens = tokenize((CACHE / f"{spec['work_id']}.normalized.txt").read_text(encoding="utf-8"))
        all_features[spec["work_id"]] = feature_counts(tokens)
    nodes = [1, 4, 8, 12, 16, 20]
    output = []
    for permutation_id, order in enumerate(work_orders(manifests), 1):
        for node in nodes:
            chosen = order[: min(node, len(order))]
            recurrence = {fid: sum(all_features[w][fid] >= 3 for w in chosen) for fid in FEATURES}
            stable = [f"EL-X{int(fid):02d}" for fid, n in recurrence.items() if n >= max(1, min(4, len(chosen)))]
            output.append({"permutation_id": permutation_id, "node": node, "available_work_count": len(chosen), "factor_recurrence": {f"EL-X{int(fid):02d}": n for fid, n in recurrence.items()}, "factor_stabilization_count": len(stable), "stable_anonymous_factors": stable})
    write_jsonl(OUT / "cross-book-accumulation-results.jsonl", output)


def shuffled_segments(tokens: list[str], segments: list[dict[str, object]], work_id: str, seed: str) -> list[str]:
    order = sorted(range(len(segments)), key=lambda i: hashlib.sha256(f"{seed}:{work_id}:{i}".encode()).hexdigest())
    return [token for idx in order for token in tokens[int(segments[idx]["start_word"]): int(segments[idx]["end_word"])] ]


def fragment_bag(tokens: list[str], work_id: str, seed: str) -> list[str]:
    size = 400
    fragments = [tokens[i : i + size] for i in range(0, len(tokens), size)]
    order = sorted(range(len(fragments)), key=lambda i: hashlib.sha256(f"fragment:{seed}:{work_id}:{i}".encode()).hexdigest())
    return [token for idx in order for token in fragments[idx]]


def coherence_metrics(tokens: list[str]) -> dict[str, object]:
    return {"token_count": len(tokens), "ordered_signal": ordered_signal(tokens), "sequence_digest": hashlib.sha256(canonical(tokens)).hexdigest()}


def coherence_ablation(manifests: list[dict[str, object]], split: dict[str, object]) -> None:
    output = []
    for spec in manifests:
        if spec["work_id"] not in set(split["discovery_work_ids"]):
            continue
        text = (CACHE / f"{spec['work_id']}.normalized.txt").read_text(encoding="utf-8")
        tokens = tokenize(text)
        segments = segment_ranges(text, tokens, str(spec["kind"]))
        variants = {"O_ORIGINAL_ORDER": tokens, "S_SEEDED_CHAPTER_SHUFFLE": shuffled_segments(tokens, segments, str(spec["work_id"]), "task162-seed-01"), "F_FRAGMENT_BAG": fragment_bag(tokens, str(spec["work_id"]), "task162-seed-01")}
        multiset_digest = hashlib.sha256(canonical(sorted(tokens))).hexdigest()
        for variant, stream in variants.items():
            metrics = coherence_metrics(stream)
            output.append({"work_id": spec["work_id"], "domain": spec["domain"], "variant": variant, "token_multiset_digest": multiset_digest, "same_token_count_as_original": len(stream) == len(tokens), "metrics": metrics, "segment_count_original": len(segments)})
    write_jsonl(OUT / "coherence-ablation-results.jsonl", output)


def holdout_and_v2(rows: list[dict[str, object]], candidates: list[dict[str, object]]) -> None:
    by_feature = {c["feature_key"]: c for c in candidates}
    holdout = []
    for row in rows:
        if row["split"] != "holdout":
            continue
        factors = {f["feature_key"]: f for f in row["anonymous_factors"]}
        for c in candidates:
            f = factors[c["feature_key"]]
            holdout.append({"work_id": row["work_id"], "domain": row["domain"], "candidate_id": c["candidate_id"], "feature_key": c["feature_key"], "predicted_by_discovery_threshold": f["density_per_10000_words"] >= c["density_threshold_per_10000_words"], "observed_density_per_10000_words": f["density_per_10000_words"], "threshold": c["density_threshold_per_10000_words"]})
    write_jsonl(OUT / "external-holdout-results.jsonl", holdout)
    scores = []
    for c in candidates:
        h = [r for r in holdout if r["candidate_id"] == c["candidate_id"]]
        scores.append({"candidate_id": c["candidate_id"], "heldout_work_count": len(h), "heldout_domain_count": len({r["domain"] for r in h}), "heldout_positive_count": sum(bool(r["predicted_by_discovery_threshold"]) for r in h), "v2": {"L1": "NOT_ADJUDICATED", "L2": "NOT_ESTABLISHED", "L3": "NOT_ESTABLISHED", "L4": "NOT_ESTABLISHED", "L5": "SUPPORTIVE_ONLY", "L6": "NOT_ESTABLISHED"}, "status": "UNDERDETERMINED"})
    write_jsonl(OUT / "external-v2-scores.jsonl", scores)


def source_track() -> None:
    manifests = external_download_and_extract()
    split = external_split(manifests)
    rows = external_induction(manifests, split)
    structured_longform_extraction(manifests)
    candidates = candidate_freeze(rows, split)
    volume_ladder(rows, manifests, split)
    cross_book_accumulation(manifests)
    coherence_ablation(manifests, split)
    holdout_and_v2(rows, candidates)
    write_json(OUT / "external-track-summary.json", {"task_id": TASK, "eligible_work_count": len(manifests), "eligible_words": sum(int(x["word_count"]) for x in manifests), "eligible_domains": sorted({str(x["domain"]) for x in manifests}), "book_monograph_or_thesis_scale_count": sum(str(x["publication_type"]) in {"public_domain_book", "public_domain_monograph", "open_textbook"} for x in manifests), "candidate_count": len(candidates), "source_split_digest": split["digest"], "status": "EXTERNAL_TRACK_FROZEN"})


def redact(text: str) -> tuple[str, list[str]]:
    found = sorted(set(m.group(0) for m in LEAK_RE.finditer(text)))
    return LEAK_RE.sub("[REDACTED_SOURCE_TERM]", text), found


def source_blob_text(sha: str) -> str:
    p = subprocess.run(["git", "cat-file", "-p", sha], cwd=REPO, capture_output=True)
    return p.stdout.decode("utf-8", errors="replace") if p.returncode == 0 else ""


def path_history(path: str) -> list[dict[str, str]]:
    raw = git_text("log", "--all", "--format=%H%x09%ad%x09%s", "--date=short", "--follow", "--", path)
    rows = []
    for line in raw.splitlines()[:16]:
        parts = line.split("\t", 2)
        if len(parts) == 3:
            rows.append({"commit_sha": parts[0], "date": parts[1], "message": parts[2]})
    return rows


def packet_facts(text: str, history: list[dict[str, str]]) -> dict[str, object]:
    lower = (text + " " + " ".join(h["message"] for h in history)).lower()
    return {
        "endpoint_properties_observed": any(x in lower for x in ("field", "value", "schema", "property", "valid")),
        "unordered_pair_observed": any(x in lower for x in ("pair", "before and after", "source and target")),
        "ordered_intermediate_events_observed": any(x in lower for x in ("before", "after", "sequence", "order", "step", "stage", "replay")),
        "cross_object_identity_or_binding_observed": any(x in lower for x in ("identity", "binding", "same object", "specific object", "owner")),
        "authorization_or_evidence_binding_observed": any(x in lower for x in ("approval", "authorize", "evidence", "attestation", "claim")),
        "rollback_or_inverse_link_observed": any(x in lower for x in ("rollback", "revert", "reverse", "restore", "undo")),
        "epoch_staleness_or_lifecycle_observed": any(x in lower for x in ("epoch", "stale", "lifecycle", "version", "current")),
        "other_nonlocal_fact_observed": any(x in lower for x in ("cross", "dependency", "reconcile", "propagat", "global", "concurrency")),
    }


def neutral_taxonomy(facts: dict[str, object]) -> list[str]:
    values = []
    if facts["endpoint_properties_observed"]: values.append("A_ENDPOINT_PROPERTIES_ONLY")
    if facts["unordered_pair_observed"]: values.append("B_UNORDERED_ENDPOINT_PAIR")
    if facts["ordered_intermediate_events_observed"]: values.append("C_ORDERED_INTERMEDIATE_EVENTS_REQUIRED")
    if facts["cross_object_identity_or_binding_observed"]: values.append("D_CROSS_OBJECT_IDENTITY_OR_BINDING_REQUIRED")
    if facts["authorization_or_evidence_binding_observed"]: values.append("E_AUTHORIZATION_OR_EVIDENCE_TO_SPECIFIC_CHANGE_REQUIRED")
    if facts["rollback_or_inverse_link_observed"]: values.append("F_ROLLBACK_OR_INVERSE_LINK_REQUIRED")
    if facts["epoch_staleness_or_lifecycle_observed"]: values.append("G_EPOCH_STALENESS_OR_LIFECYCLE_LINK_REQUIRED")
    if facts["other_nonlocal_fact_observed"]: values.append("H_OTHER_NONLOCAL_FACT_REQUIRED")
    return values or ["U_INSUFFICIENT_EVIDENCE"]


def build_history_packets() -> None:
    residuals = read_jsonl(TASK160 / "representation-residuals.jsonl")
    universe = read_jsonl(TASK160 / "corpus-universe.jsonl")
    by_id = {str(row["item_id"]): row for row in universe}
    residuals = sorted(residuals, key=lambda r: digest(r))
    controls = sorted([r for r in universe if r.get("family") == "C7_ENGINEERING_NEGATIVE_CONTROL"], key=lambda r: digest(r))
    selected = []
    seen = set()
    for row in residuals:
        item = str(row["item_id"])
        if item not in seen and item in by_id:
            selected.append(("residual_lead", by_id[item], row))
            seen.add(item)
        if len([x for x in selected if x[0] == "residual_lead"]) >= 240:
            break
    for row in controls:
        item = str(row["item_id"])
        if item not in seen:
            selected.append(("control_lead", row, None))
            seen.add(item)
        if len([x for x in selected if x[0] == "control_lead"]) >= 160:
            break
    packets = []
    manifest_rows = []
    for idx, (origin, row, residual) in enumerate(selected, 1):
        blob = str(row.get("source_blob_sha", ""))
        path = str(row.get("source_path", ""))
        text = source_blob_text(blob) if blob else ""
        history = path_history(path) if path else []
        redacted, leaks = redact(text[:900])
        packet_id = f"HP-{idx:04d}"
        facts = packet_facts(text, history)
        packet = {"packet_id": packet_id, "source": {"path": path, "blob_sha": blob, "content_sha256": hashlib.sha256(text.encode()).hexdigest(), "source_blob_available": bool(text)}, "history_evidence": {"observed_commit_shas": [h["commit_sha"] for h in history], "observed_commit_messages": [redact(h["message"])[0] for h in history], "explicit_failure_evidence": any(x in (text + " " + " ".join(h["message"] for h in history)).lower() for x in ("failed", "failure", "falsif", "drift", "out-of-date", "rejected", "rollback")), "explicit_success_evidence": any(x in (text + " " + " ".join(h["message"] for h in history)).lower() for x in ("passed", "success", "validated", "accepted", "complete", "no regressions")), "correction_followup_observed": any(x in " ".join(h["message"] for h in history).lower() for x in ("fix", "repair", "correct", "revert", "refresh", "address"))}, "neutral_facts": facts, "minimal_facts_taxonomy_candidates": neutral_taxonomy(facts), "sanitized_evidence_excerpt": redacted, "source_term_leakage_redacted": bool(leaks)}
        packets.append(packet)
        manifest_rows.append({"packet_id": packet_id, "item_id": row.get("item_id"), "origin": origin, "corpus_family_hidden_from_packet": row.get("family") or row.get("corpus_family"), "time_slice": row.get("time_slice"), "source_path": path, "source_blob_sha": blob, "leakage_terms_observed": leaks, "history_commit_count_observed": len(history)})
    write_jsonl(OUT / "sanitized-history-packets.jsonl", packets)
    write_jsonl(OUT / "historical-universe.jsonl", manifest_rows)
    write_json(OUT / "historical-sample-manifest.json", {"task_id": TASK, "residual_lead_target": 240, "residual_lead_selected": sum(r["origin"] == "residual_lead" for r in manifest_rows), "control_target": 160, "control_selected": sum(r["origin"] == "control_lead" for r in manifest_rows), "total_selected": len(manifest_rows), "families_in_hidden_manifest": sorted({str(r["corpus_family_hidden_from_packet"]) for r in manifest_rows}), "time_slices": sorted({str(r["time_slice"]) for r in manifest_rows}), "packet_digest": file_digest(OUT / "sanitized-history-packets.jsonl"), "manifest_digest": file_digest(OUT / "historical-universe.jsonl"), "candidate_labels_not_in_packets": True, "task161_answer_key_not_loaded": True})


def adjudicate_packet(packet: dict[str, object], variant: str) -> dict[str, object]:
    evidence = packet["history_evidence"]
    defect = bool(evidence["explicit_failure_evidence"] and evidence["correction_followup_observed"])
    clean = bool(evidence["explicit_success_evidence"] and not evidence["explicit_failure_evidence"] and not evidence["correction_followup_observed"])
    if defect:
        label = "CONFIRMED_DEFECT"
    elif clean:
        label = "CONFIRMED_CLEAN" if variant == "pass-1" else "STRONG_NEGATIVE"
    else:
        label = "UNDECIDABLE"
    return {"packet_id": packet["packet_id"], "label": label, "minimal_facts": packet["minimal_facts_taxonomy_candidates"], "reason_codes": {"failure_and_followup": defect, "positive_clean_evidence": clean, "variant": variant}}


def history_pass(pass_name: str) -> None:
    packets = read_jsonl(OUT / "sanitized-history-packets.jsonl")
    rows = [adjudicate_packet(p, pass_name) for p in packets]
    write_jsonl(OUT / f"adjudication-{pass_name}.jsonl", rows)


def reconcile_history() -> None:
    p1 = {r["packet_id"]: r for r in read_jsonl(OUT / "adjudication-pass-1.jsonl")}
    p2 = {r["packet_id"]: r for r in read_jsonl(OUT / "adjudication-pass-2.jsonl")}
    final, disagreements, facts = [], [], []
    for packet_id in sorted(p1):
        a, b = p1[packet_id], p2[packet_id]
        if a["label"] == b["label"]:
            label = a["label"]
        elif {a["label"], b["label"]} <= {"CONFIRMED_CLEAN", "STRONG_NEGATIVE"}:
            label = "STRONG_NEGATIVE"
        else:
            label = "UNDECIDABLE"
        if a["label"] != b["label"]:
            disagreements.append({"packet_id": packet_id, "pass_1": a["label"], "pass_2": b["label"], "resolution": label})
        final.append({"packet_id": packet_id, "final_label": label, "pass_1_label": a["label"], "pass_2_label": b["label"], "minimal_facts": sorted(set(a["minimal_facts"]) | set(b["minimal_facts"]))})
        for fact in final[-1]["minimal_facts"]:
            facts.append({"packet_id": packet_id, "final_label": label, "minimal_fact": fact})
    write_jsonl(OUT / "adjudication-disagreement-ledger.jsonl", disagreements)
    write_jsonl(OUT / "historical-final-labels.jsonl", final)
    write_jsonl(OUT / "minimal-facts-taxonomy-results.jsonl", facts)
    write_json(OUT / "history-adjudication-freeze.json", {"task_id": TASK, "status": "FROZEN", "packets_digest": file_digest(OUT / "sanitized-history-packets.jsonl"), "pass_1_digest": file_digest(OUT / "adjudication-pass-1.jsonl"), "pass_2_digest": file_digest(OUT / "adjudication-pass-2.jsonl"), "disagreement_digest": file_digest(OUT / "adjudication-disagreement-ledger.jsonl"), "final_label_digest": file_digest(OUT / "historical-final-labels.jsonl"), "procedural_status": "PROCEDURAL_SEPARATION_ONLY / NOT_COGNITIVE_INDEPENDENCE", "task161_models_loaded": False})


def history_model_score() -> None:
    labels = read_jsonl(OUT / "historical-final-labels.jsonl")
    model_path = TASK161 / "model-definitions.json"
    model_digest = file_digest(model_path)
    ms = {"A_ENDPOINT_PROPERTIES_ONLY", "B_UNORDERED_ENDPOINT_PAIR"}
    mt = ms | {"C_ORDERED_INTERMEDIATE_EVENTS_REQUIRED", "D_CROSS_OBJECT_IDENTITY_OR_BINDING_REQUIRED", "E_AUTHORIZATION_OR_EVIDENCE_TO_SPECIFIC_CHANGE_REQUIRED", "F_ROLLBACK_OR_INVERSE_LINK_REQUIRED", "G_EPOCH_STALENESS_OR_LIFECYCLE_LINK_REQUIRED", "H_OTHER_NONLOCAL_FACT_REQUIRED"}
    predictions = []
    for row in labels:
        facts = set(row["minimal_facts"])
        predictions.append({"packet_id": row["packet_id"], "observed_label": row["final_label"], "MS_predicts_defect": bool(facts & ms), "MT_predicts_defect": bool(facts & mt), "same_neutral_facts": True})
    def metrics(key: str) -> dict[str, int | float]:
        tp = sum(r[key] and r["observed_label"] == "CONFIRMED_DEFECT" for r in predictions)
        fp = sum(r[key] and r["observed_label"] in {"CONFIRMED_CLEAN", "STRONG_NEGATIVE"} for r in predictions)
        fn = sum((not r[key]) and r["observed_label"] == "CONFIRMED_DEFECT" for r in predictions)
        tn = sum((not r[key]) and r["observed_label"] in {"CONFIRMED_CLEAN", "STRONG_NEGATIVE"} for r in predictions)
        return {"TP": tp, "FP": fp, "FN": fn, "TN": tn, "precision": round(tp / max(1, tp + fp), 6), "recall": round(tp / max(1, tp + fn), 6)}
    write_jsonl(OUT / "historical-ms-mt-scores.jsonl", [{"model": "MS", **metrics("MS_predicts_defect")}, {"model": "MT", **metrics("MT_predicts_defect")}])
    write_json(OUT / "history-model-adapter-freeze.json", {"task_id": TASK, "loaded_after_history_label_freeze": True, "task161_model_definitions_sha256": model_digest, "models": {"MS": "M0 plus A/B neutral facts", "MT": "M0 plus the exact same neutral facts A-H; no MT-only facts"}, "no_parameter_change": True, "same_facts_hard_constraint": True})
    write_json(OUT / "historical-score-summary.json", {"task_id": TASK, "final_label_counts": dict(Counter(r["final_label"] for r in labels)), "confirmed_defect_count": sum(r["final_label"] == "CONFIRMED_DEFECT" for r in labels), "confirmed_clean_or_negative_count": sum(r["final_label"] in {"CONFIRMED_CLEAN", "STRONG_NEGATIVE"} for r in labels), "undecidable_count": sum(r["final_label"] == "UNDECIDABLE" for r in labels), "score_file": "historical-ms-mt-scores.jsonl", "epistemic_status": "HISTORICAL_UNDERDETERMINED unless all command thresholds are met"})


def convergence() -> None:
    ext = read_json(OUT / "external-track-summary.json")
    hist = read_json(OUT / "historical-score-summary.json")
    v2 = read_jsonl(OUT / "external-v2-scores.jsonl")
    crosswalk = []
    for c in read_jsonl(OUT / "basis-free-candidate-freeze.jsonl"):
        crosswalk.append({"candidate_id": c["candidate_id"], "external_feature_key": c["feature_key"], "existing_basis_crosswalk": "UNBLINDED_AFTER_EXTERNAL_FREEZE: generic ordered/causal/constraint/etc feature; conservative local compilation not adjudicated", "historical_taxonomy_crosswalk": "comparison only; not an identity claim", "same_lost_question": False, "semantic_leap_status": "NOT_ESTABLISHED"})
    write_jsonl(OUT / "existing-basis-crosswalk.jsonl", crosswalk)
    write_jsonl(OUT / "cross-source-convergence.jsonl", [{"track_a_frozen": True, "track_b_frozen": True, "candidate_crosswalks": len(crosswalk), "convergence": "NO_INDEPENDENT_CONVERGENCE_ESTABLISHED", "reason": "external factors are anonymous lexical/argument summaries and history passes are procedural only; no cognitive independence or independent adjudication", "source_independence": "external public corpus and repository history are separate source channels"}])
    write_jsonl(OUT / "candidate-ablation-results.jsonl", [{"candidate_id": c["candidate_id"], "deletion_test": "NOT_RUN_AS_CANONICAL_CHANGE", "research_deletion_observation": "feature extraction count becomes unavailable when the feature is removed", "semantic_capability_loss_independently_adjudicated": False} for c in crosswalk])
    write_jsonl(OUT / "candidate-deletion-conditions.jsonl", [{"candidate_id": c["candidate_id"], "deletion_condition": "remove generic feature extractor and rerun exact frozen corpus", "pass": False, "reason": "deletion is a method sensitivity observation, not V2 semantic capability proof"} for c in crosswalk])
    v2_final = {"task_id": TASK, "task159_v2_signature_reused_exactly": True, "candidate_count": len(v2), "all_candidates_pass_v2": False, "status": "UNDERDETERMINED", "reason": "no candidate has independently established L2/L3/L4/L6; no cognitive independence; no canonical validation"}
    write_json(OUT / "v2-final-gate.json", v2_final)
    history_labels = hist["final_label_counts"]
    historical_thresholds = {"confirmed_defects_at_least_40": hist["confirmed_defect_count"] >= 40, "clean_or_negative_at_least_80": hist["confirmed_clean_or_negative_count"] >= 80, "procedural_cognitive_independence": False, "four_families_mt_increment": False}
    coherence_rows = read_jsonl(OUT / "coherence-ablation-results.jsonl")
    by_work_variant = {(r["work_id"], r["variant"]): r for r in coherence_rows}
    paired = []
    for work_id in {r["work_id"] for r in coherence_rows}:
        original = by_work_variant.get((work_id, "O_ORIGINAL_ORDER"))
        shuffled = by_work_variant.get((work_id, "S_SEEDED_CHAPTER_SHUFFLE"))
        fragments = by_work_variant.get((work_id, "F_FRAGMENT_BAG"))
        if original and shuffled and fragments:
            om = original["metrics"]["ordered_signal"]["ordered_cue_pairs"]
            sm = shuffled["metrics"]["ordered_signal"]["ordered_cue_pairs"]
            fm = fragments["metrics"]["ordered_signal"]["ordered_cue_pairs"]
            paired.append({"work_id": work_id, "original_beats_both": om > sm and om > fm, "original_ordered_cue_pairs": om, "shuffle_ordered_cue_pairs": sm, "fragment_ordered_cue_pairs": fm})
    coherence_rate = sum(bool(x["original_beats_both"]) for x in paired) / max(1, len(paired))
    coherence_support = bool(paired) and coherence_rate >= 0.60
    ladder = read_jsonl(OUT / "volume-ladder-results.jsonl")
    ladder_means = {fraction: round(sum(int(r["factor_count"]) for r in ladder if r["fraction"] == fraction) / max(1, sum(1 for r in ladder if r["fraction"] == fraction)), 6) for fraction in (0.10, 0.25, 0.50, 0.75, 1.00)}
    volume_support = ladder_means[1.00] > ladder_means[0.10]
    if ext["eligible_words"] < 500000 or len(ext["eligible_domains"]) < 6:
        input_verdict = "LONGFORM_INPUT_EFFECT_UNDERDETERMINED"
    elif coherence_support and volume_support:
        input_verdict = "VOLUME_AND_COHERENCE_EFFECT_SUPPORTED_AS_RESEARCH_FINDING"
    elif volume_support:
        input_verdict = "INFORMATION_VOLUME_EFFECT_ONLY"
    elif coherence_support:
        input_verdict = "LOGICAL_COHERENCE_EFFECT_ONLY"
    else:
        input_verdict = "NO_DETECTABLE_LONGFORM_ADVANTAGE"
    verdict = {"task_id": TASK, "input_regime_verdict": input_verdict, "historical_verdict": "HISTORICAL_UNDERDETERMINED", "basis_semantic_verdict": "NO_BASIS_ESCAPE_DETECTED", "epistemic_status": "DETECTOR_NOT_VALIDATED / UNDERDETERMINED", "research_only": True, "ready": False, "draft_only": True, "external_truth_claim": False, "owner_acceptance": False, "task161_inherited_foundation_drift": "INHERITED_CI_RESIDUAL_RECORDED_SEPARATELY", "counts": {"external_words": ext["eligible_words"], "external_works": ext["eligible_work_count"], "external_domains": len(ext["eligible_domains"]), "history_labels": history_labels}, "historical_thresholds": historical_thresholds, "residuals": ["PROCEDURAL_SEPARATION_ONLY / NOT_COGNITIVE_INDEPENDENCE", "lexical/argument feature extraction is not independent semantic adjudication", "historical sample labels depend on explicit repository text markers and are not human adjudication", "canonical validation and remote Task162 CI not yet observed", "instructions/CURRENT.md and relay/current missing"], "final_answers": {"owner_book_hypothesis": input_verdict, "coherence_pair_count": len(paired), "coherence_original_beats_both_rate": round(coherence_rate, 6), "volume_ladder_factor_means": ladder_means, "next_semantic_leap": "no evidence of a validated next semantic leap"}}
    write_json(OUT / "verdict.json", verdict)
    write_json(OUT / "freeze-ledger.json", {"task_id": TASK, "command_source": {"repository": "Arvin-liu/1111", "path": "agent-commands/IGNITION-20260907-162.md", "commit": "8ab1aac0cdedd4874c798f4593614335cdd79e76", "blob": "df58765e5c21cf3b0aba15f804ce461b4b1c542e", "content_sha256": "e4e61e12ca3798b72b714c0fc2e9cf1ec0b1224529dee138c9740a0fc2b4b65a"}, "formal_base": {"ref": "work/IGNITION-20260907-161", "sha": "5ccb15d45cec259d5397f1843278fd98011105aa"}, "formal_pr_preflight": {"repository": "Arvin-liu/when-systems-catch-fire", "number": 211, "state": "open", "draft": True, "head": "5ccb15d45cec259d5397f1843278fd98011105aa", "base": "work/IGNITION-20260907-160"}, "control_pointers": {"instructions/CURRENT.md": "missing; preserve and record STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL", "relay/current": "missing; preserve and record STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL"}, "hypotheses_frozen_before_source_discovery": True, "source_selection_frozen_before_source_discovery": True, "external_track_frozen": True, "history_track_frozen": True, "task161_answer_key_loaded_only_after_history_freeze": True, "forbidden_actions_taken": [], "status": "RESEARCH_ONLY_DRAFT_PENDING"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("external", "history-packets", "history-pass-1", "history-pass-2", "history-reconcile", "history-score", "convergence", "all"), default="all")
    args = parser.parse_args()
    if args.phase in {"external", "all"}:
        source_track()
    if args.phase in {"history-packets", "all"}:
        build_history_packets()
    if args.phase in {"history-pass-1", "all"}:
        history_pass("pass-1")
    if args.phase in {"history-pass-2", "all"}:
        history_pass("pass-2")
    if args.phase in {"history-reconcile", "all"}:
        reconcile_history()
    if args.phase in {"history-score", "all"}:
        history_model_score()
    if args.phase in {"convergence", "all"}:
        convergence()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
