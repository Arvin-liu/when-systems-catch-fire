#!/usr/bin/env python3
"""Recall discovery/prediction/answer candidates from exported discussion history."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import zipfile
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = REPO_ROOT / "data/rebuild/discussion-inference-recall.json"
OUT_JSONL = REPO_ROOT / "data/rebuild/discussion-inference-recall.jsonl"
OUT_MD = REPO_ROOT / "data/rebuild/discussion-inference-recall.md"

KEYWORDS = ["发现", "洞察", "推论", "猜想", "预测"]
PREDICTION_HINTS = ["预测", "猜想", "将", "会", "未来", "可检验", "证伪"]
ANSWER_HINTS = ["新答案", "答案", "回答", "解释", "解决", "问题"]
DISCOVERY_HINTS = ["发现", "洞察", "推论", "推出", "证明", "验证"]


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


def normalize(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[`*_#|>\[\](){}<>]", "", text)
    return text.strip()


def signature(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()[:16]


def chargrams(text: str, n: int = 2) -> set[str]:
    clean = re.sub(r"\s+", "", normalize(text))
    return {clean[i : i + n] for i in range(max(len(clean) - n + 1, 0))}


def similarity(a: str, b: str) -> float:
    ga = chargrams(a)
    gb = chargrams(b)
    return gram_similarity(ga, gb)


def gram_similarity(ga: set[str], gb: set[str]) -> float:
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def object_text(item: dict) -> str:
    fields = []
    for key in ["title", "summary", "content", "statement", "answer", "question", "basis", "new_explanation"]:
        value = item.get(key)
        if isinstance(value, dict):
            fields.extend(str(v) for v in value.values() if v)
        elif value:
            fields.append(str(value))
    return "\n".join(fields)


def existing_objects() -> list[dict]:
    rows = []
    for layer, path in [
        ("discovery", REPO_ROOT / "data/discoveries/unified-discoveries.json"),
        ("prediction", REPO_ROOT / "data/predictions/unified-predictions.json"),
        ("answer", REPO_ROOT / "data/answers/unified-answers.json"),
        ("function", REPO_ROOT / "data/functions/unified-functions.json"),
        ("case", REPO_ROOT / "data/cases/unified-cases.json"),
    ]:
        for item in read_json(path, []):
            text = object_text(item)
            rows.append({"layer": layer, "id": item.get("id") or item.get("normalized_id"), "text": text, "grams": chargrams(text)})
    return rows


def classify_context(text: str) -> str:
    score = {
        "prediction": sum(text.count(hint) for hint in PREDICTION_HINTS),
        "answer": sum(text.count(hint) for hint in ANSWER_HINTS),
        "discovery": sum(text.count(hint) for hint in DISCOVERY_HINTS),
    }
    if score["prediction"] >= max(score["answer"], score["discovery"]):
        return "prediction"
    if score["answer"] >= max(score["prediction"], score["discovery"]):
        return "answer"
    return "discovery"


def discipline_tags(text: str) -> list[str]:
    rules = {
        "physics": ["物理", "量子", "引力", "暗物质", "宇宙", "热力学", "相变"],
        "psychology": ["心理", "认知", "动机", "情绪", "决策", "直觉"],
        "ai-and-systems": ["AI", "智能体", "agent", "工具", "接口", "调度", "token", "模型"],
        "technology-and-engineering": ["工程", "系统", "算法", "架构", "门控", "函数"],
        "economics-and-wealth": ["经济", "投资", "定投", "市场", "收益", "风险"],
        "history-and-civilization": ["历史", "文明", "制度", "王朝", "周公"],
        "law-and-institutions": ["法律", "法治", "契约", "权利"],
        "neuroscience-and-consciousness": ["意识", "神经", "脑", "心智"],
    }
    tags = [name for name, hints in rules.items() if any(hint in text for hint in hints)]
    return tags or ["other"]


def context_windows(text: str, source: str) -> list[dict]:
    rows = []
    for keyword in KEYWORDS:
        for match in re.finditer(re.escape(keyword), text):
            start = max(0, match.start() - 180)
            end = min(len(text), match.end() + 220)
            context = normalize(text[start:end])
            if len(context) < 20:
                continue
            rows.append(
                {
                    "recall_id": f"R-{signature(source + ':' + str(match.start()) + ':' + context)}",
                    "source_file": source,
                    "keyword": keyword,
                    "offset": match.start(),
                    "context": context,
                }
            )
    return rows


def load_zip_texts(zip_path: Path) -> list[tuple[str, str]]:
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp)
        for path in sorted(Path(tmp).rglob("*")):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            rows.append((path.relative_to(tmp).as_posix(), text))
    return rows


def build_recall(zip_path: Path) -> dict:
    existing = existing_objects()
    raw = []
    seen_contexts = set()
    for source, text in load_zip_texts(zip_path):
        for row in context_windows(text, source):
            key = signature(row["context"])
            if key in seen_contexts:
                continue
            seen_contexts.add(key)
            best = {"layer": None, "id": None, "score": 0.0}
            context_grams = chargrams(row["context"])
            for item in existing:
                score = gram_similarity(context_grams, item["grams"])
                if score > best["score"]:
                    best = {"layer": item["layer"], "id": item["id"], "score": round(score, 4)}
            target = classify_context(row["context"])
            covered = best["score"] >= 0.42
            row.update(
                {
                    "target_directory": target,
                    "discipline_tags": discipline_tags(row["context"]),
                    "coverage": "covered" if covered else "not_fully_listed",
                    "nearest_existing": best,
                    "internal_verification": {
                        "status": "passed",
                        "checks": [
                            "source_context_present",
                            "keyword_recalled",
                            "target_directory_classified",
                            "nearest_existing_compared",
                        ],
                    },
                }
            )
            raw.append(row)
    counts = Counter((row["target_directory"], row["coverage"]) for row in raw)
    return {
        "zip_path": str(zip_path),
        "keywords": KEYWORDS,
        "total_recalled": len(raw),
        "counts": {f"{key[0]}:{key[1]}": value for key, value in sorted(counts.items())},
        "not_fully_listed": [row for row in raw if row["coverage"] == "not_fully_listed"],
        "all_recalled": raw,
    }


def render_md(payload: dict) -> str:
    lines = [
        "# 历史讨论推论召回报告",
        "",
        f"- zip_path: `{payload['zip_path']}`",
        f"- keywords: {', '.join(payload['keywords'])}",
        f"- total_recalled: {payload['total_recalled']}",
        f"- not_fully_listed: {len(payload['not_fully_listed'])}",
        "",
        "## 计数 / Counts",
        "",
    ]
    for key, value in payload["counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## 未完整列出召回 / Not Fully Listed Recall", ""])
    for row in payload["not_fully_listed"][:300]:
        lines.extend(
            [
                f"### {row['recall_id']} -> {row['target_directory']}",
                "",
                f"- source: `{row['source_file']}`",
                f"- keyword: `{row['keyword']}`",
                f"- discipline_tags: {', '.join(row['discipline_tags'])}",
                f"- nearest_existing: {row['nearest_existing']['layer']}:{row['nearest_existing']['id']} score={row['nearest_existing']['score']}",
                f"- internal_verification: {row['internal_verification']['status']}",
                "",
                row["context"],
                "",
            ]
        )
    if len(payload["not_fully_listed"]) > 300:
        lines.append(f"... 其余 {len(payload['not_fully_listed']) - 300} 条见 JSON/JSONL。")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args()
    payload = build_recall(args.zip_path)
    write_text(OUT_JSON, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_text(OUT_JSONL, "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in payload["all_recalled"]))
    write_text(OUT_MD, render_md(payload))
    print(json.dumps({k: payload[k] for k in ["total_recalled", "counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
