#!/usr/bin/env python3
"""Re-download the public inputs, extract the global rows, and recompute 004."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "input"
OUTPUT = ROOT / "output"
INPUT.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)

EMBER_URL = "https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv"
IEA_GENERATION_URL = "https://www.iea.org/data-and-statistics/charts/global-electricity-generation-by-source-2015-2025"
IEA_CHANGE_URL = "https://www.iea.org/data-and-statistics/charts/annual-change-in-global-electricity-generation-by-source-2024-2025"


def get(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "R2-004-reproducibility/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_bytes(path: Path, data: bytes) -> None:
    path.write_bytes(data)


def extract_ember(data: bytes) -> list[dict[str, str]]:
    rows = list(csv.DictReader(data.decode("utf-8-sig").splitlines()))
    keep = [row for row in rows if row["Area"] == "World" and row["Year"] in {"2024", "2025"}]
    keep.sort(key=lambda row: (row["Year"], row["Electricity source"]))
    return keep


def extract_chart(data: bytes, identifier: str) -> str:
    text = data.decode("utf-8")
    pattern = rf'data-chart-identifier="{re.escape(identifier)}".*?data-chart-csv="(.*?)"'
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"chart data not found: {identifier}")
    return html.unescape(match.group(1))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    fetched_at = datetime.now(timezone.utc).isoformat()
    ember = get(EMBER_URL)
    generation_html = get(IEA_GENERATION_URL)
    change_html = get(IEA_CHANGE_URL)

    ember_rows = extract_ember(ember)
    write_csv(INPUT / "ember_world_2024_2025.csv", ember_rows, list(ember_rows[0]))
    write_bytes(INPUT / "iea_generation_by_source_2015_2025.csv", extract_chart(generation_html, "global-electricity-generation-by-source-2015-2025").encode())
    write_bytes(INPUT / "iea_annual_change_2024_2025.csv", extract_chart(change_html, "annual-change-in-global-electricity-generation-by-source-2024-2025").encode())

    ember_values = {
        (row["Year"], row["Electricity source"]): float(row["Generation (TWh)"])
        for row in ember_rows
    }
    ember_2024 = {source: value for (year, source), value in ember_values.items() if year == "2024"}
    ember_2025 = {source: value for (year, source), value in ember_values.items() if year == "2025"}
    ember_delta = {source: round(ember_2025[source] - ember_2024[source], 6) for source in ember_2025}

    def parse_semicolon_chart(path: Path) -> list[list[str]]:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return [line.split(";") for line in lines]

    iea_generation = parse_semicolon_chart(INPUT / "iea_generation_by_source_2015_2025.csv")
    iea_change = parse_semicolon_chart(INPUT / "iea_annual_change_2024_2025.csv")
    iea_gen_header = iea_generation[0]
    iea_gen = {row[0]: {field: float(value) for field, value in zip(iea_gen_header[1:], row[1:])} for row in iea_generation[1:]}
    iea_change_header = iea_change[0]
    iea_delta = {row[0]: {field: float(value) for field, value in zip(iea_change_header[1:], row[1:])} for row in iea_change[1:]}

    result = {
        "fetched_at_utc": fetched_at,
        "ember": {
            "2024_total_generation_twh": ember_2024["Total generation"],
            "2025_total_generation_twh": ember_2025["Total generation"],
            "demand_increment_twh": ember_delta["Demand"],
            "clean_increment_twh": ember_delta["Clean"],
            "clean_minus_demand_twh": round(ember_delta["Clean"] - ember_delta["Demand"], 6),
            "renewables_increment_twh": ember_delta["Renewables"],
            "nuclear_increment_twh": ember_delta["Nuclear"],
            "coal_increment_twh": ember_delta["Coal"],
            "gas_increment_twh": ember_delta["Gas"],
            "other_fossil_increment_twh": ember_delta["Other fossil"],
            "fossil_increment_twh": ember_delta["Fossil"],
            "note": "The current global CSV has no separate oil row; Ember says Other fossil is mostly oil in the report methodology.",
        },
        "iea_chart": {
            "generation_2024_twh": sum(iea_gen["2024"].values()),
            "generation_2025_twh": sum(iea_gen["2025"].values()),
            "renewables_increment_twh": sum(iea_delta[source]["2025"] for source in ["Solar PV", "Wind", "Hydro", "Other renewables"]),
            "nuclear_increment_twh": iea_delta["Nuclear"]["2025"],
            "low_emissions_increment_twh": round(sum(iea_delta[source]["2025"] for source in ["Solar PV", "Wind", "Hydro", "Other renewables", "Nuclear"]), 6),
            "coal_increment_twh": iea_delta["Coal"]["2025"],
            "gas_increment_twh": iea_delta["Natural gas"]["2025"],
            "oil_increment_twh": iea_delta["Oil"]["2025"],
            "fossil_increment_twh": round(sum(iea_delta[source]["2025"] for source in ["Coal", "Natural gas", "Oil"]), 6),
            "source_note": "IEA chart values are the public CC BY 4.0 chart table embedded in the page; the separate report text describes demand growth as around 800 TWh.",
        },
        "input_sha256": {
            "ember_download": sha256(ember),
            "ember_filtered": sha256((INPUT / "ember_world_2024_2025.csv").read_bytes()),
            "iea_generation_chart_html": sha256(generation_html),
            "iea_change_chart_html": sha256(change_html),
        },
    }
    (OUTPUT / "recomputed_metrics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (OUTPUT / "download-manifest.json").write_text(json.dumps({
        "fetched_at_utc": fetched_at,
        "sources": [
            {"url": EMBER_URL, "bytes": len(ember), "sha256": sha256(ember)},
            {"url": IEA_GENERATION_URL, "bytes": len(generation_html), "sha256": sha256(generation_html)},
            {"url": IEA_CHANGE_URL, "bytes": len(change_html), "sha256": sha256(change_html)},
        ],
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
