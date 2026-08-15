#!/usr/bin/env python3
"""Standalone validation entrypoint for the R2 blast-radius report."""
from __future__ import annotations

import sys

try:
    from agent_platform_blast_radius import main
except ModuleNotFoundError:
    from tools.propagation.agent_platform_blast_radius import main


if __name__ == "__main__":
    raise SystemExit(main())
