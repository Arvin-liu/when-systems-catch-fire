#!/usr/bin/env python3
"""Compatibility entry point for the registry-derived machine projection.

The homepage's stable public visualization is separately bound to the
Task150-verified standalone artifact by
``validate_homepage_architecture_projection.py``. This retired-name entrypoint
keeps older validation commands on the canonical registry projection without
creating a second authored architecture graph.
"""
from __future__ import annotations

import json

try:
    from tools.generate_interactive_system_map import (
        DEFAULT_OUTPUT as OUT,
        DEFAULT_SPEC as SPEC_PATH,
        build_projection,
        main as generate_main,
        render_svg,
        validate_spec,
    )
except ModuleNotFoundError:
    from generate_interactive_system_map import (
        DEFAULT_OUTPUT as OUT,
        DEFAULT_SPEC as SPEC_PATH,
        build_projection,
        main as generate_main,
        render_svg,
        validate_spec,
    )


def main() -> int:
    return generate_main()


if __name__ == "__main__":
    raise SystemExit(main())
