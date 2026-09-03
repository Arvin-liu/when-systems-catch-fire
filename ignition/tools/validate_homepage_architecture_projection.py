#!/usr/bin/env python3
"""Validate the Task150-derived architecture projection published on the homepage.

The homepage projection is a public, derived visualization.  This validator
keeps its provenance separate from the registry-derived machine projection and
fails closed if the canonical authored source or the verified Task150 bytes
drift.  It deliberately does not invoke a provider or select a renderer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
MANIFEST_PATH = ROOT / "data/architecture/homepage-architecture-projection-r1.json"
CANONICAL_SOURCE_PATH = ROOT / "data/architecture/overall-architecture.json"
TASK150_STEP06_PATH = ROOT / "data/operations/iterations/150/step06-current-architecture-smoke.json"
TASK150_STEP21_PATH = ROOT / "data/operations/iterations/150/step21-fresh-standalone-evidence.json"
TASK150_STEP29_PATH = ROOT / "data/operations/iterations/150/step29-exact-head-ready-gate.json"
TASK150_SVG_PATH = ROOT / "data/operations/iterations/150/derived-artifacts/task150-current-architecture.svg"
TASK150_HTML_PATH = ROOT / "data/operations/iterations/150/standalone-evidence/task150-step21-standalone.html"
PUBLISHED_SVG_PATH = ROOT / "docs/generated/ignition-system-architecture.svg"
PUBLISHED_HTML_PATH = ROOT / "docs/generated/ignition-system-architecture.html"
README_PATH = REPO_ROOT / ".github/README.md"
SVG_NS = "http://www.w3.org/2000/svg"

FORMAL_MAIN_BASELINE = "8a95d393fbcae3de733f16e4b8f7e6c05e0d3a1b"
TASK150_SOURCE_REVISION = "68d5d30bda0d8eb9c715ac346ce6476a55c0e288"
CANONICAL_SOURCE_SHA256 = "251df5de786c53374e3bf0488d90a95983a47e452860f15922d9432ed6f17f13"
TASK150_SVG_SHA256 = "34d1da4c0ed795502f1eeef3af3d82e8872953422f9ea7ce5b48549424e57952"
TASK150_HTML_SHA256 = "da7947e408af2839e51fddc90871de30f84b1846ae1d14809a076a40d55daf45"
TASK150_EMBEDDED_SVG_SHA256 = "021219edc0457a719bc07fb96bb1e2a831fdeb49b8e8352e9818b369400e1414"
PUBLISHED_SVG_SHA256 = "a6261459164c2f1f8e0be289149197f81e7da4ae346db99b4c67e9dda6ce7c4b"
TASK150_STEP21_SHA256 = "2650dc6ab9f2a447d42f0e854e0fd3a2428f4b0d80c0ad10a78bbe2225fdb045"
TASK150_STEP29_SHA256 = "b4ccb76cf3b9b774a77c1a65ae3cd23479537d11c11c8f5de675a497c5ca642d"
EXPECTED_VIEWBOX = "0 0 1650 420"
EXPECTED_NODE_IDS = {
    "source-functions",
    "source-evidence",
    "source-history",
    "claim-foundation",
    "claim-functions",
    "claim-nonfunctions",
    "governance-charter",
    "governance-k13",
    "governance-state",
    "execution-iteration",
    "execution-reos",
    "execution-obligations",
    "validation-proof",
    "validation-evidence",
    "validation-provenance",
    "human-ai",
    "human-route",
    "human-browsers",
    "publication-book",
    "publication-seeds",
    "publication-writing",
    "navigation-map",
    "navigation-overall",
    "navigation-machine",
}
EXPECTED_EDGE_IDS = {f"canonical-edge-{index:02d}" for index in range(1, 25)}
README_IMAGE_TARGET = "../ignition/docs/generated/ignition-system-architecture.svg"
README_HTML_TARGET = "../ignition/docs/generated/ignition-system-architecture.html"
STANDALONE_SVG_CSS = b"""<style>
  :root {
    --bg: #020617; --grid: #1e293b; --text: #ffffff; --text-muted: #94a3b8;
    --mask: #0f172a; --frontend-fill: rgba(8, 51, 68, 0.4); --frontend-stroke: #22d3ee;
    --backend-fill: rgba(6, 78, 59, 0.4); --backend-stroke: #34d399;
    --cloud-stroke: #fbbf24; --security-stroke: #fb7185;
    --external-fill: rgba(30, 41, 59, 0.5); --external-stroke: #94a3b8;
    --arrow: #64748b; --arrow-emphasis: #34d399;
  }
  svg { background: var(--bg); font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, 'PingFang SC', 'Microsoft YaHei', monospace; }
  .c-grid { stroke: var(--grid); fill: none; }
  .c-mask { fill: var(--mask); stroke: none; }
  .c-region { fill: rgba(251, 191, 36, 0.05); stroke: var(--cloud-stroke); stroke-dasharray: 8,4; }
  .c-frontend { fill: var(--frontend-fill); stroke: var(--frontend-stroke); }
  .c-backend { fill: var(--backend-fill); stroke: var(--backend-stroke); }
  .c-security { fill: rgba(136, 19, 55, 0.4); stroke: var(--security-stroke); }
  .c-external { fill: var(--external-fill); stroke: var(--external-stroke); }
  .t-primary { fill: var(--text); } .t-muted { fill: var(--text-muted); }
  .t-frontend { fill: var(--frontend-stroke); } .t-backend { fill: var(--backend-stroke); }
  .t-cloud { fill: var(--cloud-stroke); } .t-security { fill: var(--security-stroke); }
  .t-external { fill: var(--external-stroke); }
  .a-default { stroke: var(--arrow); fill: none; }
  .m-default { fill: var(--arrow); } .m-emphasis { fill: var(--arrow-emphasis); }
  .m-security { fill: var(--security-stroke); }
  svg .semantic-sigil { fill: none; stroke: currentColor; stroke-width: 1.35; stroke-linecap: round; stroke-linejoin: round; opacity: 0.76; pointer-events: none; }
  svg .semantic-sigil > * { vector-effect: non-scaling-stroke; }
  svg .semantic-sigil .sigil-fill { fill: currentColor; stroke: none; }
  svg .s-frontend { color: var(--frontend-stroke); } svg .s-backend { color: var(--backend-stroke); }
  svg .s-security { color: var(--security-stroke); } svg .s-external { color: var(--external-stroke); }
  svg [data-detail="fine"] { opacity: 0; pointer-events: none; }
</style>"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    require(path.is_file(), f"required projection file is missing: {path}")
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"required provenance record is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"provenance record must be an object: {path}")
    return value


def is_split_repository_root(root: Path) -> bool:
    """Return whether ``root`` is the app root under the formal split repo shell."""
    candidate = root.parent / "ignition"
    # The production-profile fixture creates a convenience ``../ignition``
    # symlink back to its copied app root. That is still an app-only fixture,
    # not the formal split checkout, so do not classify symlinks as the shell.
    return not candidate.is_symlink() and candidate.resolve() == root.resolve()


def shell_root(root: Path) -> Path:
    """Resolve the shell root in both the formal split checkout and app-only fixtures."""
    return root.parent if is_split_repository_root(root) else root


def root_path(root: Path, relative: str) -> Path:
    """Resolve either ignition-relative or repository-relative evidence paths."""
    if relative.startswith("ignition/"):
        return root.parent / relative if is_split_repository_root(root) else root / relative.removeprefix("ignition/")
    return root / relative


def repo_relative(root: Path, path: Path) -> str:
    return path.relative_to(shell_root(root)).as_posix()


def git_root(root: Path) -> Path:
    """Find the Git root without confusing a copied app fixture with its parent."""
    return root if (root / ".git").exists() else root.parent


def git_check(root: Path, *args: str) -> tuple[bool, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=git_root(root),
        capture_output=True,
        text=True,
    )
    detail = (result.stdout + result.stderr).strip()
    return result.returncode == 0, detail


def _check_task150_provenance(root: Path, *, allow_missing_git_history: bool = False) -> dict[str, Any]:
    manifest = load_json(root_path(root, "ignition/data/architecture/homepage-architecture-projection-r1.json"))
    step06 = load_json(root_path(root, "ignition/data/operations/iterations/150/step06-current-architecture-smoke.json"))
    step21 = load_json(root_path(root, "ignition/data/operations/iterations/150/step21-fresh-standalone-evidence.json"))
    step29 = load_json(root_path(root, "ignition/data/operations/iterations/150/step29-exact-head-ready-gate.json"))

    source = root_path(root, manifest["canonical_source"]["path"])
    require(source == root_path(root, "data/architecture/overall-architecture.json"), "homepage manifest points at a non-canonical architecture source")
    source_sha = sha256_file(source)
    require(source_sha == CANONICAL_SOURCE_SHA256, "canonical architecture source digest differs from the Task150-verified digest")
    require(manifest["canonical_source"]["sha256"] == source_sha, "homepage manifest canonical-source digest is stale")
    require(manifest["canonical_source"]["task150_recorded_sha256"] == source_sha, "homepage manifest does not preserve the Task150 source digest")
    task150_artifacts = manifest["task150_verified_artifacts"]
    require(task150_artifacts["svg"]["path"] == "data/operations/iterations/150/derived-artifacts/task150-current-architecture.svg", "homepage manifest Task150 SVG path drifted")
    require(task150_artifacts["svg"]["sha256"] == TASK150_SVG_SHA256, "homepage manifest Task150 SVG digest drifted")
    require(task150_artifacts["html"]["path"] == "data/operations/iterations/150/standalone-evidence/task150-step21-standalone.html", "homepage manifest Task150 HTML path drifted")
    require(task150_artifacts["html"]["sha256"] == TASK150_HTML_SHA256, "homepage manifest Task150 HTML digest drifted")
    require(task150_artifacts["html"]["embedded_svg_sha256"] == TASK150_EMBEDDED_SVG_SHA256, "homepage manifest embedded SVG digest drifted")
    require(task150_artifacts["step21_receipt_sha256"] == TASK150_STEP21_SHA256, "homepage manifest Step21 receipt digest drifted")
    require(task150_artifacts["step29_receipt_sha256"] == TASK150_STEP29_SHA256, "homepage manifest Step29 receipt digest drifted")
    require(step21["canonical_source"]["path"] == "ignition/data/architecture/overall-architecture.json", "Task150 Step21 canonical source path drifted")
    require(step21["canonical_source"]["formal_source_revision"] == TASK150_SOURCE_REVISION, "Task150 Step21 source revision drifted")
    require(step21["canonical_source"]["sha256"] == source_sha, "Task150 Step21 source digest does not match current source")
    require(step21["canonical_source"]["read_before_and_after_hash_equal"] is True, "Task150 Step21 did not preserve read-before/read-after source immutability")
    require(step21["canonical_source"]["authority"] == "IGNITION_CANONICAL_AUTHORED_SOURCE", "Task150 Step21 source authority drifted")
    require(step21["delivery"]["path"] == "ignition/data/operations/iterations/150/standalone-evidence/task150-step21-standalone.html", "Task150 Step21 standalone path drifted")
    require(step21["delivery"]["artifact_sha256"] == TASK150_HTML_SHA256, "Task150 Step21 HTML digest drifted")
    require(step21["provenance"]["artifact_is_derived_only"] is True, "Task150 Step21 artifact is not marked derived-only")

    require(step06["fresh_source"]["architecture_path"] == "ignition/data/architecture/overall-architecture.json", "Task150 Step06 source path drifted")
    require(step06["fresh_source"]["architecture_sha256"] == source_sha, "Task150 Step06 source digest does not match current source")
    require(step06["derived_artifacts"]["svg"]["path"] == "ignition/data/operations/iterations/150/derived-artifacts/task150-current-architecture.svg", "Task150 Step06 SVG path drifted")
    require(step06["derived_artifacts"]["svg"]["sha256"] == TASK150_SVG_SHA256, "Task150 Step06 SVG digest drifted")

    standalone = step29["standalone_evidence"]
    require(standalone["canonical_source_sha256"] == source_sha, "Task150 Step29 source digest does not match current source")
    require(standalone["artifact_sha256"] == TASK150_HTML_SHA256, "Task150 Step29 artifact digest drifted")
    require(standalone["provider"]["immutable_revision"] == "06dd052602dd9a369e4d034e24faef0917b5a60c", "Task150 tested provider revision drifted")
    require(standalone["provider"]["role"] == "TESTED_OPTIONAL_PROVIDER_IMPLEMENTATION", "Task150 provider role was upgraded")
    require(standalone["provider"]["architecture_authority"] is False, "Task150 provider was made architecture authority")
    require(standalone["provider"]["automatic_update"] is False, "Task150 automatic provider update boundary drifted")
    require(step29["historical_lineage"]["historical_files_unchanged"] is True, "Task150 historical files are not marked immutable")
    require(step29["historical_lineage"]["no_evidence_rewritten"] is True, "Task150 historical evidence rewrite boundary drifted")

    step21_path = root_path(root, "ignition/data/operations/iterations/150/step21-fresh-standalone-evidence.json")
    step29_path = root_path(root, "ignition/data/operations/iterations/150/step29-exact-head-ready-gate.json")
    require(sha256_file(step21_path) == TASK150_STEP21_SHA256, "Task150 Step21 receipt bytes changed")
    require(sha256_file(step29_path) == TASK150_STEP29_SHA256, "Task150 Step29 receipt bytes changed")
    require(sha256_file(root_path(root, "ignition/data/operations/iterations/150/derived-artifacts/task150-current-architecture.svg")) == TASK150_SVG_SHA256, "Task150 verified SVG bytes changed")
    require(sha256_file(root_path(root, "ignition/data/operations/iterations/150/standalone-evidence/task150-step21-standalone.html")) == TASK150_HTML_SHA256, "Task150 verified HTML bytes changed")

    baseline_object, baseline_detail = git_check(root, "cat-file", "-e", f"{FORMAL_MAIN_BASELINE}^{{commit}}")
    source_revision_object, source_revision_detail = git_check(root, "cat-file", "-e", f"{TASK150_SOURCE_REVISION}^{{commit}}")
    lineage_verified = False
    if baseline_object and source_revision_object:
        baseline_is_ancestor, detail = git_check(root, "merge-base", "--is-ancestor", FORMAL_MAIN_BASELINE, "HEAD")
        require(baseline_is_ancestor, f"formal main baseline is not an ancestor of this head: {detail}")
        source_revision_is_ancestor, detail = git_check(root, "merge-base", "--is-ancestor", TASK150_SOURCE_REVISION, "HEAD")
        require(source_revision_is_ancestor, f"Task150 source revision is not in this head lineage: {detail}")
        source_path = "ignition/data/architecture/overall-architecture.json" if is_split_repository_root(root) else "data/architecture/overall-architecture.json"
        source_unchanged, detail = git_check(root, "diff", "--quiet", FORMAL_MAIN_BASELINE, "--", source_path)
        require(source_unchanged, f"canonical architecture source changed relative to formal main {FORMAL_MAIN_BASELINE}: {detail}")
        lineage_verified = True
    else:
        require(
            allow_missing_git_history,
            "formal main and Task150 revisions are unavailable for the canonical-source lineage gate: "
            f"baseline={baseline_detail} task150={source_revision_detail}",
        )

    return {
        "manifest": manifest,
        "source": source,
        "source_sha256": source_sha,
        "source_unchanged_from_formal_main": lineage_verified,
        "formal_main_lineage_verified": lineage_verified,
        "task150_step06": step06,
        "task150_step21": step21,
        "task150_step29": step29,
    }


def _svg_element_ids(svg_root: ET.Element) -> tuple[set[str], set[str]]:
    node_ids = {element.attrib["data-node-id"] for element in svg_root.iter() if "data-node-id" in element.attrib}
    edge_ids = {element.attrib["data-edge-id"] for element in svg_root.iter() if element.attrib.get("data-edge-id", "").startswith("canonical-edge-")}
    return node_ids, edge_ids


def _standalone_svg_bytes(data: bytes) -> bytes:
    """Package the verified SVG for direct image loading without changing its graph."""
    marker = b"<svg "
    require(data.startswith(marker), "Task150 SVG does not have the expected standalone root")
    namespace = b'xmlns="http://www.w3.org/2000/svg" '
    packaged = data if data.startswith(b'<svg xmlns="http://www.w3.org/2000/svg" ') else data.replace(marker, b"<svg " + namespace, 1)
    if b"<style>" in packaged:
        return packaged
    return packaged.replace(b"</desc>", b"</desc>\n        " + STANDALONE_SVG_CSS + b"\n", 1)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _first_child(svg_root: ET.Element, name: str) -> ET.Element | None:
    return next((element for element in svg_root if _local_name(element.tag) == name), None)


def _validate_svg(path: Path, expected_sha: str) -> dict[str, Any]:
    data = path.read_bytes()
    require(sha256_bytes(data) == expected_sha, f"published SVG digest mismatch: {path}")
    svg_root = ET.fromstring(data)
    require(_local_name(svg_root.tag) == "svg", "published architecture projection is not an SVG root")
    require(svg_root.attrib.get("viewBox") == EXPECTED_VIEWBOX, "published architecture SVG viewBox drifted")
    title = _first_child(svg_root, "title")
    description = _first_child(svg_root, "desc")
    require(title is not None and title.text == "点火整体架构：从来源到可读结果", "published architecture SVG title drifted")
    require(description is not None and "derived visualization" in (description.text or ""), "published architecture SVG description lost its derived boundary")
    node_ids, edge_ids = _svg_element_ids(svg_root)
    require(node_ids == EXPECTED_NODE_IDS, f"published architecture SVG node IDs drifted: {sorted(node_ids ^ EXPECTED_NODE_IDS)}")
    require(edge_ids == EXPECTED_EDGE_IDS, f"published architecture SVG edge IDs drifted: {sorted(edge_ids ^ EXPECTED_EDGE_IDS)}")
    require(not any(_local_name(element.tag) == "a" for element in svg_root.iter()), "published standalone SVG must not introduce stale source-link metadata")
    raw = data.decode("utf-8")
    require("<style>" in raw and "--bg:" in raw and ".c-frontend" in raw, "published standalone SVG lacks its packaging stylesheet")
    for token in ('class="map-bg"', 'class="node-link"', "iterations/150/"):
        require(token not in raw, f"published SVG contains retired or unstable projection marker: {token}")
    return {"sha256": sha256_bytes(data), "bytes": len(data), "nodes": len(node_ids), "edges": len(edge_ids)}


def _validate_html(path: Path, expected_sha: str, expected_svg: bytes) -> dict[str, Any]:
    data = path.read_bytes()
    require(sha256_bytes(data) == expected_sha, f"published interactive HTML digest mismatch: {path}")
    text = data.decode("utf-8")
    require("iterations/150/" not in text, "published interactive HTML must not expose an iterations/150 permanent route")
    matches = re.findall(rb"<svg\b.*?</svg>", data, flags=re.DOTALL)
    require(len(matches) == 1, "published interactive HTML must contain exactly one embedded SVG")
    embedded = matches[0]
    require(sha256_bytes(embedded) == TASK150_EMBEDDED_SVG_SHA256, "published interactive HTML embedded SVG digest drifted")
    require(_standalone_svg_bytes(embedded) + b"\n" == expected_svg, "published HTML and SVG are not the same verified visual")
    svg_root = ET.fromstring(embedded)
    require(_local_name(svg_root.tag) == "svg", "published HTML embedded content is not an SVG root")
    node_ids, edge_ids = _svg_element_ids(svg_root)
    require(node_ids == EXPECTED_NODE_IDS, "published interactive HTML node IDs drifted")
    require(edge_ids == EXPECTED_EDGE_IDS, "published interactive HTML edge IDs drifted")
    require("addEventListener" in text and "data-edge-from" in text, "published interactive HTML lacks its interaction behavior")
    return {"sha256": sha256_bytes(data), "bytes": len(data), "embedded_svg_sha256": sha256_bytes(embedded), "nodes": len(node_ids), "edges": len(edge_ids)}


def _validate_homepage_routes(root: Path) -> None:
    readme = shell_root(root) / ".github/README.md"
    require(readme.is_file(), "homepage README is missing")
    text = readme.read_text(encoding="utf-8")
    architecture = re.search(r"^## 4\. 整体架构\s*$", text, re.MULTILINE)
    require(architecture is not None, "homepage architecture section is missing")
    next_heading = re.search(r"^## (?!#)", text[architecture.end() :], re.MULTILINE)
    section = text[architecture.start() : architecture.end() + (next_heading.start() if next_heading else len(text))]
    images = re.findall(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)", section)
    require(images == [README_IMAGE_TARGET], "homepage does not embed the stable architecture SVG path")
    require(section.count(README_HTML_TARGET) == 1, "homepage does not expose exactly one stable interactive architecture link")

    def route_target(target: str) -> Path:
        direct = (readme.parent / target).resolve()
        if direct.is_file() or is_split_repository_root(root):
            return direct
        # The production-profile materialization probe places the split shell
        # inside an app-only copy and exposes the app through a sibling alias.
        # Validate the copied output directly in that fixture; strict formal
        # README route resolution remains enforced in the real split checkout.
        return (root / target.removeprefix("../ignition/")).resolve()

    require(route_target(README_IMAGE_TARGET).is_file(), "homepage embedded SVG target is unreachable")
    require(route_target(README_HTML_TARGET).is_file(), "homepage interactive HTML target is unreachable")


def validate(root: Path = ROOT, *, require_git_lineage: bool | None = None) -> dict[str, Any]:
    if require_git_lineage is None:
        require_git_lineage = is_split_repository_root(root)
    provenance = _check_task150_provenance(root, allow_missing_git_history=not require_git_lineage)
    manifest = provenance["manifest"]
    published_svg = root_path(root, manifest["published_outputs"]["svg"]["path"])
    published_html = root_path(root, manifest["published_outputs"]["html"]["path"])
    expected_svg = _standalone_svg_bytes(root_path(root, "ignition/data/operations/iterations/150/derived-artifacts/task150-current-architecture.svg").read_bytes())
    svg_result = _validate_svg(published_svg, PUBLISHED_SVG_SHA256)
    html_result = _validate_html(published_html, TASK150_HTML_SHA256, expected_svg)
    require(manifest["published_outputs"]["svg"]["sha256"] == svg_result["sha256"], "homepage manifest SVG digest is stale")
    require(manifest["published_outputs"]["html"]["sha256"] == html_result["sha256"], "homepage manifest HTML digest is stale")
    require(manifest["published_outputs"]["svg"]["bytes"] == svg_result["bytes"], "homepage manifest SVG byte count is stale")
    require(manifest["published_outputs"]["html"]["bytes"] == html_result["bytes"], "homepage manifest HTML byte count is stale")
    require(manifest["published_outputs"]["svg"]["source_artifact_sha256"] == TASK150_SVG_SHA256, "homepage published SVG is not bound to the Task150 source artifact")
    require(manifest["published_outputs"]["svg"]["packaging_normalization"] == "ADD_STANDALONE_SVG_XMLNS_AND_EMBEDDED_CSS_ONLY", "homepage SVG packaging normalization is not the bounded standalone wrapper")
    require(manifest["projection_contract"]["derived_only"] is True, "homepage projection is not declared derived-only")
    require(manifest["projection_contract"]["canonical_architecture_unchanged"] is True, "homepage manifest permits canonical architecture mutation")
    require(manifest["projection_contract"]["nodes"] == svg_result["nodes"] == html_result["nodes"], "homepage projection node count drifted")
    require(manifest["projection_contract"]["edges"] == svg_result["edges"] == html_result["edges"], "homepage projection edge count drifted")
    require(manifest["projection_contract"]["svg_view_box"] == EXPECTED_VIEWBOX, "homepage projection viewBox contract drifted")
    require(manifest["projection_contract"]["format_pair_same_visual"] is True, "homepage SVG/HTML visual-pair contract drifted")
    require(manifest["projection_contract"]["architecture_authority"] == "IGNITION_CANONICAL_AUTHORED_SOURCE", "homepage projection architecture authority drifted")
    require(manifest["projection_contract"]["provider_role"] == "TESTED_OPTIONAL_PROVIDER_IMPLEMENTATION", "homepage projection provider role drifted")
    require(manifest["projection_contract"]["default_renderer"] == "NOT_SELECTED", "homepage projection selected a default renderer")
    require(manifest["projection_contract"]["agent_reach"] == "NO_CHANGE", "homepage projection changed Agent Reach")
    require(manifest["projection_contract"]["live_external_invocation"] == "UNCHANGED_OPEN_OWNER_DEFERRED_NOT_RUN", "homepage projection changed live external invocation scope")
    _validate_homepage_routes(root)
    return {
        "status": "PASS",
        "source_sha256": provenance["source_sha256"],
        "source_unchanged_from_formal_main": provenance["source_unchanged_from_formal_main"],
        "formal_main_lineage_verified": provenance["formal_main_lineage_verified"],
        "svg": svg_result,
        "html": html_result,
        "homepage_display_verified": True,
        "default_renderer": manifest["projection_contract"]["default_renderer"],
        "agent_reach": manifest["projection_contract"]["agent_reach"],
        "live_external_invocation": manifest["projection_contract"]["live_external_invocation"],
    }


def materialize(root: Path = ROOT) -> dict[str, Any]:
    """Copy only the exact Task150-verified bytes after the digest gate passes."""
    # A production-profile probe may copy the app into a self-contained one-commit
    # fixture with no formal refs. Exact source/artifact digests still gate the
    # copy; a real repository publication uses ``--check`` and the strict lineage
    # path below whenever those formal refs are available.
    provenance = _check_task150_provenance(root, allow_missing_git_history=True)
    source_svg = root_path(root, "ignition/data/operations/iterations/150/derived-artifacts/task150-current-architecture.svg")
    source_html = root_path(root, "ignition/data/operations/iterations/150/standalone-evidence/task150-step21-standalone.html")
    published_svg = root_path(root, "docs/generated/ignition-system-architecture.svg")
    published_html = root_path(root, "docs/generated/ignition-system-architecture.html")
    published_svg.parent.mkdir(parents=True, exist_ok=True)
    published_svg.write_bytes(_standalone_svg_bytes(source_svg.read_bytes()))
    shutil.copyfile(source_html, published_html)
    result = validate(root, require_git_lineage=False)
    result["materialized_from"] = {
        "svg": repo_relative(root, source_svg),
        "html": repo_relative(root, source_html),
    }
    result["source_sha256"] = provenance["source_sha256"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate provenance and stable homepage outputs without writing")
    args = parser.parse_args()
    result = validate() if args.check else materialize()
    if args.check:
        print(
            "HOMEPAGE_ARCHITECTURE_PROJECTION_OK "
            f"source_sha256={result['source_sha256']} "
            f"svg_sha256={result['svg']['sha256']} "
            f"html_sha256={result['html']['sha256']} "
            f"nodes={result['svg']['nodes']} edges={result['svg']['edges']} "
            "homepage_display_verified=true"
        )
    else:
        print(
            "materialized homepage architecture projection "
            f"svg={result['svg']['sha256']} html={result['html']['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
