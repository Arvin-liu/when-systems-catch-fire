#!/usr/bin/env python3
"""Generate the governed ``source-first-seen.json`` map.

This map records, for every result source referenced by the human-results
ledger, the date that source *first appears* in repository history
(``git log --follow --diff-filter=A`` in both the Ignition and repository roots,
with a ``git log --full-history -m`` fallback for additions hidden by merge
simplification). It is computed ONCE from a FULL
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

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "data/governance/human-results/result-ledger.jsonl"
OUT = ROOT / "data/governance/knowledge-experience/source-first-seen.json"
DATE_RE = re.compile(r"20\d{2}-\d{2}-\d{2}")
LEGACY_COMPUTED_FROM = "git log --follow --diff-filter=A --format=%ad --date=short"
INTERIM_COMPUTED_FROM = (
    "git log --follow --diff-filter=A --format=%ad --date=short; "
    "fallback: git log --full-history -m --diff-filter=A --format=%ad --date=short"
)
COMPUTED_FROM = (
    "git log --follow --diff-filter=A --format=%ad --date=short (Ignition and repository roots); "
    "fallback: git log --full-history -m --diff-filter=A --format=%ad --date=short (both roots)"
)


def require_full_history() -> None:
    proc = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0 or proc.stdout.strip() not in {"true", "false"}:
        sys.exit("REFUSE: cannot establish whether source-first-seen.json has full Git history.")
    if proc.stdout.strip() == "true":
        sys.exit(
            "REFUSE: source-first-seen.json must be generated from a FULL clone. "
            "Run `git fetch --unshallow` first."
        )


def history_dates(path: str, cwd: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%ad", "--date=short", "--", path],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    dates = [line.strip() for line in proc.stdout.splitlines() if DATE_RE.fullmatch(line.strip())]
    if not dates:
        # Default path history can simplify away an add that arrived through a
        # merge commit. Compare each merge parent so the source's introducing
        # commit remains visible to the full-history census.
        proc = subprocess.run(
            ["git", "log", "--full-history", "-m", "--diff-filter=A", "--format=%ad", "--date=short", "--", path],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        dates = [line.strip() for line in proc.stdout.splitlines() if DATE_RE.fullmatch(line.strip())]
    return dates


def first_seen(path: str) -> str | None:
    # Source paths are relative to ignition/, but some files first appeared at
    # the repository root before being moved under ignition/. Search both
    # histories and keep the earliest date; checking only the current path can
    # silently replace the source's original date with its later migration date.
    dates = history_dates(path, ROOT) + history_dates(path, ROOT.parent)
    return min(dates) if dates else None


def collect_entries(
    rows: list[dict], existing_entries: dict[str, str] | None = None, *,
    recompute_all: bool = False, recompute_sources: set[str] | None = None,
) -> tuple[dict[str, str], int, int]:
    """Reuse committed full-history dates and compute only newly referenced sources."""
    previous = {} if recompute_all else (existing_entries or {})
    sources = sorted({row["source"] for row in rows})
    refresh = recompute_sources or set()
    unknown_refresh = refresh - set(sources)
    if unknown_refresh:
        raise ValueError("requested source refresh is absent from the ledger: " + ", ".join(sorted(unknown_refresh)))
    entries: dict[str, str] = {}
    missing = []
    reused = 0
    computed = 0
    for source in sources:
        date = None if source in refresh else previous.get(source)
        if date and DATE_RE.fullmatch(date):
            entries[source] = date
            reused += 1
            continue
        computed += 1
        date = first_seen(source)
        if date:
            entries[source] = date
        else:
            # Fall back to the ledger date only if it is a valid date; otherwise
            # record the gap so the generated map remains complete and auditable.
            ledger_date = (next((r.get("date") for r in rows if r["source"] == source), "") or "").strip()
            if DATE_RE.fullmatch(ledger_date):
                entries[source] = ledger_date
            else:
                missing.append(source)
    if missing:
        raise ValueError("sources have no git first-appearance and no valid ledger date: " + ", ".join(missing[:20]))
    return entries, reused, computed


def load_existing_entries() -> dict[str, str]:
    """Load only a complete map previously marked as generated from full history."""
    if not OUT.is_file():
        return {}
    try:
        payload = json.loads(OUT.read_text(encoding="utf-8"))
        entries = payload["entries"]
        if (
            payload.get("schema_version") != "1.0.0"
            or payload.get("computed_from") not in {LEGACY_COMPUTED_FROM, INTERIM_COMPUTED_FROM, COMPUTED_FROM}
            or payload.get("history_requirement") != "FULL"
            or payload.get("entry_count") != len(entries)
            or not isinstance(entries, dict)
            or not all(isinstance(k, str) and isinstance(v, str) and DATE_RE.fullmatch(v) for k, v in entries.items())
        ):
            return {}
        return entries
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recompute-all", action="store_true",
        help="ignore the committed full-history map and recompute every source date",
    )
    parser.add_argument(
        "--recompute-source", action="append", default=[], metavar="PATH",
        help="recompute one ledger source path while reusing all other committed dates; repeat as needed",
    )
    args = parser.parse_args()
    require_full_history()
    if not LEDGER.is_file():
        sys.exit(f"missing ledger: {LEDGER}")
    rows = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing = {} if args.recompute_all else load_existing_entries()
    try:
        entries, reused, computed = collect_entries(
            rows,
            existing,
            recompute_all=args.recompute_all,
            recompute_sources=set(args.recompute_source),
        )
    except ValueError as exc:
        sys.exit(f"REFUSE: {exc}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0.0",
        "computed_from": COMPUTED_FROM,
        "history_requirement": "FULL",
        "entry_count": len(entries),
        "entries": entries,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"SOURCE_FIRST_SEEN_WRITTEN entries={len(entries)} reused={reused} computed={computed} "
        f"-> {OUT.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
