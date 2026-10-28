from pathlib import Path
import stat
import tempfile
import unittest

from agent_federation.live_adapters import LiveAdapterError, LiveCodexAdapter
from agent_federation.live_bridge import LIVE_DISPATCH_SCHEMA, LiveDispatchEnvelope
from agent_federation.live_transport import RuntimeScratchLease, LiveTransportError


def envelope() -> LiveDispatchEnvelope:
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA,
        task_id="IGNITION-20260824-138",
        dispatch_id="d-138-matrix",
        attempt_id="a-138-matrix",
        executor_id="external.codex",
        adapter_id="codex-live-r3",
        capability_id="live.readonly.synthetic",
        capability_lease_ref="lease-138-matrix",
        workspace_ref="DISPOSABLE_FIXTURE_ROOT",
        workspace_mode="DISPOSABLE_SYNTHETIC_READ_ONLY",
        permission_ceiling=("repo.read",),
        side_effect_class="READ_ONLY_SYNTHETIC",
        network_class="INFERENCE_TRANSPORT_ONLY",
        intent_capsule_ref=None,
        synthetic_input_ref="fixture://IGNITION-20260824-138",
        synthetic_input_digest="c" * 64,
        success_criteria=("return the exact synthetic result",),
        output_contract={"format": "json", "required_fields": ["nonce"]},
        deadline="2026-08-24T12:00:00Z",
        timeout_seconds=10,
        retry_policy="NO_BLIND_RETRY",
        reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT",
        budget_authority="NO_NEW_BILLING_AUTHORITY",
        provenance={"controller": "pointfire-os"},
    )


class NeverSpawnTransport:
    supports_runtime_scratch = True

    def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None, runtime_scratch=None, runtime_env_keys=()):
        raise AssertionError("the adversarial preflight must reject before process start")


class LiveCodexSafetyMatrixTests(unittest.TestCase):
    def _layout(self, root: Path, *, reserved_parent: Path | None = None):
        workspace = root / "workspace"
        formal = root / "formal"
        control = root / "control"
        documents = root / "documents"
        parent = reserved_parent or root / "runtime-parent"
        workspace.mkdir()
        formal.mkdir()
        control.mkdir()
        documents.mkdir()
        parent.mkdir(parents=True)
        (workspace / "fixture.txt").write_text("read-only\n", encoding="utf-8")
        (workspace / "fixture.txt").chmod(0o444)
        workspace.chmod(0o555)
        return workspace, formal, control, documents, parent

    def _adapter(self, workspace: Path, formal: Path, control: Path, documents: Path, parent: Path) -> LiveCodexAdapter:
        return LiveCodexAdapter(
            workspace,
            transport=NeverSpawnTransport(),
            authentication_observed=True,
            adapter_id="codex-live-r3",
            runtime_scratch_parent=parent,
            formal_repo=formal,
            control_repo=control,
            persistent_user_document_roots=(documents,),
        )

    def test_workspace_writable_is_rejected_and_never_spawned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace, formal, control, documents, parent = self._layout(root)
            workspace.chmod(0o755)
            with self.assertRaises(LiveAdapterError):
                self._adapter(workspace, formal, control, documents, parent).dispatch(envelope())
            self.assertEqual(tuple(parent.iterdir()), ())

    def test_scratch_parent_inside_workspace_formal_or_control_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace, formal, control, documents, _ = self._layout(root, reserved_parent=root / "workspace" / "scratch-parent")
            with self.assertRaises(LiveAdapterError):
                self._adapter(workspace, formal, control, documents, root / "workspace" / "scratch-parent").dispatch(envelope())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace, formal, control, documents, _ = self._layout(root, reserved_parent=root / "formal" / "scratch-parent")
            with self.assertRaises(LiveAdapterError):
                self._adapter(workspace, formal, control, documents, root / "formal" / "scratch-parent").dispatch(envelope())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace, formal, control, documents, _ = self._layout(root, reserved_parent=root / "control" / "scratch-parent")
            with self.assertRaises(LiveAdapterError):
                self._adapter(workspace, formal, control, documents, root / "control" / "scratch-parent").dispatch(envelope())

    def test_symlink_scratch_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            link = root / "scratch-link"
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(LiveTransportError):
                RuntimeScratchLease.from_existing(link, attempt_id="attempt-symlink", protected_roots=())

    def test_read_only_task_permission_ceiling_and_safe_argv_remain_narrow(self):
        from tests.test_live_codex_adapter import FakeTransport, envelope as r2_envelope

        with tempfile.TemporaryDirectory() as directory:
            adapter = LiveCodexAdapter(directory, transport=FakeTransport(), authentication_observed=True)
            argv = adapter.build_argv(r2_envelope(Path(directory)))
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", argv)
        self.assertNotIn("workspace-write", argv)
        self.assertNotIn("--add-dir", argv)
        self.assertIn("--sandbox", argv)
        self.assertIn("read-only", argv)
        self.assertEqual(r2_envelope(Path("/tmp/disposable")).permission_ceiling, ("repo.read",))
        with self.assertRaises(LiveAdapterError):
            adapter._assert_safe_argv((adapter.executable, "exec", "--dangerously-bypass-approvals-and-sandbox"))


if __name__ == "__main__":
    unittest.main()
