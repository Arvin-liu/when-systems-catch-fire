#!/usr/bin/env python3
"""Retired-name entry point for the single complete architecture generator.

The former hand-authored conceptual SVG is not generated anymore. This
entrypoint remains only so old validation commands fail over to the canonical,
relation-driven projection rather than silently recreating a second graph.
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
