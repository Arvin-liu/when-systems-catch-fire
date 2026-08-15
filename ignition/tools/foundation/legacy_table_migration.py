#!/usr/bin/env python3
"""Record and resolve the retired legacy function/case tables.

The two legacy directories are historical source inputs, not current human
navigation.  This module keeps a deterministic machine-side migration record
so the foundation census and claim registry can continue to replay the exact
source text after the directories are removed.  It deliberately does not
publish one Markdown page per archived source.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
GIT_ROOT = ROOT if (ROOT / ".git").is_dir() else REPO_ROOT
MANIFEST = ROOT / "data/foundation/migrations/legacy-table-migration.jsonl"
FUNCTION_ROOT = ROOT / "统一函数总表"
CASE_ROOT = ROOT / "统一案例总表"
CURRENT_COMMIT = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=GIT_ROOT, text=True).strip()


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def git_path(relative: str) -> str:
    return f"ignition/{relative}"


def git_blob(relative: str, commit: str = CURRENT_COMMIT) -> str:
    return subprocess.check_output(["git", "rev-parse", f"{commit}:{git_path(relative)}"], cwd=GIT_ROOT, text=True).strip()


def first_commit(relative: str) -> str:
    # The locked source commit is the reproducible provenance checkpoint for
    # this migration.  A per-file ancestry walk would make the archive
    # needlessly non-deterministic and costs more than the source audit.
    return CURRENT_COMMIT


def title_from_text(relative: str, text: str) -> str:
    frontmatter = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", text[:4000], re.MULTILINE)
    if frontmatter:
        return frontmatter.group(1).strip().strip("\"'")
    heading = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    if heading:
        return heading.group(1).strip()
    return Path(relative).stem


def legacy_id(relative: str, kind: str, view_rows: dict[str, dict]) -> str | None:
    if relative in view_rows:
        return view_rows[relative].get("id")
    name = Path(relative).name
    if name == "INDEX.md":
        return None
    if "Ψ₀" in name or "Ψ0" in name:
        return "Y1"
    if kind == "function":
        match = re.search(r"(?:MF-?\d+|[ATDNPY]\d+)", name, re.IGNORECASE)
        if not match:
            return None
        value = match.group(0).upper().replace("MF-", "MF")
        if value.startswith("MF"):
            return f"MF{int(value[2:])}"
        return value
    match = re.search(r"-C-(\d+)-", name)
    return f"C{int(match.group(1)):04d}" if match else None


def load_jsonl(relative: str) -> list[dict]:
    path = ROOT / relative
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def view_map(relative: str) -> dict[str, dict]:
    return {row["source"]: row for row in load_jsonl(relative) if row.get("source")}


def path_mentions(relative: str, files: tuple[str, ...]) -> list[str]:
    destinations: list[str] = []
    for file in files:
        path = ROOT / file
        if not path.is_file():
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if relative not in line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                row = {}
            identity = row.get("canonical_id") or row.get("entity_key") or row.get("id")
            suffix = f"#line-{line_no}"
            if identity:
                suffix = f"#{identity}"
            destinations.append(f"{file}{suffix}")
            break
    return destinations


def state_for(relative: str, kind: str, identifier: str | None, files: tuple[str, ...]) -> str:
    statuses: set[str] = set()
    if identifier:
        for file in files:
            path = ROOT / file
            if not path.is_file():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if relative not in line and identifier not in line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for key in ("final_disposition", "disposition", "status", "evidence_status", "provenance_status"):
                    value = row.get(key)
                    if isinstance(value, str):
                        statuses.add(value)
                    elif isinstance(value, dict):
                        statuses.update(str(item) for item in value.values() if isinstance(item, str))
    if statuses:
        return "PRESERVED_STATUS: " + ", ".join(sorted(statuses))
    return "HISTORICAL_SOURCE_ONLY" if Path(relative).name == "INDEX.md" else "PRESERVED_WITHOUT_STATUS_UPGRADE"


def encode_source(text: str) -> str:
    return base64.b64encode(gzip.compress(text.encode("utf-8"), mtime=0)).decode("ascii")


def decode_source(row: dict) -> str:
    encoded = row.get("archived_source_gzip_base64")
    if not encoded:
        return ""
    return gzip.decompress(base64.b64decode(encoded)).decode("utf-8")


def all_legacy_paths() -> list[tuple[str, str]]:
    return sorted(
        [(p.relative_to(ROOT).as_posix(), "function") for p in FUNCTION_ROOT.glob("*.md")]
        + [(p.relative_to(ROOT).as_posix(), "case") for p in CASE_ROOT.glob("*.md")]
    )


def current_or_archived_text(relative: str) -> str | None:
    path = ROOT / relative
    if path.is_file():
        return path.read_text(encoding="utf-8")
    for row in read_manifest():
        if row.get("legacy_path") == relative:
            return decode_source(row)
    return None


def migration_paths() -> list[str]:
    return sorted(row["legacy_path"] for row in read_manifest() if row.get("legacy_path"))


def read_manifest() -> list[dict]:
    if not MANIFEST.is_file():
        return []
    return [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]


def source_exists(relative: str) -> bool:
    return (ROOT / relative).is_file() or any(row.get("legacy_path") == relative for row in read_manifest())


def build_rows() -> list[dict]:
    function_views = view_map("views/legacy-functions.jsonl")
    case_views = view_map("views/legacy-cases.jsonl")
    destinations_by_kind = {
        "function": (
            "views/legacy-functions.jsonl",
            "data/foundation/formal-objects/objects.jsonl",
            "data/foundation/mappings/legacy-mappings.jsonl",
            "data/foundation/function-assets/identity-cards.jsonl",
            "data/foundation/nonfunction-claims/claim-registry.jsonl",
        ),
        "case": (
            "views/legacy-cases.jsonl",
            "data/foundation/evidence/evidence.jsonl",
            "data/foundation/nonfunction-claims/claim-registry.jsonl",
        ),
    }
    function_states = {
        row.get("canonical_id"): row.get("final_disposition")
        for row in load_jsonl("data/foundation/function-assets/identity-cards.jsonl")
        if row.get("canonical_id")
    }
    case_states = {
        row.get("canonical_id"): row.get("final_disposition")
        for row in load_jsonl("data/foundation/nonfunction-claims/claim-registry.jsonl")
        if row.get("canonical_id")
    }
    rows: list[dict] = []
    for relative, kind in all_legacy_paths():
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        views = function_views if kind == "function" else case_views
        identifier = legacy_id(relative, kind, views)
        # The explicit view rows and stable IDs below are the canonical
        # migration edges.  We intentionally do not scan every large JSONL
        # record once per source path.
        destinations: list[str] = []
        if identifier and kind == "function":
            destinations.extend([
                f"data/foundation/formal-objects/objects.jsonl#formal-object:{identifier}",
                f"data/foundation/function-assets/identity-cards.jsonl#{identifier}",
                "docs/human/function-assets/README.md#迁移后的函数资产",
            ])
        elif identifier and kind == "case":
            destinations.extend([
                f"data/foundation/evidence/evidence.jsonl#evidence:{identifier}",
                "docs/human/nonfunction-assets/README.md#案例与经验材料",
            ])
        if Path(relative).name == "INDEX.md":
            disposition = "HISTORICAL_ONLY"
            note = "旧索引只保留历史目录形状与当时计数；条目级信息由 canonical registry、迁移 manifest 与 Git 历史承接。"
        elif destinations:
            disposition = "FULLY_ABSORBED"
            note = "条目结构、身份、状态、来源锚点与机器映射已进入 canonical registry；人类入口按 materiality policy 汇总，不逐条复制旧 Markdown。"
        else:
            disposition = "PARTIALLY_ABSORBED"
            note = "已保留正文、blob、commit 与路径；尚无可安全宣称的单一 canonical 条目，继续作为历史来源保留。"
        status = (function_states if kind == "function" else case_states).get(identifier)
        if status:
            state = f"PRESERVED_STATUS: {status}"
        else:
            state = state_for(relative, kind, identifier, ())
        rows.append(
            {
                "schema_version": "1.0.0",
                "asset_kind": "LEGACY_FUNCTION_SOURCE" if kind == "function" else "LEGACY_CASE_SOURCE",
                "legacy_path": relative,
                "legacy_id": identifier,
                "title": title_from_text(relative, text),
                "git_blob_sha1": git_blob(relative),
                "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "first_seen_commit": first_commit(relative),
                "last_available_commit": CURRENT_COMMIT,
                "canonical_destinations": sorted(set(destinations)) or ["data/foundation/migrations/legacy-table-migration.jsonl"],
                "disposition": disposition,
                "transformation_note": note,
                "withdrawn_or_degraded_state": state,
                "deletion_status": "DELETED_AFTER_MIGRATION" if not (FUNCTION_ROOT.exists() or CASE_ROOT.exists()) else "PENDING_DELETION",
                "archived_source_gzip_base64": encode_source(text),
            }
        )
    return rows


def write_manifest() -> None:
    rows = build_rows() if (FUNCTION_ROOT.exists() or CASE_ROOT.exists()) else read_manifest()
    if not rows:
        raise SystemExit("legacy migration manifest cannot be built: no legacy sources or prior manifest")
    if not (FUNCTION_ROOT.exists() or CASE_ROOT.exists()):
        for row in rows:
            row["deletion_status"] = "DELETED_AFTER_MIGRATION"
    payload = "".join(canonical(row) + "\n" for row in sorted(rows, key=lambda row: row["legacy_path"]))
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(payload, encoding="utf-8")


def check_manifest() -> int:
    rows = read_manifest()
    if not rows:
        print("LEGACY_MIGRATION_MISSING")
        return 1
    expected = {row["legacy_path"] for row in rows}
    actual = {path for path, _ in all_legacy_paths()}
    if actual:
        print("LEGACY_MIGRATION_NOT_DELETED " + " ".join(sorted(actual)[:5]))
        return 1
    errors: list[str] = []
    for row in rows:
        if row.get("deletion_status") != "DELETED_AFTER_MIGRATION":
            errors.append(f"{row['legacy_path']}: deletion_status")
        if hashlib.sha256(decode_source(row).encode("utf-8")).hexdigest() != row.get("content_sha256"):
            errors.append(f"{row['legacy_path']}: content_sha256")
        try:
            blob = git_blob(row["legacy_path"], row["last_available_commit"])
        except subprocess.CalledProcessError:
            blob = ""
        if blob != row.get("git_blob_sha1"):
            errors.append(f"{row['legacy_path']}: git_blob_sha1")
        if not row.get("canonical_destinations"):
            errors.append(f"{row['legacy_path']}: canonical_destinations")
        if row.get("disposition") not in {"FULLY_ABSORBED", "PARTIALLY_ABSORBED", "HISTORICAL_ONLY", "CURRENT_DEPENDENCY"}:
            errors.append(f"{row['legacy_path']}: disposition")
    if errors:
        print("LEGACY_MIGRATION_INVALID " + " | ".join(errors[:8]))
        return 1
    print(f"LEGACY_MIGRATION_VALID files={len(rows)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return check_manifest()
    write_manifest()
    print(f"LEGACY_MIGRATION_WRITTEN files={len(read_manifest())} manifest={MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
