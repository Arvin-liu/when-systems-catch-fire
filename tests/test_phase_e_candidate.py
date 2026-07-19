import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.operations.validate_phase_e_candidate import ROOT, validate


class PhaseECandidateTests(unittest.TestCase):
    def test_real_lifecycle_passes(self):
        result = validate()
        self.assertEqual(result["decision"], "FULL_REBUILD_REQUIRED")

    def test_lifecycle_inflation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            fixture = Path(td)
            for rel in ("data/operations/propagation/121Q32I-request.json", "reports/operations/121Q32I-incremental-execution-demonstration.json", "data/operations/iterations/121Q32I.json", "reports/operations/121Q32I-completion-seal.json", "docs/publication/works/when-an-army-believes-its-own-back.md", "data/operations/project-components.json", "data/operations/change-propagation-topology.json", "data/operations/component-execution-profiles.json"):
                target = fixture / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / rel).read_bytes())
            manifest_path = fixture / "data/operations/iterations/121Q32I.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["status"]["accepted"] = False
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "E_PHASE_E_LIFECYCLE"):
                validate(fixture)


if __name__ == "__main__":
    unittest.main()
