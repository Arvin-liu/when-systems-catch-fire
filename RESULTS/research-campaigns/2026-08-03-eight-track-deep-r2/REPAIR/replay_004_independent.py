#!/usr/bin/env python3
"""Line C independent replay — Track 004 core electricity reconciliation.

Clean-environment, offline, stdlib-only. This is an INDEPENDENT implementation:
it does not import or copy the track's recompute_004.py. It consumes only the
committed input CSVs and compares its own arithmetic against the committed
output recomputed_metrics.json.

Environment: fresh clone at qwen38max/eight-track-r2-auditability-repair-r1-20260803,
no network access used.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tracks" / "004-clean-electricity-2025" / "reproducibility"
IN, OUT = ROOT / "input", ROOT / "output"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def world_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r.get("Area") == "World"]


def main() -> None:
    ember_csv = IN / "ember_world_2024_2025.csv"
    iea_gen_csv = IN / "iea_generation_by_source_2015_2025.csv"
    iea_chg_csv = IN / "iea_annual_change_2024_2025.csv"
    committed = json.loads((OUT / "recomputed_metrics.json").read_text(encoding="utf-8"))
    report = {
        "track": "004-clean-electricity-2025",
        "replay_class": "INDEPENDENT_OFFLINE_RECOMPUTATION",
        "environment": "clean clone, python3 stdlib only, no network",
        "input_sha256": {p.name: sha256(p) for p in (ember_csv, iea_gen_csv, iea_chg_csv)},
        "committed_output_sha256": sha256(OUT / "recomputed_metrics.json"),
        "comparisons": [],
        "verdict": None,
    }

    def compare(name: str, mine: float, theirs: float, tol: float = 1e-6) -> None:
        ok = abs(mine - theirs) <= tol
        report["comparisons"].append({"metric": name, "independent": mine, "committed": theirs, "match": ok})

    rows = world_rows(ember_csv)
    gen = {(r["Year"], r["Electricity source"]): float(r["Generation (TWh)"]) for r in rows}
    sources_2025 = {s for (y, s) in gen if y == "2025"}
    # committed totals come from the explicit "Total generation" row (the CSV
    # also contains aggregate rows Clean/Fossil/Renewables/Demand that must not
    # be summed again)
    total_2024 = round(gen[("2024", "Total generation")], 6)
    total_2025 = round(gen[("2025", "Total generation")], 6)
    deltas = {s: round(gen[("2025", s)] - gen[("2024", s)], 6) for s in sources_2025}
    ce = committed["ember"]
    compare("ember.2024_total_generation_twh", total_2024, ce["2024_total_generation_twh"])
    compare("ember.2025_total_generation_twh", total_2025, ce["2025_total_generation_twh"])
    compare("ember.clean_increment_twh", deltas.get("Clean", 0.0), ce["clean_increment_twh"])
    compare("ember.renewables_increment_twh", deltas.get("Renewables", 0.0), ce["renewables_increment_twh"])
    compare("ember.nuclear_increment_twh", deltas.get("Nuclear", 0.0), ce["nuclear_increment_twh"])
    compare("ember.coal_increment_twh", deltas.get("Coal", 0.0), ce["coal_increment_twh"])
    compare("ember.gas_increment_twh", deltas.get("Gas", 0.0), ce["gas_increment_twh"])
    compare("ember.other_fossil_increment_twh", deltas.get("Other fossil", 0.0), ce["other_fossil_increment_twh"])
    compare("ember.fossil_increment_twh", deltas.get("Fossil", 0.0), ce["fossil_increment_twh"])
    fossil_total = round(sum(deltas.get(s, 0.0) for s in ("Coal", "Gas", "Other fossil")), 6)
    compare("ember.fossil_equals_coal+gas+other_fossil", fossil_total, deltas.get("Fossil", 0.0), tol=0.005)

    # IEA chart table is transposed: first row = source columns, first column = year
    def num(s: str) -> float:
        return float(str(s).replace(",", "").strip())

    lines = [l.split(";") for l in iea_gen_csv.read_text(encoding="utf-8").splitlines() if l.strip()]
    header = [h.strip() for h in lines[0]]
    by_year = {}
    for row in lines[1:]:
        if len(row) < 2 or not row[0].strip().isdigit():
            continue
        by_year[row[0].strip()] = [num(c) for c in row[1:] if c.strip()]
    ic = committed["iea_chart"]
    g24 = round(sum(by_year.get("2024", [])), 3)
    g25 = round(sum(by_year.get("2025", [])), 3)
    compare("iea.generation_2024_twh", g24, ic["generation_2024_twh"], tol=0.05)
    compare("iea.generation_2025_twh", g25, ic["generation_2025_twh"], tol=0.05)

    fails = [c for c in report["comparisons"] if c["match"] is False]
    report["verdict"] = "MATCH" if not fails else "MISMATCH"
    out_path = Path(__file__).parent / "replay-004-result.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"004 independent replay: {report['verdict']} ({len(report['comparisons'])} comparisons, {len(fails)} mismatch)")


if __name__ == "__main__":
    main()
