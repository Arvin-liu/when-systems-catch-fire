import subprocess
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_agent_platform_human_surface.py"


class AgentPlatformHumanSurfaceTests(unittest.TestCase):
    def test_human_surface_projection_is_consistent(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("AGENT_PLATFORM_HUMAN_SURFACE=PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
