"""Data-driven access to the Research OS registries under data/research-os/.

Single source of truth: the JSON registries. The engine never hard-codes the
vocabulary; it reads it here.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "research-os"


def _load(name: str):
    with open(DATA_DIR / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def action_vocabulary() -> dict:
    return _load("action-vocabulary.json")


@lru_cache(maxsize=1)
def obligation_classes() -> dict:
    return _load("obligation-classes.json")


@lru_cache(maxsize=1)
def gap_codes() -> dict:
    return _load("gap-codes.json")


@lru_cache(maxsize=1)
def episode_states() -> dict:
    return _load("episode-states.json")


ACTION_CODES: list[str] = [a["code"] for a in action_vocabulary()["actions"]]
ACTION_BY_CODE: dict[str, dict] = {a["code"]: a for a in action_vocabulary()["actions"]}
GAP_CODE_LIST: list[str] = [g["code"] for g in gap_codes()["codes"]]
GAP_BY_CODE: dict[str, dict] = {g["code"]: g for g in gap_codes()["codes"]}
STATE_CODES: list[str] = list(episode_states()["states"].keys())
OBLIGATION_CLASS_CODES: list[str] = [c["code"] for c in obligation_classes()["classes"]]
CLASS_TO_GAP: dict[str, str] = {c["code"]: c["maps_to_gap"] for c in obligation_classes()["classes"]}
STATUS_ENUM: list[str] = obligation_classes()["status_enum"]
SEVERITY_RANK = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def assert_action(code: str) -> None:
    if code not in ACTION_BY_CODE:
        raise ValueError(f"unknown action code: {code}")


def assert_gap(code: str) -> None:
    if code not in GAP_BY_CODE:
        raise ValueError(f"unknown gap code: {code}")


def assert_state(code: str) -> None:
    if code not in STATE_CODES:
        raise ValueError(f"unknown state: {code}")


def assert_obligation_class(code: str) -> None:
    if code not in OBLIGATION_CLASS_CODES:
        raise ValueError(f"unknown obligation class: {code}")


def assert_status(code: str) -> None:
    if code not in STATUS_ENUM:
        raise ValueError(f"unknown obligation status: {code}")


# ---------------------------------------------------------------------------
# Strategy packs (Checkpoint C)
# ---------------------------------------------------------------------------
# Claim ceilings mirror obligation_graph.VALID_CEILINGS. Duplicated here as a
# local enum to avoid a circular import (obligation_graph imports registries).
CLAIM_CEILING_ENUM: list[str] = [
    "SPECULATIVE",
    "TENTATIVE",
    "QUALIFIED",
    "BOUNDED_STRONG",
    "NOT_ASSERTED",
]


def _validate_strategy_pack(pack: dict) -> None:
    """Cross-validate a pack's references against the existing registries."""
    code = pack.get("code")
    if not code:
        raise ValueError("strategy pack missing 'code'")
    if pack.get("registry") != "strategy-pack":
        raise ValueError(f"strategy pack {code}: registry must be 'strategy-pack'")
    for oc in pack.get("required_obligations", []):
        assert_obligation_class(oc)
    for gc in pack.get("typical_gaps", []):
        assert_gap(gc)
    for ac in pack.get("mandatory_calculations", []):
        assert_action(ac)
    for fm in pack.get("common_failure_modes", []):
        g = fm.get("gap_code")
        if not g:
            raise ValueError(f"strategy pack {code}: common_failure_modes entry missing gap_code")
        assert_gap(g)
    ceil = pack.get("max_claim_ceiling")
    if ceil not in CLAIM_CEILING_ENUM:
        raise ValueError(f"strategy pack {code}: invalid max_claim_ceiling {ceil}")
    for ec in pack.get("escalation_conditions", []):
        tg = ec.get("trigger_gap")
        if tg:
            assert_gap(tg)
        if ec.get("escalate_to") != "GPT_OWNER":
            raise ValueError(f"strategy pack {code}: escalate_to must be 'GPT_OWNER'")
    for sc in pack.get("stop_criteria", []):
        tg = sc.get("trigger_gap")
        if tg:
            assert_gap(tg)
        ts = sc.get("terminal_state")
        if ts:
            assert_state(ts)


@lru_cache(maxsize=1)
def strategy_packs() -> dict:
    """Load and validate every strategy pack under data/research-os/strategy-packs/.

    Returns a code-keyed dict. Malformed packs raise at import/load time so a bad
    registry never reaches the engine.
    """
    packs: dict[str, dict] = {}
    pack_dir = DATA_DIR / "strategy-packs"
    for path in sorted(pack_dir.glob("*.json")):
        with open(path, "r", encoding="utf-8") as fh:
            pack = json.load(fh)
        _validate_strategy_pack(pack)
        packs[pack["code"]] = pack
    return packs


STRATEGY_PACK_CODES: list[str] = list(strategy_packs().keys())
PACK_BY_CODE: dict[str, dict] = strategy_packs()


def assert_strategy_pack(code: str) -> None:
    """Validate that a strategy-pack code exists and its contents are valid.

    Used by the episode kernel at creation time. Because PACK_BY_CODE is built
    from validated loads, this also guarantees reference integrity.
    """
    if code not in PACK_BY_CODE:
        raise ValueError(f"unknown strategy pack: {code}")
