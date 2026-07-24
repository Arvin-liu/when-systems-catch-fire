"""Generate the 12 cross-domain fixtures for ARR commit 4.

Run once:  python3 tests/adaptive_relational_runtime/gen_fixtures.py
Writes tests/adaptive_relational_runtime/fixtures/*.json. Each fixture is a
valid runtime input (Source + Observation, optionally an Assertion for the
explicit/hidden-assumption split). The pytest suite loads these and runs the
closed loop, asserting a valid runtime-envelope receipt.

No license header: test scaffolding, matching repo tests/ convention.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

from helpers import (make_source, make_observation,  # noqa: E402
                     make_assertion_reconstruction)

FIX = HERE / "fixtures"


def text_fixture(idx: int, content: str, excerpt: str, *, reconstruct=False):
    src = make_source(source_type="text",
                      locator={"ref_type": "url",
                               "ref_value": f"https://example.com/doc/{idx}"},
                      content=content)
    obs = make_observation(
        source_id=src["record_id"],
        raw_excerpt={"kind": "inline", "value": excerpt},
        collection_metadata={"method": "manual", "tool_ref": "fixture",
                             "parameters": {}})
    fx = {"source": src, "observation": obs}
    if reconstruct:
        ast = make_assertion_reconstruction(
            subject_ref=src["record_id"],
            observation_ref=obs["record_id"],
            alternatives=[
                "Speaker meant X literally",
                "Speaker implied Y by context",
            ],
            reconstruction_basis={
                "method": "interpreter_reconstruction_from_excerpt",
                "from_observation_refs": [obs["record_id"]],
            },
            proposition="The speaker's statement is interpreted as claiming Y, "
                        "which was not explicitly stated.",
            uncertainty="Explicit content present; hidden assumption reconstructed "
                        "by interpreter and flagged as attributed_by_interpreter.")
        fx["assertion"] = ast
    return fx


def git_fixture(idx: int, sha: str, excerpt: str):
    src = make_source(source_type="git_commit",
                      locator={"ref_type": "git_commit", "ref_value": sha},
                      content=f"commit {sha}\n{excerpt}", tier="PRIMARY")
    obs = make_observation(
        source_id=src["record_id"],
        raw_excerpt={"kind": "inline", "value": excerpt},
        collection_metadata={"method": "git_show", "tool_ref": "fixture",
                             "parameters": {"rev": sha}})
    return {"source": src, "observation": obs}


def structured_fixture(idx: int, content: str, excerpt: str):
    src = make_source(source_type="structured_data",
                      locator={"ref_type": "external_ref",
                               "ref_value": f"dataset://table/{idx}"},
                      content=content)
    obs = make_observation(
        source_id=src["record_id"],
        raw_excerpt={"kind": "inline", "value": excerpt},
        collection_metadata={"method": "schema_scan", "tool_ref": "fixture",
                             "parameters": {}})
    return {"source": src, "observation": obs}


def runtime_receipt_fixture(idx: int, receipt_id: str, excerpt: str):
    src = make_source(source_type="runtime_receipt",
                      locator={"ref_type": "external_ref",
                               "ref_value": f"receipt://{receipt_id}"},
                      content=f"operation receipt {receipt_id}", tier="PRIMARY")
    obs = make_observation(
        source_id=src["record_id"],
        raw_excerpt={"kind": "inline", "value": excerpt},
        collection_metadata={"method": "receipt_replay", "tool_ref": "fixture",
                             "parameters": {"receipt_id": receipt_id}})
    return {"source": src, "observation": obs}


def event_sequence_fixture(idx: int, content: str, excerpt: str):
    src = make_source(source_type="declared_event",
                      locator={"ref_type": "external_ref",
                               "ref_value": f"events://seq/{idx}"},
                      content=content)
    obs = make_observation(
        source_id=src["record_id"],
        raw_excerpt={"kind": "inline", "value": excerpt},
        collection_metadata={"method": "event_log", "tool_ref": "fixture",
                             "parameters": {}})
    return {"source": src, "observation": obs}


def main() -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    fixtures = {
        # 3 text
        "text-01": text_fixture(1, "The model outputs a summary of the report.",
                                "Summary text extracted from report."),
        "text-02": text_fixture(2, "Users reported latency spikes at peak hours.",
                                "User-reported latency observation."),
        "text-03": text_fixture(
            3,
            "We should ship the fix on Friday.",
            "We should ship the fix on Friday.",
            reconstruct=True),
        # 3 Git
        "git-01": git_fixture(1, "a" * 40,
                              "def foo():\n    return 1\n"),
        "git-02": git_fixture(2, "b" * 40,
                              "fix: handle None in parser\n"),
        "git-03": git_fixture(3, "c" * 40,
                              "refactor: extract helper\n"),
        # 2 structured
        "structured-01": structured_fixture(
            1, '{"rows": 100, "cols": 3}', '{"rows": 100, "cols": 3}'),
        "structured-02": structured_fixture(
            2, '{"metric": "accuracy", "value": 0.92}',
            '{"metric": "accuracy", "value": 0.92}'),
        # 2 runtime receipt
        "runtime-receipt-01": runtime_receipt_fixture(
            1, "op_" + "d" * 32, "admitted run receipt digest d..."),
        "runtime-receipt-02": runtime_receipt_fixture(
            2, "op_" + "e" * 32, "admitted run receipt digest e..."),
        # 2 event-sequence
        "event-sequence-01": event_sequence_fixture(
            1, "seq: boot -> ready -> serve",
            "boot -> ready -> serve"),
        "event-sequence-02": event_sequence_fixture(
            2, "seq: request -> queue -> respond",
            "request -> queue -> respond"),
    }
    for name, fx in fixtures.items():
        (FIX / f"{name}.json").write_text(
            json.dumps(fx, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(fixtures)} fixtures to {FIX}")


if __name__ == "__main__":
    main()
