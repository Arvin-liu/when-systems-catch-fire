"""PART C (a): the 12 cross-domain fixtures run the closed loop and each
produces a valid runtime-envelope receipt.

No license header: matches repo tests/ convention.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402

from tools.adaptive_relational_runtime import runtime  # noqa: E402

FIX = HERE / "fixtures"


def _fixture_files():
    return sorted(FIX.glob("*.json"))


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.stem)
def test_fixture_produces_valid_envelope(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    source = data["source"]
    observation = data["observation"]

    eng = runtime.ARRRuntime()
    # Source + Observation are validated inside run() (OBSERVE stage).
    envelope = eng.run(source, observation)

    # Envelope validates against its schema.
    eng.contract.validate_generic("runtime-envelope", envelope)
    assert envelope["closed"] is True
    assert envelope["mode_assertion"]["promote_called"] is False
    assert envelope["mode_assertion"]["evolve_called"] is False
    assert envelope["mode_assertion"]["real_world_actions"] == 0
    # All 10 stages succeeded.
    assert len(eng.stages) == 10
    assert all(s["ok"] for s in eng.stages)


@pytest.mark.parametrize("path", _fixture_files(), ids=lambda p: p.stem)
def test_fixture_records_validate_against_schemas(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    eng = runtime.ARRRuntime()
    eng.contract.validate_record(data["source"])
    eng.contract.validate_record(data["observation"])
    # The reconstruction fixture carries an Assertion (schema C) that must
    # validate and carry the explicit/hidden-assumption split.
    if "assertion" in data:
        eng.contract.validate_record(data["assertion"])
        a = data["assertion"]
        assert a["explicitness"] == "INTERPRETER_RECONSTRUCTION"
        assert a["speaker_commitment"] == "attributed_by_interpreter"
        assert len(a["alternatives"]) >= 1
        assert a.get("reconstruction_basis")


def test_exactly_12_fixtures():
    assert len(_fixture_files()) == 12
