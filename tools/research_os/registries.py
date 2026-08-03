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
