#!/usr/bin/env python3
"""Build the pre-migration root inventory and inbound-reference audit.

The audit is intentionally descriptive: it records what is at the repository
root, which entries are platform contracts, and where root-shaped references or
runtime assumptions occur.  It is not a second canonical registry and does not
decide semantic authority.
"""

from __future__ import annotations

import json
import re
import subprocess
import argparse
from collections import Counter
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError("repository root not found")


SCRIPT_ROOT = find_repo_root(Path(__file__).resolve())
PROJECT_ROOT = SCRIPT_ROOT / "ignition" if (SCRIPT_ROOT / "ignition").is_dir() else SCRIPT_ROOT
AUDIT_DIR = PROJECT_ROOT / "data/operations/root-normalization"

PLATFORM_RETAIN = {".github", ".gitignore", "AGENTS.md", "LICENSE"}
COMMUNITY_TO_GITHUB = {"CONTRIBUTING.md", "SUPPORT.md", "README.md"}
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".jsonl", ".csv", ".py", ".sh", ".yml", ".yaml",
    ".toml", ".ini", ".schema", ".svg", ".xml", ".html", ".js", ".ts",
}
SENSITIVE_PATH_PATTERNS = ("/Users/", "/tmp/", "file://")


def tracked_paths() -> list[str]:
    raw = subprocess.check_output(
        ["git", "-C", str(SCRIPT_ROOT), "ls-files", "-z"],
    )
    return sorted(item.decode("utf-8") for item in raw.split(b"\0") if item)


def git_head() -> str:
    return subprocess.check_output(
        ["git", "-C", str(SCRIPT_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()


def read_text(path: Path) -> str | None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def root_inventory(paths: list[str]) -> dict:
    entries = sorted(
        path.name
        for path in SCRIPT_ROOT.iterdir()
        if path.name != ".git"
    )
    rows = []
    for entry in entries:
        descendants = [path for path in paths if path == entry or path.startswith(entry + "/")]
        if entry in PLATFORM_RETAIN:
            action = "RETAIN_ROOT_PLATFORM_SHELL"
            destination = entry
            reason = "GitHub, Codex, license or ignore contract remains repository-root scoped."
        elif entry == "README.md":
            action = "MOVE_TO_GITHUB_REPOSITORY_LANDING"
            destination = ".github/README.md"
            reason = "GitHub officially surfaces a repository README from .github, root or docs; use the platform surface to keep the root shell minimal."
        elif entry in COMMUNITY_TO_GITHUB:
            action = "MOVE_TO_GITHUB_COMMUNITY_SURFACE"
            destination = f".github/{entry}"
            reason = "GitHub-supported community file; keep under the platform surface."
        else:
            action = "MOVE_TO_IGNITION_NAMESPACE"
            destination = f"ignition/{entry}"
            reason = "Ordinary project entity; move below the single project namespace."
        rows.append(
            {
                "entry": entry,
                "kind": "directory" if (SCRIPT_ROOT / entry).is_dir() else "file",
                "tracked_descendant_count": len(descendants),
                "tracked": bool(descendants),
                "action": action,
                "destination": destination,
                "reason": reason,
            }
        )
    return {
        "audit_version": "1.0.0",
        "audit_kind": "PRE_MIGRATION_ROOT_INVENTORY",
        "base_commit": git_head(),
        "repository_root_entries": rows,
        "root_entry_count": len(entries),
        "tracked_path_count": len(paths),
    }


def inbound_audit(paths: list[str]) -> dict:
    root_entries = sorted(
        path.name
        for path in SCRIPT_ROOT.iterdir()
        if path.name != ".git"
    )
    token_counts: Counter[str] = Counter()
    token_samples: dict[str, list[dict[str, object]]] = {}
    assumption_hits: list[dict[str, object]] = []
    absolute_hits: list[dict[str, object]] = []
    tokens = [token for token in root_entries if token not in {".gitignore", ".github"}]
    token_pattern = re.compile(
        r"(?<![A-Za-z0-9_.-])(?:" + "|".join(re.escape(token) for token in sorted(tokens, key=len, reverse=True)) + r")(?![A-Za-z0-9_.-])"
    )
    assumption_pattern = re.compile(
        r"Path\(__file__\)|os\.path\.dirname|parents\[\d+\]|git ls-files|cwd\s*=\s*ROOT|ROOT\s*/|README\.md"
    )
    text_files_scanned = 0
    for relative in paths:
        if relative.startswith("ignition/data/operations/root-normalization/"):
            continue
        text = read_text(SCRIPT_ROOT / relative)
        if text is None:
            continue
        text_files_scanned += 1
        lines = text.splitlines()
        for line_number, line in enumerate(lines, start=1):
            for match in token_pattern.finditer(line):
                token = match.group(0)
                token_counts[token] += 1
                bucket = token_samples.setdefault(token, [])
                if len(bucket) < 12:
                    bucket.append({"path": relative, "line": line_number, "excerpt": line[:240]})
            if assumption_pattern.search(line):
                if len(assumption_hits) < 5000:
                    assumption_hits.append({"path": relative, "line": line_number, "excerpt": line[:240]})
            if any(marker in line for marker in SENSITIVE_PATH_PATTERNS):
                if len(absolute_hits) < 5000:
                    absolute_hits.append({"path": relative, "line": line_number, "excerpt": line[:240]})
    return {
        "audit_version": "1.0.0",
        "audit_kind": "PRE_MIGRATION_INBOUND_REFERENCE_AUDIT",
        "base_commit": git_head(),
        "root_token_reference_line_counts": dict(sorted(token_counts.items())),
        "root_token_reference_samples": dict(sorted(token_samples.items())),
        "runtime_root_assumption_samples": assumption_hits,
        "sensitive_path_samples": absolute_hits,
        "tracked_text_files_scanned": text_files_scanned,
    }


def post_migration_inventory(paths: list[str]) -> dict:
    """Record the enforced five-entry root shell after the move."""
    entries = sorted(path.name for path in SCRIPT_ROOT.iterdir() if path.name != ".git")
    expected = [".github", ".gitignore", "AGENTS.md", "LICENSE", "ignition"]
    return {
        "audit_version": "1.0.0",
        "audit_kind": "POST_MIGRATION_ROOT_INVENTORY",
        "base_commit": git_head(),
        "repository_root_entries": entries,
        "expected_root_entries": expected,
        "root_entry_count": len(entries),
        "root_shell_ok": entries == expected,
        "tracked_path_count": len(paths),
        "namespace_descendant_count": sum(1 for path in paths if path.startswith("ignition/")),
        "ordinary_entities_outside_namespace": [
            path for path in entries if path not in {".github", ".gitignore", "AGENTS.md", "LICENSE", "ignition"}
        ],
    }


def post_migration_inbound_audit(paths: list[str]) -> dict:
    """Reuse the descriptive inbound scan with an explicit post-migration label."""
    result = inbound_audit(paths)
    result["audit_kind"] = "POST_MIGRATION_INBOUND_REFERENCE_AUDIT"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--post-migration", action="store_true")
    args = parser.parse_args()
    paths = tracked_paths()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    if args.post_migration:
        inventory = post_migration_inventory(paths)
        inbound = post_migration_inbound_audit(paths)
        (AUDIT_DIR / "post-migration-root-inventory.json").write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (AUDIT_DIR / "post-migration-inbound-reference-audit.json").write_text(
            json.dumps(inbound, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            "ROOT_NORMALIZATION_POST_AUDIT_OK "
            f"root_entries={inventory['root_entry_count']} "
            f"root_shell_ok={int(inventory['root_shell_ok'])} "
            f"outside_namespace={len(inventory['ordinary_entities_outside_namespace'])} "
            f"tracked_paths={inventory['tracked_path_count']}"
        )
        return 0
    inventory = root_inventory(paths)
    inbound = inbound_audit(paths)
    (AUDIT_DIR / "pre-migration-root-inventory.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (AUDIT_DIR / "pre-migration-inbound-reference-audit.json").write_text(
        json.dumps(inbound, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "ROOT_NORMALIZATION_AUDIT_OK "
        f"root_entries={inventory['root_entry_count']} "
        f"tracked_paths={inventory['tracked_path_count']} "
        f"text_files={inbound['tracked_text_files_scanned']} "
        f"root_tokens={len(inbound['root_token_reference_line_counts'])} "
        f"assumption_samples={len(inbound['runtime_root_assumption_samples'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
