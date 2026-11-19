from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.markdown_document import strip_fenced_code  # noqa: E402
from tools.validate_human_front_door import validate_readme_structure  # noqa: E402


class ReadmeFrontDoorLocalTests(unittest.TestCase):
    def test_readme_front_door_structure_and_identity(self):
        readme = (REPO_ROOT / ".github/README.md").read_text(encoding="utf-8")
        validate_readme_structure(strip_fenced_code(readme))


if __name__ == "__main__":
    unittest.main()
