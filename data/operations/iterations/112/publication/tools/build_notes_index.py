#!/usr/bin/env python3
"""Build the machine-readable index for the published first notes volume.

The index is derived from the rendered Markdown headings and the fixed five-field
note contract. It deliberately does not infer scientific validity from titles.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
NOTES = ROOT / "PUBLICATIONS/notes/001-pointfire-research-notes.md"
INDEX = ROOT / "PUBLICATIONS/notes/index.jsonl"


def main() -> None:
    text = NOTES.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^### (N\d{2})｜(.+)$", text, flags=re.MULTILINE))
    if not matches:
        raise SystemExit("no note headings found")

    records: list[dict[str, object]] = []
    for number, match in enumerate(matches):
        start = match.end()
        end = matches[number + 1].start() if number + 1 < len(matches) else len(text)
        block = text[start:end]
        section_matches = list(re.finditer(r"^## (.+)$", text[: match.start()], flags=re.MULTILINE))
        theme = section_matches[-1].group(1).strip() if section_matches else "theme_unresolved"
        fields = {}
        for field in ("问题", "核心认识", "证据或来源", "边界", "尚未解决"):
            field_match = re.search(rf"^\*\*{field}：\*\*\s*(.+)$", block, flags=re.MULTILINE)
            if not field_match:
                raise SystemExit(f"{match.group(1)} missing field: {field}")
            fields[field] = field_match.group(1).strip()
        records.append(
            {
                "note_id": match.group(1),
                "title": match.group(2).strip(),
                "theme": theme,
                "question": fields["问题"],
                "core_insight": fields["核心认识"],
                "evidence": fields["证据或来源"],
                "boundary": fields["边界"],
                "open_question": fields["尚未解决"],
                "source_volume": "PUBLICATIONS/notes/001-pointfire-research-notes.md",
                "status": "PUBLISHED_WITH_EXPLICIT_LIMITATIONS",
                "claim_ceiling": "仅支持声明来源、版本、范围和证据类型内的窄结论；不抬高为外部真理。",
            }
        )

    if len(records) < 60:
        raise SystemExit(f"expected at least 60 notes, found {len(records)}")
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    with INDEX.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"wrote {len(records)} note records to {INDEX}")


if __name__ == "__main__":
    main()
