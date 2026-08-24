from pathlib import Path
import hashlib
import json
import os
import stat
import tempfile
import unittest

from agent_federation.contracts import FederationContractError
from agent_federation.live_filesystem import (
    FILESYSTEM_DOMAINS_SCHEMA,
    PATH_ASSERTION_KEYS,
    ExecutionFilesystemDomains,
    empty_scratch_digest,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class LiveFilesystemTests(unittest.TestCase):
    def _contract(self, root: Path, **overrides) -> ExecutionFilesystemDomains:
        workspace = root / "workspace"
        scratch = root / "scratch"
        auth = root / "auth"
        formal = root / "formal"
        control = root / "control"
        persistent = root / "documents"
        for path in (workspace, scratch, auth, formal, control, persistent):
            path.mkdir(exist_ok=True)
        (workspace / "input.txt").write_text("input\n", encoding="utf-8")
        workspace.chmod(0o555)
        (workspace / "input.txt").chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        auth.chmod(0o555)
        values = {
            "task_workspace_ref": str(workspace),
            "task_workspace_mode": "DISPOSABLE_READ_ONLY",
            "task_workspace_digest_before": _digest("workspace-before"),
            "task_workspace_digest_after": _digest("workspace-after"),
            "runtime_scratch_ref": str(scratch),
            "runtime_scratch_mode": "ATTEMPT_EPHEMERAL_WRITABLE",
            "runtime_scratch_owner": "current-user",
            "runtime_scratch_ttl": 300,
            "runtime_scratch_cleanup_policy": "CLEANUP_FINALLY_FAIL_CLOSED",
            "runtime_scratch_digest_before": empty_scratch_digest(),
            "runtime_scratch_digest_after": empty_scratch_digest(),
            "auth_source_ref": str(auth),
            "auth_source_mode": "READ_ONLY_REFERENCE",
            "auth_source_content_read": False,
            "config_mutation_allowed": False,
            "runtime_env_allowlist": ("PATH", "HOME", "TMPDIR", "CODEX_HOME"),
            "runtime_env_redaction_policy": "PRESENCE_ONLY_REDACT_PATHS_NO_VALUES",
            "path_non_overlap_assertions": {key: True for key in PATH_ASSERTION_KEYS},
            "permission_non_escalation_assertion": True,
            "runtime_scratch_persistence_declared": True,
            "secret_materialization": False,
            "unknown_filesystem_domains": (),
            "formal_repo_ref": str(formal),
            "control_repo_ref": str(control),
            "persistent_user_document_roots": (str(persistent),),
        }
        values.update(overrides)
        return ExecutionFilesystemDomains(**values)

    def test_contract_validates_three_domains_and_redacts_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = self._contract(Path(directory))
            self.assertIs(contract.validate_paths(), contract)
            public = contract.to_dict(redact_paths=True)
            self.assertEqual(public["schema_version"], FILESYSTEM_DOMAINS_SCHEMA)
            self.assertEqual(public["runtime_scratch_ref"], "ATTEMPT_RUNTIME_SCRATCH")
            self.assertNotIn(directory, json.dumps(public))
            restored = ExecutionFilesystemDomains.from_dict(contract.to_dict())
            self.assertEqual(restored.runtime_scratch_mode, "ATTEMPT_EPHEMERAL_WRITABLE")

    def test_workspace_writable_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = self._contract(root)
            workspace = root / "workspace"
            workspace.chmod(0o755)
            with self.assertRaisesRegex(FederationContractError, "task workspace is writable"):
                contract.validate_paths()

    def test_scratch_overlap_and_protected_roots_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            contract = self._contract(root, runtime_scratch_ref=str(workspace))
            with self.assertRaises(FederationContractError):
                contract.validate_paths()
            workspace.chmod(0o755)
            (workspace / "input.txt").chmod(0o644)
            contract = self._contract(root, runtime_scratch_ref=str(root / "formal"))
            with self.assertRaises(FederationContractError):
                contract.validate_paths()

    def test_scratch_inside_control_or_persistent_tree_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scratch = root / "documents" / "scratch"
            scratch.mkdir(parents=True)
            contract = self._contract(root, runtime_scratch_ref=str(scratch))
            with self.assertRaises(FederationContractError):
                contract.validate_paths()

    def test_auth_source_must_be_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = self._contract(root)
            (root / "auth").chmod(0o755)
            with self.assertRaisesRegex(FederationContractError, "auth source is writable"):
                contract.validate_paths()

    def test_symlink_escape_and_unknown_domain_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            link = root / "linked-scratch"
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(FederationContractError):
                self._contract(root, runtime_scratch_ref=str(link)).validate_paths()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FederationContractError, "unknown filesystem domains"):
                self._contract(Path(directory), unknown_filesystem_domains=("UNKNOWN",))

    def test_secret_env_and_undeclared_persistence_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FederationContractError):
                self._contract(Path(directory), runtime_env_allowlist=("PATH", "AUTH_TOKEN"))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FederationContractError):
                self._contract(Path(directory), runtime_scratch_persistence_declared=False)

    def test_auth_reference_can_be_opaque_without_reading_content(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = self._contract(Path(directory), auth_source_ref="auth://existing-public-login-state")
            self.assertIs(contract.validate_paths(), contract)


if __name__ == "__main__":
    unittest.main()
