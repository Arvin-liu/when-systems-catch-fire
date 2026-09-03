#!/usr/bin/env python3
"""Regression tests for the stable Task150-derived homepage projection."""

from __future__ import annotations

import unittest

from tools.validate_homepage_architecture_projection import (
    PUBLISHED_SVG_SHA256,
    TASK150_HTML_SHA256,
    TASK150_SVG_SHA256,
    ROOT,
    _standalone_svg_bytes,
    sha256_bytes,
    validate,
)


class HomepageArchitectureProjectionTests(unittest.TestCase):
    def test_stable_homepage_projection_is_current_and_displayed(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["source_unchanged_from_formal_main"])
        self.assertTrue(result["homepage_display_verified"])
        self.assertEqual(result["default_renderer"], "NOT_SELECTED")
        self.assertEqual(result["agent_reach"], "NO_CHANGE")
        self.assertEqual(result["svg"]["nodes"], result["html"]["nodes"])
        self.assertEqual(result["svg"]["edges"], result["html"]["edges"])

    def test_published_svg_is_a_bounded_packaging_of_the_task150_svg(self) -> None:
        source = (ROOT / "data/operations/iterations/150/derived-artifacts/task150-current-architecture.svg").read_bytes()
        published = (ROOT / "docs/generated/ignition-system-architecture.svg").read_bytes()
        html = (ROOT / "docs/generated/ignition-system-architecture.html").read_bytes()
        self.assertEqual(sha256_bytes(source), TASK150_SVG_SHA256)
        self.assertEqual(sha256_bytes(published), PUBLISHED_SVG_SHA256)
        self.assertEqual(sha256_bytes(html), TASK150_HTML_SHA256)
        self.assertEqual(_standalone_svg_bytes(source), published)
        self.assertNotIn(b"iterations/150/", published)
        self.assertNotIn(b"iterations/150/", html)


if __name__ == "__main__":
    unittest.main()
