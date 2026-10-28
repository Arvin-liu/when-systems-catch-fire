#!/usr/bin/env python3
"""Refresh the bounded Human Surface materiality projection after registry changes.

This keeps the hand-written reading contract and README structure intact.  It
only refreshes machine fingerprints/counts, removes entries whose canonical
record was withdrawn from the current projection, and records those withdrawn
presentation entries in the manifest for provenance.  It never changes a
claim, permission, epistemic status, or source text.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data/governance/human-surface/materiality-manifest.json"
FUNCTION_REGISTRY = ROOT / "data/foundation/function-assets/census.jsonl"
NONFUNCTION_REGISTRY = ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl"
FUNCTION_README = ROOT / "docs/human/function-assets/README.md"
FUNCTION_BULK = ROOT / "docs/human/function-assets/bulk-explanation.md"
NONFUNCTION_README = ROOT / "docs/human/nonfunction-assets/README.md"
NONFUNCTION_BULK = ROOT / "docs/human/nonfunction-assets/bulk-explanation.md"
NONFUNCTION_THEME = ROOT / "docs/human/nonfunction-assets/themes/withdrawals-history-and-boundaries.md"
NONFUNCTION_THEME_INDEX = ROOT / "docs/human/nonfunction-assets/themes/README.md"


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> dict[str, dict]:
    return {row.get("stable_id") or row.get("canonical_id"): row for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())}


def replace_machine_hash(text: str, digest: str) -> str:
    pattern = r"(机器记录指纹：`)[0-9a-f]+(`)"
    updated, count = re.subn(pattern, rf"\g<1>{digest}\g<2>", text, count=1)
    if count != 1:
        raise ValueError("human entry lacks exactly one machine record fingerprint")
    return updated


def refresh_count_text(text: str, machine_count: int, human_count: int, noun: str) -> str:
    text = re.sub(r"机器记录规模：\*\*\d+\*\* 条；独立人话说明：\*\*\d+\*\* 条", f"机器记录规模：**{machine_count}** 条；独立人话说明：**{human_count}** 条", text)
    text = re.sub(rf"当前机器记录中有 \*\*\d+\*\* 条{noun}，其中 \*\*\d+\*\* 条", f"当前机器记录中有 **{machine_count}** 条{noun}，其中 **{human_count}** 条", text)
    remaining = machine_count - human_count
    text = re.sub(rf"其余 \*\*\d+\*\* 条仍保留在机器 registry 中", f"其余 **{remaining}** 条仍保留在机器 registry 中", text)
    return text


def refresh_theme_index(text: str, theme_path: Path) -> str:
    lines = text.splitlines()
    updated: list[str] = []
    for line in lines:
        match = re.match(r"(- \[[^]]+\]\(([^)]+)\)：)\d+( 条人话说明)$", line)
        if match:
            target = theme_path.parent / match.group(2)
            count = len(re.findall(r"\[打开人话说明\]", target.read_text(encoding="utf-8"))) if target.is_file() else 0
            line = f"{match.group(1)}{count} 条人话说明"
        updated.append(line)
    return "\n".join(updated) + "\n"


def build() -> tuple[dict[Path, str], list[Path], dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    functions = read_jsonl(FUNCTION_REGISTRY)
    claims = read_jsonl(NONFUNCTION_REGISTRY)
    registries = {"FUNCTION_ASSET": functions, "NONFUNCTION_ASSET": claims}
    kept_entries: list[dict] = []
    withdrawn = list(manifest.get("withdrawn_entries", []))
    withdrawn_ids = {entry.get("machine_id") for entry in withdrawn}
    rendered: dict[Path, str] = {}
    delete_paths: list[Path] = []

    for source_entry in manifest.get("entries", []):
        entry = copy.deepcopy(source_entry)
        row = registries[entry["asset_kind"]].get(entry["machine_id"])
        human_path = ROOT / entry["human_path"]
        if row is None:
            if entry["machine_id"] not in withdrawn_ids:
                withdrawn.append({
                    "asset_kind": entry["asset_kind"],
                    "human_path": entry["human_path"],
                    "machine_id": entry["machine_id"],
                    "machine_record_sha256": entry.get("machine_record_sha256"),
                    "source_path": entry.get("source_path"),
                    "source_sha256": entry.get("source_sha256"),
                    "withdrawal_reason": "PLATFORM_CODE_EXCLUDED",
                })
            delete_paths.append(human_path)
            continue
        digest = sha256_text(canonical(row))
        entry["machine_record_sha256"] = digest
        kept_entries.append(entry)
        rendered[human_path] = replace_machine_hash(human_path.read_text(encoding="utf-8"), digest)

    function_human = sum(entry["asset_kind"] == "FUNCTION_ASSET" for entry in kept_entries)
    nonfunction_human = sum(entry["asset_kind"] == "NONFUNCTION_ASSET" for entry in kept_entries)
    manifest["entries"] = kept_entries
    manifest["withdrawn_entries"] = withdrawn
    manifest["counts"] = {
        "function_human": function_human,
        "function_machine": len(functions),
        "nonfunction_human": nonfunction_human,
        "nonfunction_machine": len(claims),
    }
    rendered[MANIFEST] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"

    rendered[FUNCTION_README] = refresh_count_text(FUNCTION_README.read_text(encoding="utf-8"), len(functions), function_human, "函数资产")
    rendered[FUNCTION_BULK] = refresh_count_text(FUNCTION_BULK.read_text(encoding="utf-8"), len(functions), function_human, "函数资产")
    rendered[NONFUNCTION_README] = refresh_count_text(NONFUNCTION_README.read_text(encoding="utf-8"), len(claims), nonfunction_human, "非函数资产")
    rendered[NONFUNCTION_BULK] = refresh_count_text(NONFUNCTION_BULK.read_text(encoding="utf-8"), len(claims), nonfunction_human, "非函数资产")

    stale_names = {path.name for path in delete_paths}
    if stale_names:
        theme_text = NONFUNCTION_THEME.read_text(encoding="utf-8")
        for name in sorted(stale_names):
            theme_text = re.sub(rf"\n## [^\n]+\n\n它是一条[^\n]*\[打开人话说明\]\(\.\./entries/{re.escape(name)}\)\n", "\n", theme_text)
        rendered[NONFUNCTION_THEME] = theme_text
    theme_index = refresh_theme_index(NONFUNCTION_THEME_INDEX.read_text(encoding="utf-8"), NONFUNCTION_THEME_INDEX)
    if stale_names:
        theme_count = len(re.findall(r"\[打开人话说明\]", theme_text))
        theme_index = re.sub(
            r"(- \[撤回、历史与边界\]\(withdrawals-history-and-boundaries\.md\)：)\d+( 条人话说明)$",
            rf"\g<1>{theme_count} 条人话说明",
            theme_index,
            flags=re.MULTILINE,
        )
    rendered[NONFUNCTION_THEME_INDEX] = theme_index
    return rendered, delete_paths, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered, delete_paths, manifest = build()
    mismatches = [str(path.relative_to(ROOT)) for path, content in rendered.items() if not path.is_file() or path.read_text(encoding="utf-8") != content]
    missing_deletions = [str(path.relative_to(ROOT)) for path in delete_paths if path.exists()]
    stale_manifest_paths = [entry.get("human_path") for entry in manifest.get("withdrawn_entries", []) if (ROOT / entry.get("human_path", "")).exists()]
    if args.check:
        if mismatches or missing_deletions or stale_manifest_paths:
            print("HUMAN_SURFACE_MATERIALITY_DRIFT")
            for item in mismatches + missing_deletions + stale_manifest_paths:
                print(item)
            return 1
        print(f"HUMAN_SURFACE_MATERIALITY_DETERMINISTIC entries={len(manifest['entries'])} withdrawn={len(manifest.get('withdrawn_entries', []))}")
        return 0
    if args.write:
        for path, content in rendered.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        for path in delete_paths:
            if path.is_file():
                path.unlink()
        print(f"HUMAN_SURFACE_MATERIALITY_REFRESHED entries={len(manifest['entries'])} withdrawn={len(manifest.get('withdrawn_entries', []))}")
        return 0
    parser.error("choose --write or --check")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
