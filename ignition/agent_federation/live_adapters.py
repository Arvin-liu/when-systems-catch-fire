"""Thin live adapters over already-installed public executor CLIs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import FederationContractError, canonical_json
from .live_child_guard import CHILD_ENV_ALLOWLIST, LiveChildContext, LiveChildGuardError, build_synthetic_child_prompt
from .live_bridge import LiveCapabilityLease, LiveDispatchEnvelope
from .live_filesystem import (
    AUTH_SOURCE_MODE,
    PATH_ASSERTION_KEYS,
    RUNTIME_ENV_REDACTION_POLICY,
    RUNTIME_SCRATCH_CLEANUP_POLICY,
    RUNTIME_SCRATCH_MODE,
    TASK_WORKSPACE_MODE,
    ExecutionFilesystemDomains,
)
from .live_pilot import tree_digest
from .live_transport import (
    LiveProcessResult,
    LiveProcessTransport,
    LiveTransportError,
    RuntimeScratchLease,
    RUNTIME_SCRATCH_CLEANED,
    interface_digest,
    parse_bounded_jsonl,
)


class LiveAdapterError(FederationContractError):
    """Raised when a live adapter cannot prove its public safety boundary."""


@dataclass(frozen=True)
class LiveAdapterObservation:
    executor_id: str
    adapter_id: str
    version: str
    interface_digest: str
    process: LiveProcessResult
    parsed_events: tuple[Mapping[str, Any], ...]
    parsed: bool
    parse_error: str
    summary: str
    response_digest: str | None
    session_pointer: str | None
    runtime_scratch_receipt: Mapping[str, Any] | None = None
    runtime_scratch_cleanup_status: str = "NOT_USED"


def _response_digest(text: str) -> str | None:
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None


def _summary(text: str) -> str:
    clean = " ".join(line.strip() for line in text.splitlines() if line.strip())
    return clean[-1000:] if clean else "public executor returned no summary"


def _session_pointer(events: Sequence[Mapping[str, Any]]) -> str | None:
    for event in events:
        value = event.get("thread_id") or event.get("session_id")
        if isinstance(value, str) and value.strip():
            return "opaque:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return None


def _binary_digest(executable: str, version: str) -> str:
    """Hash the observed executable when readable; never fall back to secrets."""

    try:
        path = Path(executable).resolve(strict=True)
        if path.is_file():
            return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        pass
    return hashlib.sha256(version.encode("utf-8")).hexdigest()


class LiveCodexAdapter:
    """Bounded Codex JSONL read-only adapter with optional R3 scratch separation."""

    executor_id = "external.codex"
    family = "Codex CLI"

    def __init__(
        self,
        workspace: str | Path,
        *,
        executable: str = "/Users/zhiyuan/.local/bin/codex",
        transport: LiveProcessTransport | Any | None = None,
        authentication_observed: bool = False,
        adapter_id: str = "codex-live-r2",
        child_context: LiveChildContext | None = None,
        runtime_scratch_required: bool | None = None,
        runtime_scratch_parent: str | Path | None = None,
        formal_repo: str | Path | None = None,
        control_repo: str | Path | None = None,
        persistent_user_document_roots: Sequence[str | Path] | None = None,
        auth_source_ref: str = "auth://existing-public-login-state",
    ) -> None:
        root = Path(workspace)
        if not root.is_absolute() or not root.is_dir():
            raise LiveAdapterError("Codex live adapter requires an existing absolute disposable workspace")
        if not isinstance(executable, str) or not executable.startswith("/"):
            raise LiveAdapterError("Codex executable must be an absolute path")
        self.workspace = root
        self.executable = executable
        self.transport = transport or LiveProcessTransport(executable_allowlist=(executable,), env_allowlist=CHILD_ENV_ALLOWLIST)
        self.authentication_observed = authentication_observed
        self.adapter_id = adapter_id
        self.child_context = child_context or LiveChildContext.from_environment()
        self.runtime_scratch_required = adapter_id == "codex-live-r3" if runtime_scratch_required is None else runtime_scratch_required
        if not isinstance(self.runtime_scratch_required, bool):
            raise LiveAdapterError("runtime_scratch_required must be boolean")
        self.runtime_scratch_parent = Path(runtime_scratch_parent).absolute() if runtime_scratch_parent is not None else None
        if self.runtime_scratch_parent is not None and (not self.runtime_scratch_parent.is_absolute() or not self.runtime_scratch_parent.is_dir()):
            raise LiveAdapterError("runtime scratch parent must be an existing absolute directory")
        self.formal_repo = Path(formal_repo or Path(__file__).resolve().parents[2]).resolve()
        self.control_repo = Path(control_repo or "/Users/zhiyuan/Agent 工作区/1111-sync").resolve()
        roots = persistent_user_document_roots
        if roots is None:
            candidates = (Path.home() / "Documents", Path.home() / "我的笔记", Path.home())
            roots = tuple(path for path in candidates if path.is_dir())[:2]
        self.persistent_user_document_roots = tuple(Path(path).resolve() for path in roots)
        if not self.persistent_user_document_roots:
            raise LiveAdapterError("persistent user document roots must contain an existing directory")
        self.auth_source_ref = auth_source_ref
        self.last_filesystem_domains: ExecutionFilesystemDomains | None = None
        self._probe_cache: tuple[LiveProcessResult, LiveProcessResult] | None = None

    def _run(
        self,
        argv: Sequence[str],
        timeout_seconds: float = 5,
        *,
        env_overrides: Mapping[str, str] | None = None,
        runtime_scratch: RuntimeScratchLease | None = None,
        runtime_env_keys: Sequence[str] = (),
    ) -> LiveProcessResult:
        try:
            if runtime_scratch is not None:
                if not getattr(self.transport, "supports_runtime_scratch", False):
                    raise LiveAdapterError("Codex R3 requires a transport with runtime scratch lifecycle support")
                return self.transport.run(
                    argv, cwd=self.workspace, timeout_seconds=timeout_seconds, env_overrides=env_overrides,
                    runtime_scratch=runtime_scratch, runtime_env_keys=runtime_env_keys,
                )
            return self.transport.run(argv, cwd=self.workspace, timeout_seconds=timeout_seconds, env_overrides=env_overrides)
        except (OSError, LiveTransportError) as exc:
            raise LiveAdapterError(f"Codex public process probe failed: {type(exc).__name__}") from exc

    def _probe(self) -> tuple[LiveProcessResult, LiveProcessResult]:
        if self._probe_cache is None:
            self._probe_cache = (
                self._run((self.executable, "--version")),
                self._run((self.executable, "exec", "--help")),
            )
        return self._probe_cache

    def _protected_roots(self) -> tuple[Path, ...]:
        roots = [self.workspace, self.formal_repo, self.control_repo, *self.persistent_user_document_roots]
        if not self.auth_source_ref.startswith("auth://"):
            roots.append(Path(self.auth_source_ref))
        return tuple(path.resolve() for path in roots)

    def _new_runtime_scratch(self, attempt_id: str) -> RuntimeScratchLease:
        try:
            return RuntimeScratchLease.create(
                attempt_id=attempt_id,
                parent=self.runtime_scratch_parent,
                protected_roots=self._protected_roots(),
            )
        except (OSError, LiveTransportError) as exc:
            raise LiveAdapterError(f"Codex runtime scratch could not be created: {type(exc).__name__}") from exc

    def _filesystem_domains(
        self,
        scratch: RuntimeScratchLease,
        *,
        workspace_before: str,
        workspace_after: str,
        scratch_after: str,
        validate_paths: bool,
    ) -> ExecutionFilesystemDomains:
        contract = ExecutionFilesystemDomains(
            task_workspace_ref=str(self.workspace.resolve()),
            task_workspace_mode=TASK_WORKSPACE_MODE,
            task_workspace_digest_before=workspace_before,
            task_workspace_digest_after=workspace_after,
            runtime_scratch_ref=str(scratch.path.resolve()),
            runtime_scratch_mode=RUNTIME_SCRATCH_MODE,
            runtime_scratch_owner=scratch.owner,
            runtime_scratch_ttl=scratch.ttl_seconds,
            runtime_scratch_cleanup_policy=RUNTIME_SCRATCH_CLEANUP_POLICY,
            runtime_scratch_digest_before=scratch.before_digest,
            runtime_scratch_digest_after=scratch_after,
            auth_source_ref=self.auth_source_ref,
            auth_source_mode=AUTH_SOURCE_MODE,
            auth_source_content_read=False,
            config_mutation_allowed=False,
            runtime_env_allowlist=tuple(CHILD_ENV_ALLOWLIST),
            runtime_env_redaction_policy=RUNTIME_ENV_REDACTION_POLICY,
            path_non_overlap_assertions={key: True for key in PATH_ASSERTION_KEYS},
            permission_non_escalation_assertion=True,
            runtime_scratch_persistence_declared=True,
            secret_materialization=False,
            unknown_filesystem_domains=(),
            formal_repo_ref=str(self.formal_repo),
            control_repo_ref=str(self.control_repo),
            persistent_user_document_roots=tuple(str(path) for path in self.persistent_user_document_roots),
        )
        try:
            return contract.validate_paths() if validate_paths else contract
        except FederationContractError as exc:
            raise LiveAdapterError(f"Codex filesystem domain contract failed: {exc}") from exc

    def observe_lease(self, *, lease_id: str, observed_at: str, expires_at: str, ttl_seconds: float) -> LiveCapabilityLease:
        version_result, help_result = self._probe()
        version = _summary(version_result.stdout or version_result.stderr)
        help_text = (help_result.stdout or "") + ("\n" + help_result.stderr if help_result.stderr else "")
        required_flags = ("--json", "--ephemeral", "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check", "--sandbox", "--cd", "--output-schema")
        missing = [flag for flag in required_flags if flag not in help_text]
        blockers: list[str] = []
        if version_result.returncode != 0 or not version:
            blockers.append("VERSION_PROBE_FAILED")
        if help_result.returncode != 0:
            blockers.append("HELP_PROBE_FAILED")
        blockers.extend("MISSING_PUBLIC_FLAG:" + flag for flag in missing)
        if not self.authentication_observed:
            blockers.append("AUTH_NOT_OBSERVED")
        eligibility = "ELIGIBLE_FOR_LIVE_READONLY" if not blockers else "SKIPPED_INTERFACE_UNSUPPORTED" if any(item.startswith(("MISSING_PUBLIC_FLAG", "HELP_PROBE", "VERSION_PROBE")) for item in blockers) else "SKIPPED_NOT_AUTHENTICATED"
        return LiveCapabilityLease.build(
            lease_id=lease_id, executor_id=self.executor_id, executor_version=version,
            observed_at=observed_at, expires_at=expires_at, ttl_seconds=ttl_seconds,
            binary_digest=_binary_digest(self.executable, version), interface_digest=interface_digest(help_text),
            observed_capabilities=("repo.read", "structured_progress") if not missing else ("repo.read",),
            forbidden_capabilities=("repo.write", "repo.test", "terminal.run", "browser.read", "browser.act", "web.read", "messaging.send", "subagents", "scheduler"),
            unknown_capabilities=(), workspace_semantics=(
                "EXPLICIT_DISPOSABLE_READ_ONLY_CWD_WITH_ATTEMPT_RUNTIME_SCRATCH"
                if self.runtime_scratch_required else "EXPLICIT_DISPOSABLE_READ_ONLY_CWD"
            ),
            approval_sandbox_semantics="CODEX_READ_ONLY_EPHEMERAL_IGNORE_USER_CONFIG_AND_RULES",
            structured_output_semantics="JSONL_PUBLIC_EVENTS_AND_OUTPUT_SCHEMA", timeout_supported=True, cancel_supported=True,
            resume_supported=False, live_eligibility=eligibility, eligibility_blockers=tuple(blockers),
            source="codex-public-cli-probe-r3-runtime-scratch" if self.runtime_scratch_required else "codex-public-cli-probe-r3",
        )

    def build_argv(self, envelope: LiveDispatchEnvelope) -> tuple[str, ...]:
        try:
            self.child_context.assert_spawn_allowed()
        except LiveChildGuardError as exc:
            raise LiveAdapterError(str(exc)) from exc
        if envelope.executor_id != self.executor_id or envelope.adapter_id != self.adapter_id:
            raise LiveAdapterError("Codex live envelope is not bound to this adapter")
        if envelope.workspace_mode not in {"DISPOSABLE_READ_ONLY", "DISPOSABLE_SYNTHETIC_READ_ONLY"}:
            raise LiveAdapterError("Codex live adapter accepts only disposable read-only workspaces")
        if envelope.side_effect_class != "READ_ONLY_SYNTHETIC" or envelope.permission_ceiling != ("repo.read",):
            raise LiveAdapterError("Codex live adapter refuses a widened side-effect or permission ceiling")
        try:
            prompt = build_synthetic_child_prompt(
                synthetic_input_ref=envelope.synthetic_input_ref,
                success_criteria=envelope.success_criteria,
                output_contract=envelope.output_contract,
            )
        except LiveChildGuardError as exc:
            raise LiveAdapterError(str(exc)) from exc
        if len(prompt.encode("utf-8")) > 32 * 1024:
            raise LiveAdapterError("Codex live synthetic prompt exceeds the bounded input")
        strict_output_schema = envelope.output_contract.get("strict_output_schema", False)
        if not isinstance(strict_output_schema, bool):
            raise LiveAdapterError("Codex output contract strict_output_schema must be boolean")
        argv_prefix = [
            self.executable, "exec", "--json", "--ephemeral", "--ignore-user-config", "--ignore-rules",
            "--skip-git-repo-check", "--sandbox", "read-only",
        ]
        if strict_output_schema:
            schema_ref = envelope.output_contract.get("schema_path")
            if not isinstance(schema_ref, str) or not schema_ref.startswith("/"):
                raise LiveAdapterError("strict Codex output contract requires an absolute disposable schema path")
            schema_path = Path(schema_ref).resolve()
            try:
                schema_path.relative_to(self.workspace.resolve())
            except ValueError:
                pass
            else:
                raise LiveAdapterError("strict Codex output schema must not be inside the fixture workspace")
            if not schema_path.is_file():
                raise LiveAdapterError("strict Codex output schema path must be an existing file")
            if schema_path.stat().st_mode & 0o222:
                raise LiveAdapterError("strict Codex output schema must be read-only")
            help_text = self._probe()[1].stdout or self._probe()[1].stderr
            if "--output-schema" not in help_text:
                raise LiveAdapterError("current Codex CLI does not expose --output-schema")
            argv_prefix.extend(("--output-schema", str(schema_path)))
        argv = tuple(argv_prefix + ["--cd", str(self.workspace), prompt])
        if any("dangerously" in item or item == "--add-dir" or "workspace-write" in item for item in argv):
            raise LiveAdapterError("unsafe Codex flag leaked into the live argv")
        return argv

    def dispatch(self, envelope: LiveDispatchEnvelope) -> LiveAdapterObservation:
        argv = self.build_argv(envelope)
        try:
            child = self.child_context.issue_child(self.workspace)
            child_env = child.child_environment()
        except LiveChildGuardError as exc:
            raise LiveAdapterError(str(exc)) from exc
        runtime_scratch: RuntimeScratchLease | None = None
        runtime_env_keys: tuple[str, ...] = ()
        workspace_before: str | None = None
        if self.runtime_scratch_required:
            workspace_before = tree_digest(self.workspace)
            runtime_scratch = self._new_runtime_scratch(envelope.attempt_id)
            try:
                runtime_env_keys = (
                    "HOME", "TMPDIR", "CODEX_HOME", "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_RUNTIME_DIR",
                )
                child_env.update(runtime_scratch.environment_overrides(runtime_env_keys))
                self._filesystem_domains(
                    runtime_scratch,
                    workspace_before=workspace_before,
                    workspace_after=workspace_before,
                    scratch_after=runtime_scratch.before_digest,
                    validate_paths=True,
                )
            except (OSError, LiveTransportError, LiveAdapterError) as exc:
                cleanup_status = runtime_scratch.cleanup()
                if cleanup_status != RUNTIME_SCRATCH_CLEANED:
                    raise LiveAdapterError("Codex runtime scratch preflight failed and cleanup was not proven") from exc
                raise
        try:
            process = self._run(
                argv,
                timeout_seconds=envelope.timeout_seconds,
                env_overrides=child_env,
                runtime_scratch=runtime_scratch,
                runtime_env_keys=runtime_env_keys,
            )
        except Exception:
            if runtime_scratch is not None and runtime_scratch.cleanup_status is None:
                runtime_scratch.cleanup()
            raise
        runtime_receipt = process.runtime_scratch_receipt
        runtime_cleanup_status = process.runtime_scratch_cleanup_status
        if runtime_scratch is not None:
            if not isinstance(runtime_receipt, Mapping):
                if runtime_scratch.cleanup_status is None:
                    runtime_scratch.cleanup()
                raise LiveAdapterError("Codex R3 process returned no runtime scratch receipt")
            if (
                runtime_receipt.get("runtime_scratch_ref") != "ATTEMPT_RUNTIME_SCRATCH"
                or runtime_receipt.get("attempt_id") != envelope.attempt_id
                or runtime_receipt.get("digest_before") != runtime_scratch.before_digest
                or runtime_receipt.get("cleanup_status") != RUNTIME_SCRATCH_CLEANED
                or runtime_receipt.get("content_persisted") is not False
                or runtime_cleanup_status != RUNTIME_SCRATCH_CLEANED
            ):
                raise LiveAdapterError("Codex R3 runtime scratch receipt did not prove clean ephemeral completion")
            scratch_after = runtime_receipt.get("digest_after")
            if not isinstance(scratch_after, str):
                raise LiveAdapterError("Codex R3 runtime scratch receipt omitted the metadata digest")
            workspace_after = tree_digest(self.workspace)
            assert workspace_before is not None
            self.last_filesystem_domains = self._filesystem_domains(
                runtime_scratch,
                workspace_before=workspace_before,
                workspace_after=workspace_after,
                scratch_after=scratch_after,
                validate_paths=False,
            )
        events: tuple[Mapping[str, Any], ...] = ()
        parsed = False
        parse_error = ""
        if (
            not process.timed_out
            and not process.output_truncated
            and process.stdout.strip()
            and (runtime_scratch is None or runtime_cleanup_status == RUNTIME_SCRATCH_CLEANED)
        ):
            try:
                events = parse_bounded_jsonl(process.stdout)
                parsed = True
            except LiveTransportError as exc:
                parse_error = str(exc)
        return LiveAdapterObservation(
            self.executor_id, self.adapter_id,
            _summary(self._probe()[0].stdout or self._probe()[0].stderr),
            self._probe()[1].stdout and interface_digest(self._probe()[1].stdout) or interface_digest(self._probe()[1].stderr),
            process, events, parsed, parse_error, _summary(process.stdout or process.stderr),
            _response_digest(process.stdout), _session_pointer(events),
            runtime_receipt, runtime_cleanup_status,
        )


class LiveHermesAdapter:
    """R2 adapter for Hermes' bounded safe one-shot text surface."""

    executor_id = "external.hermes"
    family = "Hermes Agent"

    def __init__(
        self,
        workspace: str | Path,
        *,
        executable: str = "/Users/zhiyuan/.local/bin/hermes",
        transport: LiveProcessTransport | Any | None = None,
        authentication_observed: bool = False,
        read_only_guard_observed: bool = False,
        adapter_id: str = "hermes-live-r2",
        provider: str = "openai-codex",
        model: str = "gpt-5.6-luna",
    ) -> None:
        root = Path(workspace)
        if not root.is_absolute() or not root.is_dir():
            raise LiveAdapterError("Hermes live adapter requires an existing absolute disposable workspace")
        if not isinstance(executable, str) or not executable.startswith("/"):
            raise LiveAdapterError("Hermes executable must be an absolute path")
        self.workspace = root
        self.executable = executable
        self.transport = transport or LiveProcessTransport(executable_allowlist=(executable,))
        self.authentication_observed = authentication_observed
        self.read_only_guard_observed = read_only_guard_observed
        self.adapter_id = adapter_id
        self.provider = provider
        self.model = model
        self._probe_cache: tuple[LiveProcessResult, LiveProcessResult] | None = None

    def _run(self, argv: Sequence[str], timeout_seconds: float = 5) -> LiveProcessResult:
        try:
            return self.transport.run(argv, cwd=self.workspace, timeout_seconds=timeout_seconds)
        except (OSError, LiveTransportError) as exc:
            raise LiveAdapterError(f"Hermes public process probe failed: {type(exc).__name__}") from exc

    def _probe(self) -> tuple[LiveProcessResult, LiveProcessResult]:
        if self._probe_cache is None:
            self._probe_cache = (self._run((self.executable, "--version")), self._run((self.executable, "--help")))
        return self._probe_cache

    def observe_lease(self, *, lease_id: str, observed_at: str, expires_at: str, ttl_seconds: float) -> LiveCapabilityLease:
        version_result, help_result = self._probe()
        version = _summary(version_result.stdout or version_result.stderr)
        help_text = (help_result.stdout or "") + ("\n" + help_result.stderr if help_result.stderr else "")
        required_flags = ("-z", "--safe-mode", "--ignore-user-config", "--ignore-rules", "--no-restore-cwd")
        missing = [flag for flag in required_flags if flag not in help_text]
        blockers: list[str] = []
        if version_result.returncode != 0 or not version:
            blockers.append("VERSION_PROBE_FAILED")
        if help_result.returncode != 0:
            blockers.append("HELP_PROBE_FAILED")
        blockers.extend("MISSING_PUBLIC_FLAG:" + flag for flag in missing)
        if not self.authentication_observed:
            blockers.append("AUTH_NOT_OBSERVED")
        if not self.read_only_guard_observed:
            blockers.append("READ_ONLY_FILESYSTEM_GUARD_NOT_OBSERVED")
        if any(item.startswith(("MISSING_PUBLIC_FLAG", "HELP_PROBE", "VERSION_PROBE")) for item in blockers):
            eligibility = "SKIPPED_INTERFACE_UNSUPPORTED"
        elif "AUTH_NOT_OBSERVED" in blockers:
            eligibility = "SKIPPED_NOT_AUTHENTICATED"
        elif "READ_ONLY_FILESYSTEM_GUARD_NOT_OBSERVED" in blockers:
            eligibility = "SKIPPED_UNSAFE_WORKSPACE_OR_CHANNEL_BOUNDARY"
        else:
            eligibility = "ELIGIBLE_FOR_LIVE_READONLY"
        return LiveCapabilityLease.build(
            lease_id=lease_id, executor_id=self.executor_id, executor_version=version,
            observed_at=observed_at, expires_at=expires_at, ttl_seconds=ttl_seconds,
            binary_digest=hashlib.sha256(version.encode("utf-8")).hexdigest(), interface_digest=interface_digest(help_text),
            observed_capabilities=("repo.read",), forbidden_capabilities=("repo.write", "repo.test", "terminal.run", "browser.read", "browser.act", "web.read", "messaging.send", "subagents", "scheduler"),
            unknown_capabilities=(), workspace_semantics="EXPLICIT_DISPOSABLE_CWD_WITH_READ_ONLY_FILESYSTEM_GUARD",
            approval_sandbox_semantics="HERMES_SAFE_MODE_IGNORE_USER_CONFIG_AND_RULES",
            structured_output_semantics="BOUNDED_SINGLE_JSON_TEXT_OBJECT", timeout_supported=True, cancel_supported=True,
            resume_supported=False, live_eligibility=eligibility, eligibility_blockers=tuple(blockers), source="hermes-public-cli-probe-r2",
        )

    def build_argv(self, envelope: LiveDispatchEnvelope) -> tuple[str, ...]:
        if envelope.executor_id != self.executor_id or envelope.adapter_id != self.adapter_id:
            raise LiveAdapterError("Hermes live envelope is not bound to this adapter")
        if envelope.workspace_mode not in {"DISPOSABLE_READ_ONLY", "DISPOSABLE_SYNTHETIC_READ_ONLY"} or envelope.side_effect_class != "READ_ONLY_SYNTHETIC" or envelope.permission_ceiling != ("repo.read",):
            raise LiveAdapterError("Hermes live adapter refuses a widened workspace, effect, or permission ceiling")
        prompt = "IGNITION_LIVE_SYNTHETIC_READONLY_TASK\n" + canonical_json({
            "task_id": envelope.task_id,
            "synthetic_input_ref": envelope.synthetic_input_ref,
            "success_criteria": list(envelope.success_criteria),
            "output_contract": dict(envelope.output_contract),
            "instruction": "Read only the disposable fixture. Do not write, delete, execute shell, use network, message, browse, or inspect private state. Return exactly one JSON object and no commentary.",
        })
        if len(prompt.encode("utf-8")) > 32 * 1024:
            raise LiveAdapterError("Hermes live synthetic prompt exceeds the bounded input")
        argv = (
            self.executable, "--safe-mode", "--ignore-user-config", "--ignore-rules", "--no-restore-cwd",
            "--provider", self.provider, "--model", self.model, "--reasoning", "low", "-z", prompt,
        )
        if any(item in {"--resume", "--continue", "--worktree", "--yolo", "--accept-hooks"} or item in {"gateway", "send", "message"} for item in argv):
            raise LiveAdapterError("unsafe Hermes session, worktree, approval, or channel flag leaked into live argv")
        return argv

    def dispatch(self, envelope: LiveDispatchEnvelope) -> LiveAdapterObservation:
        argv = self.build_argv(envelope)
        process = self._run(argv, timeout_seconds=envelope.timeout_seconds)
        events: tuple[Mapping[str, Any], ...] = ()
        parsed = False
        parse_error = ""
        if not process.timed_out and not process.output_truncated and process.stdout.strip():
            try:
                value = json.loads(process.stdout.strip())
                if not isinstance(value, dict):
                    raise ValueError("final response is not an object")
                events = (value,)
                parsed = True
            except (ValueError, json.JSONDecodeError) as exc:
                parse_error = f"Hermes final text is not the exact JSON contract: {exc}"
        version_result, help_result = self._probe()
        help_text = help_result.stdout or help_result.stderr
        return LiveAdapterObservation(
            self.executor_id, self.adapter_id, _summary(version_result.stdout or version_result.stderr), interface_digest(help_text),
            process, events, parsed, parse_error, _summary(process.stdout or process.stderr), _response_digest(process.stdout), None,
        )


class LiveOpenClawAdapter:
    """Safety probe for OpenClaw; refuses the current gateway-owned surface."""

    executor_id = "external.openclaw"
    family = "OpenClaw"

    def __init__(
        self,
        workspace: str | Path,
        *,
        executable: str = "/Users/zhiyuan/.local/bin/openclaw",
        transport: LiveProcessTransport | Any | None = None,
        adapter_id: str = "openclaw-live-r2",
    ) -> None:
        root = Path(workspace)
        if not root.is_absolute() or not root.is_dir():
            raise LiveAdapterError("OpenClaw safety probe requires an existing absolute disposable workspace")
        self.workspace = root
        self.executable = executable
        self.transport = transport or LiveProcessTransport(executable_allowlist=(executable,))
        self.adapter_id = adapter_id
        self._probe_cache: tuple[LiveProcessResult, LiveProcessResult] | None = None

    def _run(self, argv: Sequence[str], timeout_seconds: float = 5) -> LiveProcessResult:
        try:
            return self.transport.run(argv, cwd=self.workspace, timeout_seconds=timeout_seconds)
        except (OSError, LiveTransportError) as exc:
            raise LiveAdapterError(f"OpenClaw public process probe failed: {type(exc).__name__}") from exc

    def _probe(self) -> tuple[LiveProcessResult, LiveProcessResult]:
        if self._probe_cache is None:
            self._probe_cache = (self._run((self.executable, "--version")), self._run((self.executable, "agent", "--help")))
        return self._probe_cache

    def observe_lease(self, *, lease_id: str, observed_at: str, expires_at: str, ttl_seconds: float) -> LiveCapabilityLease:
        version_result, help_result = self._probe()
        version = _summary(version_result.stdout or version_result.stderr)
        help_text = (help_result.stdout or "") + ("\n" + help_result.stderr if help_result.stderr else "")
        blockers = [
            "MISSING_PUBLIC_DISPOSABLE_WORKSPACE_BINDING",
            "GATEWAY_OR_LOCAL_AGENT_SESSION_SURFACE_NOT_CHANNEL_OFF_PROVABLE",
            "NO_EXPLICIT_READ_ONLY_PERMISSION_CEILING",
            "MESSAGE_AND_CHANNEL_OPTIONS_PRESENT_IN_PUBLIC_AGENT_SURFACE",
        ]
        if version_result.returncode != 0:
            blockers.append("VERSION_PROBE_FAILED")
        if help_result.returncode != 0:
            blockers.append("HELP_PROBE_FAILED")
        return LiveCapabilityLease.build(
            lease_id=lease_id, executor_id=self.executor_id, executor_version=version,
            observed_at=observed_at, expires_at=expires_at, ttl_seconds=ttl_seconds,
            binary_digest=hashlib.sha256(version.encode("utf-8")).hexdigest(), interface_digest=interface_digest(help_text),
            observed_capabilities=(), forbidden_capabilities=("repo.read", "repo.write", "repo.test", "terminal.run", "browser.read", "browser.act", "web.read", "messaging.send", "subagents", "scheduler"),
            unknown_capabilities=("workspace.binding", "channel.disable", "read_only_permission", "daemon.persistence"),
            workspace_semantics="GATEWAY_OWNED_OR_CONFIGURED_WORKSPACE_NOT_DISPOSABLE",
            approval_sandbox_semantics="NOT_PROVEN_FROM_AGENT_HELP",
            structured_output_semantics="JSON_RESULT_ADVERTISED_BUT_BINDING_UNSAFE",
            timeout_supported=True, cancel_supported=False, resume_supported=False,
            live_eligibility="SKIPPED_UNSAFE_WORKSPACE_OR_CHANNEL_BOUNDARY", eligibility_blockers=tuple(blockers), source="openclaw-agent-help-safety-probe-r2",
        )

    def build_argv(self, envelope: LiveDispatchEnvelope) -> tuple[str, ...]:
        raise LiveAdapterError("OpenClaw live dispatch is refused until disposable workspace and channel-off boundary are publicly provable")

    def dispatch(self, envelope: LiveDispatchEnvelope) -> LiveAdapterObservation:
        raise LiveAdapterError("OpenClaw live dispatch is intentionally not attempted under the current safety lease")


__all__ = ["LiveAdapterError", "LiveAdapterObservation", "LiveCodexAdapter", "LiveHermesAdapter", "LiveOpenClawAdapter"]
