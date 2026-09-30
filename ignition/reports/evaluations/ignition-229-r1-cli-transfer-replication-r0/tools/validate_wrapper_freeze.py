#!/usr/bin/env python3
"""Check frozen source/prompt bundles and the synthetic transport fixture only."""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name): return json.loads((ROOT / name).read_text(encoding="utf-8"))
source = load("source-bundle-manifest.json")
prompts = load("prompt-bundle-manifest.json")
assert source["expected_file_count"] == source["copied_file_count"] == 19
assert source["original_freeze_manifest_sha256"] == "057d76eae931881a3209129528fef500aef762854beb6b5288411441bbf55b95"
for row in source["files"]:
    p = ROOT.parents[3] / row["copied_path"]
    assert sha(p) == row["expected_sha256"] == row["copied_sha256"], row["copied_path"]
assert prompts["expected_prompt_count"] == prompts["copied_prompt_count"] == 18
for row in prompts["prompts"]:
    p = ROOT.parents[3] / row["copied_path"]
    assert p.stat().st_size == row["byte_length"]
    assert sha(p) == row["sha256"] == row["copied_sha256"], row["copied_path"]
dispatcher = ROOT / "tools/dispatcher.py"
assert sha(dispatcher) == "c4e2aa109201c8292149a7a92020be36470f90be6d2ab7927d8c82c4b9cce577"
canary = ROOT / "fixtures/large-input-nonscientific-canary.txt"
plan = load("canary-plan.json")
assert canary.stat().st_size == plan["canary_bytes"] >= max(plan["max_frozen_successor_prompt_bytes"], 65536)
assert sha(canary) == plan["canary_sha256"]
assert canary.read_bytes().endswith(b"Reply exactly with CANARY_ACK.\n")
freeze = load("freeze-manifest.json")
for row in freeze["files"]:
    p = ROOT / row["path"]
    assert sha(p) == row["sha256"], row["path"]
print("SOURCE_PREREG=19/19 PASS")
print("PROMPTS=18/18 PASS")
print("H1_DISPATCHER=PASS")
print("SYNTHETIC_CANARY_FIXTURE=PASS")
print("WRAPPER_FREEZE_MANIFEST=PASS")
