import json
from pathlib import Path
import stat
import tempfile
import unittest

from agent_federation.live_adapters import LiveAdapterError, LiveCodexAdapter
from agent_federation.live_bridge import LIVE_DISPATCH_SCHEMA, LiveDispatchEnvelope
from agent_federation.live_child_guard import CHILD_ENV_ALLOWLIST
from agent_federation.live_pilot import tree_digest
from agent_federation.live_transport import LiveProcessTransport


def envelope() -> LiveDispatchEnvelope:
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA,
        task_id="IGNITION-20260824-138",
        dispatch_id="d-138-r3",
        attempt_id="a-138-r3",
        executor_id="external.codex",
        adapter_id="codex-live-r3",
        capability_id="live.readonly.synthetic",
        capability_lease_ref="lease-138-r3",
        workspace_ref="DISPOSABLE_FIXTURE_ROOT",
        workspace_mode="DISPOSABLE_SYNTHETIC_READ_ONLY",
        permission_ceiling=("repo.read",),
        side_effect_class="READ_ONLY_SYNTHETIC",
        network_class="INFERENCE_TRANSPORT_ONLY",
        intent_capsule_ref=None,
        synthetic_input_ref="fixture://IGNITION-20260824-138",
        synthetic_input_digest="b" * 64,
        success_criteria=("return the exact synthetic result",),
        output_contract={"format": "json", "required_fields": ["nonce"]},
        deadline="2026-08-24T12:00:00Z",
        timeout_seconds=10,
        retry_policy="NO_BLIND_RETRY",
        reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT",
        budget_authority="NO_NEW_BILLING_AUTHORITY",
        provenance={"controller": "pointfire-os", "task": "138"},
    )


class LiveCodexRuntimeScratchTests(unittest.TestCase):
    def _fake_codex(self, path: Path) -> None:
        path.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "args = sys.argv[1:]\n"
            "if args == ['--version']:\n"
            "    print('codex-cli 0.144.4')\n"
            "elif args == ['exec', '--help']:\n"
            "    print('--json --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --sandbox --cd --output-schema')\n"
            "else:\n"
            "    assert args[0] == 'exec'\n"
            "    scratch = Path(os.environ['TMPDIR']).resolve()\n"
            "    assert Path(os.environ['HOME']).resolve() == scratch\n"
            "    assert Path(os.environ['CODEX_HOME']).resolve() == scratch / '.codex'\n"
            "    assert Path(os.environ['XDG_CACHE_HOME']).resolve() == scratch / '.cache'\n"
            "    assert Path(os.environ['XDG_CONFIG_HOME']).resolve() == scratch / '.config'\n"
            "    assert Path(os.environ['XDG_RUNTIME_DIR']).resolve() == scratch / '.runtime'\n"
            "    scratch.mkdir(exist_ok=True)\n"
            "    (scratch / 'helper-created-by-fake-codex').write_text('runtime-only')\n"
            "    (Path(os.environ['CODEX_HOME'])).mkdir(parents=True, exist_ok=True)\n"
            "    print(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': '{\\\"nonce\\\":\\\"r3\\\"}'}}))\n",
            encoding="utf-8",
        )
        path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    def test_r3_binds_codex_runtime_paths_without_widening_task_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "input.txt").write_text("fixture-138\n", encoding="utf-8")
            workspace.chmod(0o555)
            (workspace / "input.txt").chmod(0o444)
            scratch_parent = root / "runtime-parent"
            scratch_parent.mkdir()
            formal = root / "formal"
            control = root / "control"
            documents = root / "documents"
            formal.mkdir()
            control.mkdir()
            documents.mkdir()
            fake = root / "codex-fake"
            self._fake_codex(fake)
            before = tree_digest(workspace)
            adapter = LiveCodexAdapter(
                workspace,
                executable=str(fake),
                transport=LiveProcessTransport(
                    executable_allowlist=(str(fake),),
                    env_allowlist=CHILD_ENV_ALLOWLIST,
                ),
                authentication_observed=True,
                adapter_id="codex-live-r3",
                runtime_scratch_parent=scratch_parent,
                formal_repo=formal,
                control_repo=control,
                persistent_user_document_roots=(documents,),
            )

            observation = adapter.dispatch(envelope())

            self.assertTrue(observation.parsed)
            self.assertEqual(observation.runtime_scratch_cleanup_status, "CLEANED")
            self.assertEqual(observation.runtime_scratch_receipt["cleanup_status"], "CLEANED")
            self.assertFalse(observation.runtime_scratch_receipt["content_persisted"])
            self.assertNotEqual(
                observation.runtime_scratch_receipt["digest_before"],
                observation.runtime_scratch_receipt["digest_after"],
            )
            self.assertEqual(tree_digest(workspace), before)
            self.assertEqual(stat.S_IMODE(workspace.stat().st_mode), 0o555)
            self.assertEqual(stat.S_IMODE((workspace / "input.txt").stat().st_mode), 0o444)
            self.assertEqual(tuple(scratch_parent.iterdir()), ())
            self.assertIsNotNone(adapter.last_filesystem_domains)
            self.assertTrue(all(adapter.last_filesystem_domains.path_non_overlap_assertions.values()))
            self.assertFalse(adapter.last_filesystem_domains.auth_source_content_read)
            self.assertEqual(adapter.last_filesystem_domains.task_workspace_mode, "DISPOSABLE_READ_ONLY")
            self.assertEqual(adapter.last_filesystem_domains.runtime_scratch_mode, "ATTEMPT_EPHEMERAL_WRITABLE")

    def test_r3_refuses_transport_without_scratch_lifecycle_support(self):
        class NoScratchTransport:
            supports_runtime_scratch = False

            def run(self, argv, *, cwd, timeout_seconds, input_text=None, env_overrides=None):
                raise AssertionError("R3 must reject before invoking an unsupported transport")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            workspace.chmod(0o555)
            parent = root / "runtime-parent"
            parent.mkdir()
            formal = root / "formal"
            control = root / "control"
            documents = root / "documents"
            formal.mkdir()
            control.mkdir()
            documents.mkdir()
            adapter = LiveCodexAdapter(
                workspace,
                transport=NoScratchTransport(),
                authentication_observed=True,
                adapter_id="codex-live-r3",
                runtime_scratch_parent=parent,
                formal_repo=formal,
                control_repo=control,
                persistent_user_document_roots=(documents,),
            )
            with self.assertRaises(LiveAdapterError):
                adapter.dispatch(envelope())
            self.assertEqual(tuple(parent.iterdir()), ())


if __name__ == "__main__":
    unittest.main()
