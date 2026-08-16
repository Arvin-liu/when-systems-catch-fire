from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Use the repository-qualified namespace.  The discovery suite also contains
# ``tests/foundation``; importing the tool as top-level ``foundation`` would
# therefore depend on module-discovery order and can resolve to the test
# package instead of the shared admission policy implementation.
from tools.foundation.knowledge_corpus_admission import admission_for_path


class KnowledgeCorpusAdmissionTests(unittest.TestCase):
    def test_platform_code_and_runtime_traces_are_not_auto_admitted(self) -> None:
        for path in (
            "agent_kernel/contracts.py",
            "agent_runtime/r1_runtime.py",
            "data/agent-runtime/pilots/r1-real-local/pilot-a-receipt.json",
            "schemas/agent-runtime/r1-run-state.schema.json",
            "tests/test_agent_runtime_r1.py",
            "tools/foundation/build_function_asset_census.py",
            ".github/workflows/foundation-validation.yml",
        ):
            admission = admission_for_path(path)
            self.assertEqual(admission.classification, "PLATFORM_CODE_EXCLUDED", path)
            self.assertFalse(admission.auto_discovery, path)

    def test_explicit_architecture_registration_is_narrow(self) -> None:
        registered = admission_for_path("docs/architecture/agent-runtime-r1.md")
        self.assertTrue(registered.explicit)
        self.assertTrue(registered.auto_discovery)
        unregistered = admission_for_path("packs/research/manifest.json")
        self.assertEqual(unregistered.classification, "KNOWLEDGE_SOURCE_EXPLICIT_ONLY")
        self.assertFalse(unregistered.auto_discovery)

    def test_historical_provenance_is_not_an_authority_upgrade(self) -> None:
        admission = admission_for_path("reports/operations/old-audit.md")
        self.assertEqual(admission.classification, "HISTORICAL_PROVENANCE_ONLY")
        self.assertTrue(admission.provenance_only)
        self.assertTrue(admission.auto_discovery)

    def test_current_projection_has_no_platform_only_rows(self) -> None:
        result = __import__("subprocess").run(
            ["python3", "tools/validate_knowledge_corpus_admission.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
