#!/usr/bin/env python3
"""Run the R5-A candidate's exact local contract gates from the Ignition root."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.validate_life_integrity_r5a_consolidated_repair import main as consolidated_main
from tools.validate_life_integrity_r5a_repair import main as narrow_main


def main() -> int:
    narrow_status = narrow_main()
    consolidated_status = consolidated_main()
    return 0 if narrow_status == 0 and consolidated_status == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
