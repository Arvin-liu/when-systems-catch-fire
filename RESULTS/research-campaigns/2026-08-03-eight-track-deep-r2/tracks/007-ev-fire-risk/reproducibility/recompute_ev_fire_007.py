"""Recompute the public numerator/denominator rates audited in R2 track 007."""

from __future__ import annotations

import json
from pathlib import Path


ROWS = [
    {"jurisdiction": "Denmark", "year": 2023, "fires": 46, "stock": 332089, "published_rate": 1.7, "stock_timing": "end_year"},
    {"jurisdiction": "Denmark", "year": 2024, "fires": 50, "stock": 485000, "published_rate": 1.2, "stock_timing": "approx_end_year"},
    {"jurisdiction": "Denmark", "year": 2025, "fires": 62, "stock": 693000, "published_rate": 1.0, "stock_timing": "approx_end_year"},
    {"jurisdiction": "Sweden", "year": 2024, "fires": 40, "stock": 880958, "other_fires": 3060, "other_stock": 4096833, "published_rate": 0.45, "stock_timing": "end_year_in_traffic"},
]


def main() -> None:
    for row in ROWS:
        row["recomputed_rate_per_10000"] = row["fires"] / row["stock"] * 10000
        row["implied_stock_from_published_rate"] = row["fires"] / row["published_rate"] * 10000
        if "other_fires" in row:
            row["recomputed_other_rate_per_10000"] = row["other_fires"] / row["other_stock"] * 10000
    output = {
        "formula": "fires / stock * 10000",
        "warning": "published rates can use a different exposure timing; no age or mileage adjustment",
        "rows": ROWS,
    }
    destination = Path(__file__).parent / "output/official-rate-recalc.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
