"""One-level child-context guard for bounded live executor attempts."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import FederationContractError, canonical_json


LIVE_CHILD_DEPTH_ENV = "POINTFIRE_LIVE_CHILD_DEPTH"
MAX_LIVE_CHILD_DEPTH = 1
CHILD_ENV_ALLOWLIST = (
    "PATH", "LANG", "LC_ALL", "TMPDIR", "HOME", "CODEX_HOME",
    "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_RUNTIME_DIR", LIVE_CHILD_DEPTH_ENV,
)


class LiveChildGuardError(FederationContractError):
    """Raised when a live child would inherit or create unsafe context."""


def _depth(value: Any) -> int:
    if value is None or value == "":
        return 0
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise LiveChildGuardError("live child depth marker must be an integer") from exc
    if parsed < 0:
        raise LiveChildGuardError("live child depth marker must not be negative")
    return parsed


@dataclass(frozen=True)
class LiveChildContext:
    """Minimal machine context that can cross into one synthetic child."""

    depth: int = 0
    workspace: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.depth, int) or isinstance(self.depth, bool) or self.depth < 0:
            raise LiveChildGuardError("live child depth must be a non-negative integer")
        if self.workspace is not None:
            root = Path(self.workspace)
            if not root.is_absolute() or not root.is_dir():
                raise LiveChildGuardError("live child workspace must be an existing absolute directory")
            object.__setattr__(self, "workspace", root)

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "LiveChildContext":
        values = environment if environment is not None else os.environ
        return cls(depth=_depth(values.get(LIVE_CHILD_DEPTH_ENV)))

    def assert_spawn_allowed(self) -> None:
        if self.depth >= MAX_LIVE_CHILD_DEPTH:
            raise LiveChildGuardError("live executor reentrancy guard rejected depth >= 1 child spawn")

    def issue_child(self, workspace: str | Path) -> "LiveChildContext":
        self.assert_spawn_allowed()
        root = Path(workspace)
        if not root.is_absolute() or not root.is_dir():
            raise LiveChildGuardError("child context requires an existing disposable workspace")
        return LiveChildContext(depth=self.depth + 1, workspace=root)

    def child_environment(self, base_environment: Mapping[str, str] | None = None) -> dict[str, str]:
        if self.depth != MAX_LIVE_CHILD_DEPTH or self.workspace is None:
            raise LiveChildGuardError("only a depth-one child may be materialized")
        base = base_environment if base_environment is not None else os.environ
        result: dict[str, str] = {}
        for key in ("PATH", "LANG", "LC_ALL", "CODEX_HOME"):
            value = base.get(key)
            if isinstance(value, str) and value:
                result[key] = value
        # HOME and temporary files point at the disposable workspace, never at
        # the parent user's home or a formal repository.
        result["HOME"] = str(self.workspace)
        result["TMPDIR"] = str(self.workspace)
        result[LIVE_CHILD_DEPTH_ENV] = str(self.depth)
        return result


def build_synthetic_child_prompt(
    *,
    synthetic_input_ref: str,
    success_criteria: Sequence[str],
    output_contract: Mapping[str, Any],
) -> str:
    """Render a prompt from fixture contract only; parent prompt is not an input."""

    if not isinstance(synthetic_input_ref, str) or not synthetic_input_ref.startswith("fixture://"):
        raise LiveChildGuardError("child prompt requires a synthetic fixture reference")
    if not isinstance(success_criteria, (list, tuple)) or not success_criteria or any(not isinstance(item, str) or not item.strip() for item in success_criteria):
        raise LiveChildGuardError("child prompt success criteria must be bounded text")
    if not isinstance(output_contract, Mapping):
        raise LiveChildGuardError("child prompt output contract must be an object")
    payload = {
        "synthetic_input_ref": synthetic_input_ref,
        "success_criteria": list(success_criteria),
        "output_contract": dict(output_contract),
        "instruction": "Read only the disposable synthetic fixture, using bounded read-only file inspection when needed. Do not write, delete, run commands with side effects, use network, message, browse, inspect private state, or spawn another Agent. Return only the requested public result.",
    }
    return "IGNITION_LIVE_CHILD_SYNTHETIC_READONLY_TASK\n" + canonical_json(payload)


__all__ = [
    "CHILD_ENV_ALLOWLIST", "LIVE_CHILD_DEPTH_ENV", "MAX_LIVE_CHILD_DEPTH", "LiveChildContext",
    "LiveChildGuardError", "build_synthetic_child_prompt",
]
