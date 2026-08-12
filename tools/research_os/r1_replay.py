#!/usr/bin/env python3
"""R1 eight-round incident replay (Task 115 Line A, A2/A3).

Replays all eight R1 candidate packets from the exact locked tip
232299483f701e8304265c1484b5b50e5dcf2799 through the Research OS
diagnose + plan loop. The OS must not accept any R1 round as completed
research. This builder:

  1. reads ROUND.json / SOURCES.jsonl per round and STATUS.json for the
     campaign (exported from the locked tip);
  2. constructs one structured episode per round, mapping observed metadata
     onto episode signals WITHOUT inventing evidence:
       - elapsed time derived from start/end timestamps;
       - batch identical accessed_at timestamps -> source_timestamps_identical;
       - declared reading window = elapsed time (the only window that existed);
       - required reading floor = 0.5h per source (conservative lower bound for
         full-text reading; documented in the replay doc);
       - obligations the metadata cannot prove are OPEN; a listed-but-unverified
         primary URL is PARTIAL at best;
       - campaign closeout before the authorized deadline;
  3. runs diagnosis and scheduler planning;
  4. writes machine episodes + diagnosis + plan per round.

R1 is failure evidence, not accepted research. Nothing here promotes R1.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOLS = str(REPO / "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import research_os.kernel as kernel
import research_os.obligation_graph as og
import research_os.diagnosis as dx
import research_os.scheduler as scheduler
import research_os.registries as R

# Strategy-pack adjudication per R1 round. The mapping is a replay-time
# classification of each question's evidentiary type; it is recorded in the
# episode provenance so it can be challenged by review.
PACK_BY_SLUG = {
    "ai-weather-extremes": "QUANTITATIVE_DATA_RECONCILIATION",
    "handwriting-learning": "SYSTEMATIC_EVIDENCE_SYNTHESIS",
    "heat-action-plans": "POLICY_EFFECT_EVALUATION",
    "clean-electricity-2025": "QUANTITATIVE_DATA_RECONCILIATION",
    "glp1-cardiovascular-evidence": "RANDOMIZED_CLINICAL_EVIDENCE",
    "ai-coding-productivity": "ENGINEERING_BENCHMARK",
    "ev-fire-risk": "OBSERVATIONAL_CAUSALITY",
    "microplastics-cardiovascular": "SYSTEMATIC_EVIDENCE_SYNTHESIS",
}

READING_FLOOR_HOURS_PER_SOURCE = 0.5  # conservative lower bound, full-text


def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def load_round_meta(round_dir: Path) -> tuple[dict, str | None]:
    """Parse ROUND.json; on syntax defect apply the minimal documented repair.

    R1 round-002 ROUND.json omits a comma after report_sha256 (a genuine R1
    data-integrity defect). The repair is syntactic only: insert the missing
    comma between the two affected lines. The repair and the original failure
    are recorded in the episode provenance; no semantic content is altered.
    """
    raw = (round_dir / "ROUND.json").read_text(encoding="utf-8")
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        repaired = raw.replace('fff8"\n  "commit_sha"', 'fff8",\n  "commit_sha"')
        # generic fallback: insert comma between a string value line and a following key line
        if repaired == raw:
            import re
            repaired = re.sub(r'(")\n(\s*")', r'\1,\n\2', raw)
        meta = json.loads(repaired)  # raises if repair insufficient -> honest failure
        note = f"syntactic repair at char {exc.pos}: {exc.msg}; original strict parse failed"
        return meta, note


def build_episode(round_dir: Path, campaign_status: dict) -> dict:
    meta, parse_repair = load_round_meta(round_dir)
    sources = [
        json.loads(line)
        for line in (round_dir / "SOURCES.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    slug = meta["short_slug"]
    pack = PACK_BY_SLUG[slug]
    ep = kernel.new_episode(
        f"r1-replay-round-{meta['round_number']:03d}",
        meta["question"],
        "r1-incident-replay",
        pack,
    )
    start, end = parse_ts(meta["start_time"]), parse_ts(meta["end_time"])
    elapsed_hours = (end - start).total_seconds() / 3600.0
    ep["elapsed_time_hours"] = round(elapsed_hours, 4)
    ep["report_length_words"] = None  # length never used as completion evidence
    accessed = [s.get("accessed_at") for s in sources if s.get("accessed_at")]
    ep["source_timestamps_identical"] = len(set(accessed)) <= 1 and len(accessed) >= 2
    ep["source_identities"] = [
        {"source_id": s.get("source_id"), "url": s.get("url"), "accessed_at": s.get("accessed_at")}
        for s in sources
    ]
    ep["reading_integrity"] = {
        "declared_reading_window_hours": round(elapsed_hours, 4),
        "minimum_required_reading_hours": round(READING_FLOOR_HOURS_PER_SOURCE * len(sources), 4),
        "basis": "declared window is the actual elapsed window; floor is 0.5h/source conservative lower bound",
    }
    deadline = campaign_status.get("deadline")
    last_end = end
    ep["campaign_closeout_before_deadline"] = bool(
        deadline and campaign_status.get("status", "").startswith("COMPLETE") and last_end < parse_ts(deadline)
    )
    # Claims and obligations: R1 metadata proves no obligation was satisfied.
    # A listed URL is identification, not verified access -> PARTIAL at best.
    ceiling = min_claim_ceiling_for(pack)
    og.add_claim(ep, "c-primary", meta.get("initial_claim") or "(round claim)", ceiling)
    pack_meta = R.PACK_BY_CODE[pack]
    for i, oc in enumerate(pack_meta["required_obligations"], start=1):
        if oc == "PRIMARY_SOURCE":
            status = "PARTIAL"  # URLs listed; access level never verified
        else:
            status = "OPEN"
        og.add_obligation(ep, f"o{i:02d}", "c-primary", oc, status)
    kernel.transition(ep, "QUESTION_FROZEN", actor="r1-replay")
    kernel.transition(ep, "EVIDENCE_GATHERING", actor="r1-replay")
    rp = ep.setdefault("provenance", {})
    rp["packet_parse"] = {"strict_json_parse": parse_repair is None, "repair_note": parse_repair}
    rp["r1_replay"] = {
        "r1_locked_tip": "232299483f701e8304265c1484b5b50e5dcf2799",
        "round_number": meta["round_number"],
        "short_slug": slug,
        "r1_declared_state": meta.get("state"),
        "r1_verdict": meta.get("verdict"),
        "pack_adjudication": pack,
        "reading_floor_rule": f"{READING_FLOOR_HOURS_PER_SOURCE}h per source",
    }
    return ep


def min_claim_ceiling_for(pack: str) -> str:
    # Replay episodes carry the claim only to test the ceiling machinery; the
    # ceiling chosen is the lowest assertive level and is never raised here.
    return "SPECULATIVE" if pack in R.PACK_BY_CODE else "NOT_ASSERTED"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: r1_replay.py <exported-r1-campaign-dir> <output-dir>", file=sys.stderr)
        return 2
    campaign_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    status = json.loads((campaign_dir / "STATUS.json").read_text(encoding="utf-8"))
    summary = []
    completed_or_publish = 0
    for round_dir in sorted(campaign_dir.glob("round-*")):
        ep = build_episode(round_dir, status)
        diag = dx.diagnose(ep)
        sel = scheduler.plan(ep, diag)
        n = ep["provenance"]["r1_replay"]["round_number"]
        rec = {
            "episode": ep,
            "diagnosis": diag,
            "selected_action": sel["selected_action"],
            "ranked_candidates": sel["ranked_candidates"],
            "os_accepts_round_as_completed": kernel.is_terminal(ep)
            and ep["state"] in ("CANDIDATE_COMPLETE",),
        }
        out = out_dir / f"round-{n:03d}.json"
        out.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        codes = sorted({f["gap_code"] for f in diag["findings"]})
        summary.append(
            {
                "round": n,
                "slug": ep["provenance"]["r1_replay"]["short_slug"],
                "pack": ep["strategy_pack"],
                "gap_codes": codes,
                "selected_action": sel["selected_action"],
                "accepted_as_completed": rec["os_accepts_round_as_completed"],
            }
        )
        if rec["os_accepts_round_as_completed"] or sel["selected_action"] == "PUBLISH_CANDIDATE_PACKET":
            completed_or_publish += 1
        print(f"round {n}: {len(codes)} gaps; action={sel['selected_action']}; completed={rec['os_accepts_round_as_completed']}")
    (out_dir / "REPLAY-SUMMARY.jsonl").write_text(
        "\n".join(json.dumps(s, ensure_ascii=False) for s in summary) + "\n", encoding="utf-8"
    )
    if completed_or_publish:
        print("FATAL: OS accepted an R1 round as completed or selected publication", file=sys.stderr)
        return 1
    print(f"R1 REPLAY COMPLETE: 8/8 rounds rejected as completed research; episodes at {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
