#!/usr/bin/env python3
"""Run the exact R5-A pytest modules from the canonical Ignition app root."""
from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import pytest

if __name__ == "__main__":
    raise SystemExit(
        pytest.main([
            "-q",
            "tests/adaptive_relational_runtime/test_life_integrity_r5a.py",
            "tests/adaptive_relational_runtime/test_life_integrity_r5a_consolidated_repair.py",
        ])
    )
