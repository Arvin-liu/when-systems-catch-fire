"""Keep the dedicated Q33 workflow connected to its human-front-door inputs."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from tools import validate_human_front_door as front_door
from tools import validate_homepage_architecture_projection as homepage_projection


IGNITION_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION_ROOT.parent
WORKFLOW = REPO_ROOT / ".github/workflows/q33-governance-validation.yml"


def _pull_request_paths() -> tuple[str, ...]:
    text = WORKFLOW.read_text(encoding="utf-8")
    pull_request = re.search(r"(?ms)^  pull_request:\n(.*?)(?=^  push:)", text)
    if pull_request is None:
        raise AssertionError("Q33 workflow has no pull_request trigger")
    paths = re.search(r"(?ms)^    paths:\n((?:^      - .+\n)+)", pull_request.group(1))
    if paths is None:
        raise AssertionError("Q33 pull_request trigger has no paths list")
    return tuple(re.findall(r"(?m)^      - ['\"]([^'\"]+)['\"]\s*$", paths.group(1)))


def _matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path.startswith(prefix + "/")
    return path == pattern


class Q33HumanSurfaceTriggerCoverageTests(unittest.TestCase):
    def test_human_front_door_inputs_trigger_q33(self) -> None:
        configured = _pull_request_paths()
        required = {
            path.relative_to(REPO_ROOT).as_posix()
            for path in (
                front_door.README,
                front_door.GUIDE,
                front_door.CURRENT_STATE,
                front_door.HUMAN_READING,
                front_door.AI_START,
                front_door.AI_HANDOFF,
                front_door.LLMS,
                front_door.SYSTEM_MAP_SPEC,
                front_door.SYSTEM_MAP_SVG,
                front_door.COMPONENT_REGISTRY,
                Path(front_door.__file__).resolve(),
                Path(homepage_projection.__file__).resolve(),
                IGNITION_ROOT / "tools/generate_interactive_system_map.py",
                IGNITION_ROOT / "tests/test_human_front_door.py",
                IGNITION_ROOT / "tests/test_human_visibility_gate.py",
                IGNITION_ROOT / "tests/test_current_surface_compiler.py",
                IGNITION_ROOT / "tests/test_homepage_architecture_projection.py",
                IGNITION_ROOT / "tests/fixtures/human-front-door-r3.json",
                IGNITION_ROOT / "tests/fixtures/ignition-operating-method/homepage-ai-first-r1.json",
                Path(__file__).resolve(),
            )
        }
        missing = sorted(
            path for path in required
            if not any(_matches(path, pattern) for pattern in configured)
        )
        self.assertEqual(missing, [], f"Q33 path filters omit human-front-door inputs: {missing}")
        self.assertIn("ignition/docs/human/**", configured)
        self.assertIn(
            "ignition/docs/governance/human-surface-editorial-contract.md",
            configured,
        )


if __name__ == "__main__":
    unittest.main()
