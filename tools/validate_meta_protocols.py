#!/usr/bin/env python3
"""Validate the meta-protocol generation layer data.

Checks:
1. data/meta-protocols/meta-protocols.json exists and has exactly 12 protocols
2. protocol ids == {V1..V4, S1..S4, E1..E4}; each dimension has exactly 4
3. data/meta-protocols/meta-protocol-combinations.json exists with exactly 64 combos,
   each combo references exactly one V, one S, one E, combo_id unique
4. data/meta-protocols/book-validation-cases-20260709.json exists with exactly 22 cases,
   all status == candidate_only, all formal_case_id is null (no auto C ids)

Prints ALL_META_PROTOCOL_DATA_VALID on success, else NON_VALID + reasons and exits 1.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "meta-protocols"

EXPECTED_PROTOCOLS = (
    [f"V{i}" for i in range(1, 5)]
    + [f"S{i}" for i in range(1, 5)]
    + [f"E{i}" for i in range(1, 5)]
)
EXPECTED_V = {f"V{i}" for i in range(1, 5)}
EXPECTED_S = {f"S{i}" for i in range(1, 5)}
EXPECTED_E = {f"E{i}" for i in range(1, 5)}


def fail(reason):
    print("NON_VALID")
    print("FAIL:", reason)
    sys.exit(1)


def load(name):
    p = DATA / name
    if not p.exists():
        fail(f"missing file: {p}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"invalid JSON in {name}: {e}")


def main():
    proto = load("meta-protocols.json")
    protocols = proto.get("protocols", [])
    if len(protocols) != 12:
        fail(f"expected 12 protocols, got {len(protocols)}")
    ids = [p["id"] for p in protocols]
    if sorted(ids) != sorted(EXPECTED_PROTOCOLS):
        fail(f"protocol id set mismatch: {ids}")
    dims = {"value": 0, "structure": 0, "evolution": 0}
    for p in protocols:
        if p["dimension"] not in dims:
            fail(f"bad dimension on {p['id']}: {p['dimension']}")
        dims[p["dimension"]] += 1
    if dims != {"value": 4, "structure": 4, "evolution": 4}:
        fail(f"dimension counts wrong: {dims}")

    combos = load("meta-protocol-combinations.json")
    comb = combos.get("combinations", [])
    if len(comb) != 64:
        fail(f"expected 64 combinations, got {len(comb)}")
    seen = set()
    for c in comb:
        cid = c["combo_id"]
        if cid in seen:
            fail(f"duplicate combo_id: {cid}")
        seen.add(cid)
        v, s, e = c["value_protocol"], c["structure_protocol"], c["evolution_protocol"]
        if v not in EXPECTED_V or s not in EXPECTED_S or e not in EXPECTED_E:
            fail(f"combo {cid} has invalid protocol refs: {v},{s},{e}")
        if f"{v}-{s}-{e}" != cid:
            fail(f"combo_id {cid} inconsistent with protocols {v}-{s}-{e}")

    books = load("book-validation-cases-20260709.json")
    cases = books.get("cases", [])
    if len(cases) != 22:
        fail(f"expected 22 book validation cases, got {len(cases)}")
    for c in cases:
        if c.get("status") != "candidate_only":
            fail(f"{c.get('temporary_id')} status != candidate_only: {c.get('status')}")
        if c.get("formal_case_id") is not None:
            fail(f"{c.get('temporary_id')} has a formal_case_id assigned (must be null)")
        fid = c.get("temporary_id", "")
        if not (fid.startswith("BC-20260709-") and fid[13:].isdigit()):
            fail(f"{c.get('temporary_id')} has unexpected temporary_id format")

    print("ALL_META_PROTOCOL_DATA_VALID")
    print(f"protocols={len(protocols)} combinations={len(comb)} book_cases={len(cases)}")


if __name__ == "__main__":
    main()
