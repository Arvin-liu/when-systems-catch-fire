"""Regression tests for the two defects found while running the Task 115 loops.

Self-contained runner:

    python3 tests/test_research_os_resumability.py

Covers:
1. pause/resume returns to the paused-from state (regression for the resume
   fallback bug that always landed on EVIDENCE_GATHERING);
2. the R1 replay loader performs documented syntactic-only repair on invalid
   ROUND.json and reports it, never silently.
"""

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOLS = str(REPO / "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import research_os.kernel as kernel
from research_os import r1_replay

_FAILS = []


def check(name, cond, detail=""):
    if cond:
        print(f"PASS  {name}")
    else:
        print(f"FAIL  {name}  {detail}")
        _FAILS.append(name)


def test_pause_resume_returns_to_paused_from():
    for intermediate in ("QUESTION_FROZEN", "EVIDENCE_GATHERING", "ANALYSIS"):
        ep = kernel.new_episode("ep-resume", "q", "test", "QUANTITATIVE_DATA_RECONCILIATION")
        kernel.transition(ep, "QUESTION_FROZEN")
        if intermediate in ("EVIDENCE_GATHERING", "ANALYSIS"):
            kernel.transition(ep, "EVIDENCE_GATHERING")
        if intermediate == "ANALYSIS":
            kernel.transition(ep, "ANALYSIS")
        ep["paused_from"] = ep["state"]
        kernel.transition(ep, "PAUSED_RESUMABLE")
        # mirror cli.cmd_resume logic (post-fix)
        target = ep.get("paused_from") or "EVIDENCE_GATHERING"
        allowed = kernel.ALLOWED_NEXT.get("PAUSED_RESUMABLE", [])
        if target not in allowed:
            target = "EVIDENCE_GATHERING"
        kernel.transition(ep, target)
        check(f"resume returns to paused_from ({intermediate})", ep["state"] == intermediate, ep["state"])


def test_replay_loader_syntactic_repair():
    valid = {
        "campaign_id": "T", "round_number": 99, "short_slug": "synthetic",
        "start_time": "2026-08-03T00:00:00+08:00", "end_time": "2026-08-03T00:10:00+08:00",
        "timezone": "Asia/Shanghai", "question": "q", "initial_claim": "c",
        "selection_score": {}, "verdict": "CONTESTED", "source_count": 1,
        "source_classes": ["peer_reviewed_research"],
        "report_sha256": "ab" * 32, "commit_sha": None,
        "state": "COMPLETE_AWAITING_EXTERNAL_REVIEW",
    }
    with tempfile.TemporaryDirectory() as td:
        rd = Path(td) / "round-099-synthetic"
        rd.mkdir()
        (rd / "ROUND.json").write_text(json.dumps(valid), encoding="utf-8")
        meta, repair = r1_replay.load_round_meta(rd)
        check("valid ROUND.json parses without repair", repair is None and meta["round_number"] == 99)
        # break it exactly like R1 round-002: drop the comma after report_sha256
        raw = json.dumps(valid, indent=2)
        lines = raw.splitlines()
        for i, ln in enumerate(lines):
            if ln.strip().startswith('"report_sha256"') and ln.rstrip().endswith(","):
                lines[i] = ln.rstrip()[:-1]
        (rd / "ROUND.json").write_text("\n".join(lines), encoding="utf-8")
        meta2, repair2 = r1_replay.load_round_meta(rd)
        check("R1-002-style missing comma repaired syntactically", repair2 is not None and meta2["round_number"] == 99, str(repair2))
        check("repair never alters semantic fields", meta2["report_sha256"] == "ab" * 32 and meta2["verdict"] == "CONTESTED")


def main():
    test_pause_resume_returns_to_paused_from()
    test_replay_loader_syntactic_repair()
    if _FAILS:
        print(f"\n{len(_FAILS)} REGRESSION TEST(S) FAILED")
        sys.exit(1)
    print("\nALL RESUMABILITY/REPLAY REGRESSION TESTS PASSED")


if __name__ == "__main__":
    main()
