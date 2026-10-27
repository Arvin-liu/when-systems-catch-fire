#!/usr/bin/env python3
"""Build the minimal GitHub Pages payload for the public architecture viewer.

The viewer is an exact byte copy of the stable, provenance-bound HTML projection.
This builder does not regenerate the graph, invoke a provider, select a renderer,
or modify any repository source.  It only assembles a disposable Pages artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
MANIFEST_PATH = ROOT / "data/architecture/homepage-architecture-projection-r1.json"
STABLE_HTML_PATH = ROOT / "docs/generated/ignition-system-architecture.html"
STABLE_SVG_PATH = ROOT / "docs/generated/ignition-system-architecture.svg"
DEFAULT_OUTPUT_DIR = REPO_ROOT / ".tmp-pages/architecture-site"
EXPECTED_PUBLIC_URL = "https://arvin-liu.github.io/when-systems-catch-fire/architecture/"
EXPECTED_PAYLOAD_PATH = "architecture/index.html"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_manifest() -> dict[str, Any]:
    require(MANIFEST_PATH.is_file(), f"homepage projection manifest is missing: {MANIFEST_PATH}")
    value = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "homepage projection manifest must be an object")
    return value


def _validate_source_contract() -> tuple[dict[str, Any], bytes]:
    manifest = load_manifest()
    public = manifest.get("public_delivery")
    require(isinstance(public, dict), "homepage projection manifest lacks public_delivery")
    require(public.get("deployment") == "GITHUB_PAGES_ACTIONS", "Pages deployment contract drifted")
    require(public.get("repository") == "Arvin-liu/when-systems-catch-fire", "Pages repository contract drifted")
    require(public.get("route") == "/architecture/", "Pages architecture route drifted")
    require(public.get("expected_url") == EXPECTED_PUBLIC_URL, "Pages architecture URL drifted")
    require(public.get("payload_path") == EXPECTED_PAYLOAD_PATH, "Pages payload path drifted")
    require(public.get("identity") == "EXACT_BYTE_COPY_OF_STABLE_HTML", "Pages payload identity contract drifted")
    require(public.get("availability_status") == "AWAITING_PAGES_DEPLOYMENT_OBSERVATION", "Pages availability status must stay explicit")
    require(public.get("live_url") == EXPECTED_PUBLIC_URL, "Pages live URL provenance is missing")
    require(public.get("source_path") == "docs/generated/ignition-system-architecture.html", "Pages source path drifted")

    stable_html = STABLE_HTML_PATH.read_bytes()
    stable_svg = STABLE_SVG_PATH.read_bytes()
    published_html = manifest.get("published_outputs", {}).get("html", {})
    published_svg = manifest.get("published_outputs", {}).get("svg", {})
    require(sha256_bytes(stable_html) == published_html.get("sha256"), "stable HTML is not bound to the homepage manifest")
    require(len(stable_html) == published_html.get("bytes"), "stable HTML byte count is not bound to the homepage manifest")
    require(sha256_bytes(stable_svg) == published_svg.get("sha256"), "stable SVG is not bound to the homepage manifest")
    require(public.get("payload_sha256") == sha256_bytes(stable_html), "Pages payload digest is not bound to stable HTML")
    require(public.get("payload_bytes") == len(stable_html), "Pages payload byte count is not bound to stable HTML")
    require(b"iterations/150/" not in stable_html, "Pages payload contains an unstable iterations/150 route")
    require(b"addEventListener" in stable_html and b"data-edge-from" in stable_html, "Pages payload lacks viewer interaction behavior")
    return manifest, stable_html


def _write_site_landing(output_dir: Path) -> None:
    landing = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>点火整体架构</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, -apple-system, sans-serif; }
    body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #020617; color: #e2e8f0; }
    main { max-width: 42rem; padding: 3rem; }
    a { color: #67e8f9; }
  </style>
</head>
<body>
  <main>
    <h1>点火整体架构</h1>
    <p>这是点火的公共架构投影入口。</p>
    <p><a href="architecture/">打开交互式架构图</a></p>
  </main>
</body>
</html>
"""
    (output_dir / "index.html").write_text(landing, encoding="utf-8")


def build(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    _manifest, stable_html = _validate_source_contract()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    architecture_dir = output_dir / "architecture"
    architecture_dir.mkdir(parents=True, exist_ok=True)

    payload = architecture_dir / "index.html"
    payload.write_bytes(stable_html)
    _write_site_landing(output_dir)
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    actual = payload.read_bytes()
    require(sha256_bytes(actual) == sha256_bytes(stable_html), "Pages payload is not an exact byte copy of stable HTML")
    require(len(actual) == len(stable_html), "Pages payload byte count differs from stable HTML")
    return {
        "status": "PASS",
        "output_dir": str(output_dir),
        "payload": {
            "path": EXPECTED_PAYLOAD_PATH,
            "sha256": sha256_bytes(actual),
            "bytes": len(actual),
            "identity": "EXACT_BYTE_COPY_OF_STABLE_HTML",
        },
        "public_url": EXPECTED_PUBLIC_URL,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    result = build(args.output_dir)
    print(
        "ARCHITECTURE_PAGES_PAYLOAD_OK "
        f"output={result['output_dir']} "
        f"payload={result['payload']['path']} "
        f"sha256={result['payload']['sha256']} "
        f"bytes={result['payload']['bytes']} "
        f"url={result['public_url']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
