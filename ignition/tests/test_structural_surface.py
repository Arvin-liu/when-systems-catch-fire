import json
import unittest

from tools.generate_structural_governance_surface import (
    CONTRACT,
    DEFAULT_JSON,
    DEFAULT_MD,
    GRAMMAR,
    IDENTITY,
    SCHEMA,
    build_surface,
    load,
    render_markdown,
    validate_surface,
)


class StructuralSurfaceTests(unittest.TestCase):
    def test_projection_is_schema_valid_and_complete(self):
        surface = load(DEFAULT_JSON)
        self.assertEqual([], validate_surface(surface, load(SCHEMA)))
        self.assertEqual({rule["stable_id"] for rule in load(GRAMMAR)["rules"]}, {item["stable_id"] for item in surface["items"]})
        self.assertEqual("ADVISORY_READING_SURFACE_NOT_PROMPT", surface["surface_role"])

    def test_json_and_markdown_are_deterministic(self):
        surface = build_surface(load(GRAMMAR), load(CONTRACT), load(IDENTITY))
        expected_json = (json.dumps(surface, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self.assertEqual(expected_json, DEFAULT_JSON.read_bytes())
        self.assertEqual(render_markdown(surface).encode("utf-8"), DEFAULT_MD.read_bytes())

    def test_surface_carries_hard_soft_boundary(self):
        text = DEFAULT_MD.read_text(encoding="utf-8")
        self.assertIn("不是提示词", text)
        self.assertIn("不能授权", text)
        self.assertIn("EPISTEMICALLY_ACCEPTED=0", text)


if __name__ == "__main__":
    unittest.main()
