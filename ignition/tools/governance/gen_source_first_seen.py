#!/usr/bin/env python3
"""Generate the governed ``source-first-seen.json`` map.

This map records, for every result source referenced by the human-results
ledger, the date that source *first appears* in repository history
(``git log --follow --diff-filter=A``). It is computed ONCE from a FULL
clone and committed as governed data so that
``build_knowledge_experience.py`` no longer needs to shell out to git at
generation time. That removes the clone-depth dependence that previously
made a shallow clone emit ``snapshot`` dates while a full clone emitted the
real first-appearance dates (see task 102, pass 3).

Formal generation of this map REQUIRES full git history. On a shallow clone
this script refuses, because ``git log`` would be incomplete and would
produce wrong dates.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "data/governance/human-results/result-ledger.jsonl"
OUT = ROOT / "data/governance/knowledge-experience/source-first-seen.json"
DATE_RE = re.compile(r"20\d{2}-\d{2}-\d{2}")


def require_full_history() -> None:
    if (ROOT / ".git").is_dir():
        proc = subprocess.run(
            ["git", "rev-parse", "--is-shallow-repository"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.stdout.strip() == "true":
            sys.exit(
                "REFUSE: source-first-seen.json must be generated from a FULL clone. "
                "Run `git fetch --unshallow` first."
            )


def first_seen(path: str) -> str | None:
    proc = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%ad", "--date=short", "--", path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    dates = [line.strip() for line in proc.stdout.splitlines() if DATE_RE.fullmatch(line.strip())]
    # git log is newest-first, so dates[-1] is the OLDEST = first appearance.
    return dates[-1] if dates else None


def main() -> int:
    require_full_history()
    if not LEDGER.is_file():
        sys.exit(f"missing ledger: {LEDGER}")
    rows = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
    sources = sorted({row["source"] for row in rows})
    entries: dict[str, str] = {}
    missing = []
    for source in sources:
        date = first_seen(source)
        if date:
            entries[source] = date
        else:
            # Fall back to the ledger date only if it is a valid date; otherwise
            # record the ledger value so the gap is visible and must be fixed.
            ledger_date = (next((r.get("date") for r in rows if r["source"] == source), "") or "").strip()
            if DATE_RE.fullmatch(ledger_date):
                entries[source] = ledger_date
            else:
                missing.append(source)
    if missing:
        sys.exit("REFUSE: the following sources have no git first-appearance and no valid ledger date: " + ", ".join(missing[:20]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0.0",
        "computed_from": "git log --follow --diff-filter=A --format=%ad --date=short",
        "history_requirement": "FULL",
        "entry_count": len(entries),
        "entries": entries,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"SOURCE_FIRST_SEEN_WRITTEN entries={len(entries)} -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
