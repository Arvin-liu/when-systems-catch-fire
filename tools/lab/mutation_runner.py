#!/usr/bin/env python3
"""
Mutation Runner — second-pass deep audit
Applies real mutations to registry data, runs validators, asserts failures.

Usage:
    from tools.lab.mutation_runner import MutationTest

    mt = MutationTest("tools/rights/validate_rights_gate.py")
    mt.mutate_file("data/rights/source-rights-registry.json", mutated_content)
    result = mt.run_validator()
    mt.restore()
    assert not result.is_pass, "Validator should have caught the mutation"
"""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


class MutationTest:
    """Framework for testing whether validators detect real mutations."""

    def __init__(self, stage=""):
        self.root = ROOT
        self.stage = stage
        self._backups = {}  # path -> original content

    def mutate_file(self, rel_path, new_content):
        """Replace file content, saving original for restore."""
        full = self.root / rel_path
        if full not in self._backups:
            self._backups[full] = full.read_text(encoding="utf-8")
        if isinstance(new_content, (dict, list)):
            new_content = json.dumps(new_content, indent=2, ensure_ascii=False)
        full.write_text(new_content, encoding="utf-8")

    def restore(self):
        """Restore all mutated files to original content."""
        for path, content in self._backups.items():
            path.write_text(content, encoding="utf-8")
        self._backups.clear()

    def run_validator(self, validator_module, function_name="validate_all"):
        """Import and run a validator function, return the Result object."""
        import importlib
        mod = importlib.import_module(validator_module)
        fn = getattr(mod, function_name)
        return fn()

    def assert_catches(self, rel_path, mutated_doc, validator_module,
                       function_name="validate_all", description=""):
        """Mutate a file, run validator, assert it fails, then restore.
        Returns True if validator caught the mutation."""
        try:
            self.mutate_file(rel_path, mutated_doc)
            result = self.run_validator(validator_module, function_name)
            caught = not result.is_pass
            return caught, result
        finally:
            self.restore()


def load_json(rel_path):
    """Load a JSON file relative to ROOT."""
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))


def deep_copy(doc):
    return copy.deepcopy(doc)
