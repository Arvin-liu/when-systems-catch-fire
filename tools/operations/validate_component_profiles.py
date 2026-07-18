#!/usr/bin/env python3
"""Fail-closed structural validator for generated component execution profiles."""
from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.operations.generate_component_profiles import ROOT, REGISTRY, OUTPUT, build, canonical, safe_argv

def validate():
    actual=json.loads(OUTPUT.read_text()); expected=build()
    if canonical(actual) != canonical(expected): raise ValueError("profiles are not the deterministic generated authority")
    ids=[p["component_id"] for p in actual["profiles"]]; known=[c["component_id"] for c in json.loads(REGISTRY.read_text())["components"]]
    if len(ids)!=len(set(ids)) or set(ids)!=set(known): raise ValueError("profiles must exactly cover registry once")
    for p in actual["profiles"]:
        safe_argv(p["validator_argv"])
        if p["execution_kind"] == "automatic":
            safe_argv(p.get("producer_argv", [])); safe_argv(p.get("freshness_validator_argv", []))
        if p["execution_kind"] == "manual" and "producer_argv" in p: raise ValueError("manual profile cannot claim automatic producer")
        if p["execution_kind"] == "attestation" and "producer_argv" in p: raise ValueError("external profile cannot have local producer")
    return True
if __name__ == "__main__": validate(); print("component profiles valid")
