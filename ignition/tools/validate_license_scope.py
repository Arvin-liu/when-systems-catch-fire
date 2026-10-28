#!/usr/bin/env python3
"""Validate the 121Q9 layered license surface."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent


def read(path: str) -> str:
    repo_target = REPO_ROOT / path
    target = repo_target if repo_target.is_file() else ROOT / path
    return target.read_text(encoding="utf-8")


def tracked_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
    return [line for line in out.splitlines() if line]


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    root_license = read("LICENSE")
    licenses_readme = read("LICENSES/README.md")
    busl = read("LICENSES/active/BUSL-1.1.md")
    legacy_mit = read("LICENSES/legacy/MIT-pre-121Q9.md")
    readme = read(".github/README.md")

    check("root:layered_notice", "Layered License Notice" in root_license)
    check("root:not_single_mit", "MIT License\n\nCopyright" not in root_license)
    check("legacy:mit_preserved", legacy_mit.startswith("MIT License"))
    check("busl:change_date", "2030-07-15" in busl)
    check("busl:change_license", "AGPL-3.0-or-later" in busl)
    check("busl:source_available_not_osi", "not OSI open source" in busl)
    check("busl:standard_terms_present", "The Licensor hereby grants you the right to copy, modify, create derivative" in busl)
    check("busl:mariadb_notice_present", "License text copyright" in busl and "Business Source License" in busl and "MariaDB Corporation Ab" in busl)
    check("scope:docs_cc_nc_sa", "CC-BY-NC-SA-4.0" in read("docs/README.md"))
    check("scope:governance_cc_by_sa", "CC-BY-SA-4.0" in read("docs/governance/README.md"))
    check("scope:schemas_apache", "Apache-2.0" in read("schemas/README.md"))
    check("apache:complete_terms", "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION" in read("LICENSES/active/APACHE-2.0.md"))
    check("cc_nc_sa:complete_terms", "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International Public License" in read("LICENSES/active/CC-BY-NC-SA-4.0.md"))
    check("cc_by_sa:complete_terms", "Creative Commons Attribution-ShareAlike 4.0 International Public License" in read("LICENSES/active/CC-BY-SA-4.0.md"))
    check("scope:tools_busl", "LicenseRef-BUSL-1.1-PointFire" in read("tools/README.md"))
    check("readme:no_current_mit_claim", "本项目采用 MIT License" not in readme)
    check("readme:historical_mit_boundary", "历史 MIT" in readme)
    check("candidate:active_pointer", "active license scope" in read("LICENSES/candidate/README.md"))

    bad_cache = [
        p
        for p in tracked_files()
        if "__pycache__" in p
        or p.endswith((".pyc", ".pyo"))
        or p.endswith(".coverage")
        or "/.pytest_cache/" in p
    ]
    check("tracked:no_cache", not bad_cache, json.dumps(bad_cache[:10], ensure_ascii=False))

    forbidden = []
    for path in tracked_files():
        if path.startswith("LICENSES/legacy/"):
            continue
        if not path.endswith((".md", ".txt", ".toml", ".json", ".yml", ".yaml")):
            continue
        text = read(path)
        if "本项目采用 MIT License" in text or "project uses MIT" in text:
            forbidden.append(path)
    check("text:no_current_single_mit_claim", not forbidden, json.dumps(forbidden, ensure_ascii=False))

    for name, ok, detail in checks:
        print(("PASS" if ok else "FAIL"), name, detail)
    failed = [name for name, ok, _ in checks if not ok]
    result = {
        "checks_total": len(checks),
        "checks_failed": len(failed),
        "failed": failed,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
