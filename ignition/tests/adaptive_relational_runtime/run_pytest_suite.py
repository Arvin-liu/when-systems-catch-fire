#!/usr/bin/env python3
"""Run the bounded ARR pytest suite selected by component validation."""
from __future__ import annotations
import sys

import pytest

if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", "tests/adaptive_relational_runtime/"]))
