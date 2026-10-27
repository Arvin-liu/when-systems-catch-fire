"""Deep Research Capability — negative (must-reject) fixture generator (Round 1).

Emits intentionally-invalid example records into
``tests/fixtures/deep_research/round1/negative/``. Each file carries two
metadata keys used only by the test harness:
  * ``_record`` — the schema/record name to validate against
  * ``_expect`` — a short description of the expected rejection (for failure
    messages; the harness asserts validation RAISES, it does not string-match)
The remaining keys are the invalid record body. These prove the fail-closed
contract (executor can never self-approve / mark complete / raise a ceiling,
opened sources must declare inspected scope, STOP_SUFFICIENT requires gates,
enum values are constrained, no extra/unknown fields).

Run from the repository root:
    python3 tools/deep_research/generate_negative_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "tests" / "fixtures" / "deep_research" / "round1" / "negative"

# (filename, record_name, expect_reason, invalid_body)
NEGATIVE_EXAMPLES = [
    ("source-record-opened-no-scope.json", "source-record",
     "opened=true requires inspected_scope (fail-closed if/then)",
     {"source_id": "src-X", "access_level": "FULL_TEXT", "opened": True}),
    ("sufficiency-stop-no-gates.json", "research-sufficiency-decision",
     "STOP_SUFFICIENT_CANDIDATE requires hard_gates_passed=true",
     {"decision_id": "suff-X", "episode_id": "ep-X", "hard_gates_passed": False,
      "decision": "STOP_SUFFICIENT_CANDIDATE"}),
    ("executor-observation-self-approved.json", "executor-observation",
     "self_approved is a prohibited key",
     {"observation_id": "obs-X", "action_id": "act-X", "observations": [],
      "source_identities": [], "access_level": "DISCOVERED", "calculation_result": None,
      "errors": [], "provenance": [], "timestamps": {}, "self_approved": True}),
    ("executor-observation-claim-ceiling.json", "executor-observation",
     "claim_ceiling is a prohibited key in executor return",
     {"observation_id": "obs-X", "action_id": "act-X", "observations": [],
      "source_identities": [], "access_level": "DISCOVERED", "calculation_result": None,
      "errors": [], "provenance": [], "timestamps": {}, "claim_ceiling": "BOUNDED_STRONG"}),
    ("executor-observation-mark-complete.json", "executor-observation",
     "mark_episode_complete is a prohibited key in executor return",
     {"observation_id": "obs-X", "action_id": "act-X", "observations": [],
      "source_identities": [], "access_level": "DISCOVERED", "calculation_result": None,
      "errors": [], "provenance": [], "timestamps": {}, "mark_episode_complete": True}),
    ("evidence-obligation-bad-class.json", "evidence-obligation",
     "obligation_class must be a valid Research OS obligation class enum",
     {"obligation_id": "obl-X", "claim_id": "claim-X", "obligation_class": "NONSENSE",
      "status": "OPEN"}),
    ("research-brief-missing-scope-nested.json", "research-brief",
     "scope requires population/object/timeframe/outcomes",
     {"brief_id": "brief-X", "question_version": "v1", "question": "q",
      "scope": {"population": "p", "object": "o", "timeframe": "t"},  # missing outcomes
      "strategy_pack": "sp", "frozen": True}),
    ("research-trace-event-bad-sha.json", "research-trace-event",
     "payload_sha256 must be 64 hex chars",
     {"event_id": "evt-X", "timestamp": "2026-01-01T00:00:00Z", "type": "STEP",
      "actor": "kernel", "payload_sha256": "not-a-real-sha"}),
    ("topic-candidate-extra-field.json", "research-topic-candidate",
     "additionalProperties:False rejects unknown fields",
     {"candidate_id": "cand-X", "proposed_question": "q", "source_of_seed": "PROJECT_GAP",
      "proposed_strategy_pack": "sp", "bogus_field": 1}),
    ("claim-evidence-record-bad-ceiling.json", "claim-evidence-record",
     "claim_ceiling must be a valid Research OS ceiling enum",
     {"claim_id": "claim-X", "claim_text": "c", "claim_ceiling": "SUPER_SURE",
      "source_relations": []}),
    ("research-action-bad-code.json", "research-action",
     "action_code must be a valid kernel action code enum",
     {"action_id": "act-X", "action_code": "FLY_TO_MOON"}),
    ("queue-item-bad-status.json", "research-queue-item",
     "status must be a valid QUEUE_ITEM_STATUS enum",
     {"queue_item_id": "qi-X", "status": "MYSTERIOUS"}),
]


def write_all() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for fname, record, expect, body in NEGATIVE_EXAMPLES:
        doc = {"_record": record, "_expect": expect, **body}
        with open(OUT_DIR / fname, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        written += 1
    return written


if __name__ == "__main__":
    n = write_all()
    print(f"wrote {n} negative deep-research fixtures to {OUT_DIR}")
