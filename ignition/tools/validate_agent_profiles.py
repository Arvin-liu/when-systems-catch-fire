"""Validate the Agent Profile R1 registry and legal projection boundaries."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.profile import ProfileProjectionError, load_profile_registry, select_packs


PROFILE_PATH = ROOT / "data/agent-runtime/agent-profiles-r1.json"
REQUIRED = {"repository-maintainer", "bounded-researcher", "human-surface-writer"}
KERNEL_FORBIDDEN = {"agent_lifecycle", "checkpoint_resume", "executor_selection", "generic_permission", "kernel_definition", "owner_acceptance"}


def main() -> int:
    profiles = load_profile_registry(PROFILE_PATH)
    assert set(profiles) == REQUIRED
    for profile in profiles.values():
        assert profile.prohibited_self_escalation is True
        assert KERNEL_FORBIDDEN <= set(profile.prohibited_authority_upgrades)
        assert profile.update_authority == "owner-only"
    assert select_packs(profiles["repository-maintainer"], ("maintenance.repository", "knowledge.r0")) == ("knowledge.r0", "maintenance.repository")
    try:
        select_packs(profiles["bounded-researcher"], ("maintenance.repository",))
    except ProfileProjectionError:
        pass
    else:
        raise AssertionError("bounded-researcher selected a disallowed Pack")
    print("AGENT_PROFILE_R1_VALIDATOR=PASS")
    print("PROFILE_COUNT=3")
    print("SELF_ESCALATION=PROHIBITED")
    print("PACK_SELECTION=ALLOWLIST_ONLY")
    print("PROJECTION=PROFILE_CAN_ONLY_NARROW")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
