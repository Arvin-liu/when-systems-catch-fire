"""Task 94 gate for every authoritative GitHub Pages public surface."""

from __future__ import annotations

import html.parser
import os
import posixpath
import re
import sys
import unicodedata
import unittest
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import test_pages_deploy_gate as deploy_gate  # noqa: E402


PAGES_WORKFLOW = ROOT / ".github/workflows/pages.yml"
BASE_PATH = "/when-systems-catch-fire/"
BASE_HOST = "arvin-liu.github.io"
AUTHORITATIVE_PUBLISH = [
    ("data/foundation/arguments/arguments.jsonl", "site/data/foundation/arguments/arguments.jsonl"),
    ("data/foundation/claims/claims.jsonl", "site/data/foundation/claims/claims.jsonl"),
    ("data/foundation/evidence/evidence.jsonl", "site/data/foundation/evidence/evidence.jsonl"),
    ("data/foundation/formal-objects/objects.jsonl", "site/data/foundation/formal-objects/objects.jsonl"),
    ("data/foundation/mappings/object-evidence-mappings.jsonl", "site/data/foundation/mappings/object-evidence-mappings.jsonl"),
    ("data/foundation/migrations/legacy-assets.jsonl", "site/data/foundation/migrations/legacy-assets.jsonl"),
    ("data/foundation/proofs/proof-artifacts.jsonl", "site/data/foundation/proofs/proof-artifacts.jsonl"),
    ("data/foundation/sources/sources.jsonl", "site/data/foundation/sources/sources.jsonl"),
    ("data/foundation/validations/validation-records.jsonl", "site/data/foundation/validations/validation-records.jsonl"),
    ("docs/AGENT-GUIDE.md", "site/docs/AGENT-GUIDE.md"),
    ("docs/architecture/attention-attractor-control-plane.md", "site/docs/architecture/attention-attractor-control-plane.md"),
    ("docs/architecture/compression-integrity-gate.md", "site/docs/architecture/compression-integrity-gate.md"),
    ("docs/architecture/distribution-collapse-control-plane.md", "site/docs/architecture/distribution-collapse-control-plane.md"),
    ("docs/architecture/effectual-action-plane.md", "site/docs/architecture/effectual-action-plane.md"),
    ("docs/architecture/mechanism-adjudication-plane.md", "site/docs/architecture/mechanism-adjudication-plane.md"),
    ("docs/governance/meta-protocol-reviews/cross-protocol-red-team.md", "site/docs/governance/meta-protocol-reviews/cross-protocol-red-team.md"),
    ("docs/governance/meta-protocol-reviews/factual-pending-register.md", "site/docs/governance/meta-protocol-reviews/factual-pending-register.md"),
    ("docs/meta-protocols/book-validation-22-cases-20260709.md", "site/docs/meta-protocols/book-validation-22-cases-20260709.md"),
    ("docs/meta-protocols/version-iteration-note-20260709.md", "site/docs/meta-protocols/version-iteration-note-20260709.md"),
    ("docs/phi_meta_law.md", "site/docs/phi_meta_law.md"),
    ("docs/publication/zhiyuan-writing-examples.md", "site/docs/publication/zhiyuan-writing-examples.md"),
    ("outputs/book-collisions/20260709-22-book-validation/book-case-candidates.md", "site/outputs/book-collisions/20260709-22-book-validation/book-case-candidates.md"),
    ("reports/foundation-architecture/core-system-reclassification-20260712.md", "site/reports/foundation-architecture/core-system-reclassification-20260712.md"),
]
F5_PUBLISH = (
    deploy_gate.F5_B1_PUBLISH
    + deploy_gate.F5_B2_PUBLISH
    + deploy_gate.F5_B2_BATCH2_PUBLISH
    + deploy_gate.F5_B2_BATCH3_PUBLISH
    + deploy_gate.F5_B2_BATCH4_PUBLISH
    + deploy_gate.F5_B2_BATCH5_PUBLISH
    + deploy_gate.F5_B3_PUBLISH
)


class _HTMLRefs(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(
        self, _tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        for attr, value in attrs:
            if attr == "id" and value:
                self.ids.add(value)
            if attr in {"href", "src", "data"} and value:
                self.refs.append(value)


def _cp_pairs() -> list[tuple[str, str]]:
    return deploy_gate._extract_cp_lines(PAGES_WORKFLOW.read_text(encoding="utf-8"))


def _markdown_refs(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    refs = [
        match.group(1).strip("<>")
        for match in re.finditer(
            r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)", text
        )
    ]
    parser = _HTMLRefs()
    parser.feed(text)
    refs.extend(parser.refs)
    return refs


def _public_path(source_public_path: str, raw: str) -> str | None:
    parsed = urllib.parse.urlparse(raw)
    if raw.startswith(("#", "mailto:", "tel:", "data:")):
        return None
    if parsed.scheme or parsed.netloc:
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.netloc != BASE_HOST
            or not parsed.path.startswith(BASE_PATH)
        ):
            return None
        decoded = urllib.parse.unquote(parsed.path[len(BASE_PATH) :])
        return unicodedata.normalize("NFC", decoded.lstrip("./"))
    decoded = urllib.parse.unquote(parsed.path)
    if decoded.startswith(BASE_PATH):
        decoded = decoded[len(BASE_PATH) :]
    elif decoded.startswith("/"):
        return None
    else:
        decoded = posixpath.normpath(
            posixpath.join(posixpath.dirname(source_public_path), decoded)
        )
    if decoded in {".", ""}:
        return ""
    return unicodedata.normalize("NFC", decoded.lstrip("./"))


def _artifact_target(root: Path, relative: str) -> Path | None:
    candidates = [root / relative]
    if relative.endswith(".md"):
        candidates.append(root / (relative[:-3] + ".html"))
    if relative.endswith("/"):
        candidates.append(root / relative / "index.html")
    for candidate in candidates:
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    return None


def _artifact_refs(path: Path) -> tuple[list[str], set[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".svg":
        root = ET.fromstring(text)
        refs = []
        for element in root.iter():
            for attr, value in element.attrib.items():
                if attr.rsplit("}", 1)[-1] == "href":
                    refs.append(value)
        return refs, set()
    parser = _HTMLRefs()
    parser.feed(text)
    return parser.refs, parser.ids


def _artifact_ids(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".html":
        parser = _HTMLRefs()
        parser.feed(text)
        return parser.ids
    if path.suffix == ".md":
        ids = set()
        for line in text.splitlines():
            match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
            if not match:
                continue
            heading = match.group(1).strip().casefold()
            heading = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", heading)
            heading = re.sub(r"[\s_]+", "-", heading).strip("-")
            if heading:
                ids.add(heading)
        return ids
    if path.suffix == ".svg":
        return {
            element.attrib["id"]
            for element in ET.fromstring(text).iter()
            if element.attrib.get("id")
        }
    return set()


class PublicSurfaceSourceGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cp_pairs = _cp_pairs()
        self.cp_targets = {target for _, target in self.cp_pairs}

    def test_existing_f5_42_targets_have_no_regression(self):
        self.assertEqual(len(F5_PUBLISH), 42)
        for pair in F5_PUBLISH:
            with self.subTest(pair=pair):
                self.assertIn(pair, self.cp_pairs)

    def test_authoritative_remaining_sources_exist_and_are_explicitly_published(self):
        self.assertEqual(len(AUTHORITATIVE_PUBLISH), 23)
        for source, target in AUTHORITATIVE_PUBLISH:
            with self.subTest(source=source):
                source_path = ROOT / source
                self.assertTrue(source_path.is_file(), f"missing source: {source}")
                self.assertGreater(source_path.stat().st_size, 0, f"empty source: {source}")
                self.assertIn((source, target), self.cp_pairs)

    def test_authoritative_markdown_links_resolve_to_explicit_public_targets(self):
        surfaces = [
            ("index.md", ROOT / "README.md"),
            ("SUMMARY.md", ROOT / "SUMMARY.md"),
            ("docs/USAGE.md", ROOT / "docs/USAGE.md"),
        ]
        published = {target[len("site/") :] for target in self.cp_targets if target.startswith("site/")}
        published.update({"", "system-map.html", "generated/ignition-system-map.svg"})
        failures = []
        for public_path, source in surfaces:
            for raw in _markdown_refs(source):
                target = _public_path(public_path, raw)
                if target is None:
                    continue
                if target.endswith("/"):
                    failures.append((source.relative_to(ROOT).as_posix(), raw, "directory target"))
                elif target not in published:
                    failures.append((source.relative_to(ROOT).as_posix(), raw, target))
        self.assertEqual(failures, [], f"unpublished internal public references: {failures}")

    def test_readme_does_not_leak_repository_pages_prefix_into_public_url(self):
        failures = [
            raw
            for raw in _markdown_refs(ROOT / "README.md")
            if urllib.parse.urlparse(raw).path.startswith("./pages/")
        ]
        self.assertEqual(failures, [])

    def test_publish_allowlist_has_no_duplicate_target_or_missing_source(self):
        targets = [target for _, target in self.cp_pairs if target.startswith("site/")]
        self.assertEqual(len(targets), len(set(targets)))
        missing = [source for source, _ in self.cp_pairs if not (ROOT / source).is_file()]
        self.assertEqual(missing, [])

    def test_public_paths_are_nfc_and_do_not_duplicate_baseurl(self):
        for public_path, source in [
            ("index.md", ROOT / "README.md"),
            ("SUMMARY.md", ROOT / "SUMMARY.md"),
            ("docs/USAGE.md", ROOT / "docs/USAGE.md"),
        ]:
            for raw in _markdown_refs(source):
                target = _public_path(public_path, raw)
                if target is None:
                    continue
                with self.subTest(source=source.name, raw=raw):
                    self.assertEqual(target, unicodedata.normalize("NFC", target))
                    decoded = urllib.parse.unquote(raw).casefold()
                    self.assertLessEqual(decoded.count(BASE_PATH.rstrip("/").casefold()), 1)


@unittest.skipUnless(
    os.environ.get("PAGES_CANDIDATE_ARTIFACT_DIR"),
    "PAGES_CANDIDATE_ARTIFACT_DIR not set",
)
class PublicSurfaceCandidateArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(os.environ["PAGES_CANDIDATE_ARTIFACT_DIR"]).resolve()
        self.surfaces = [
            self.root / "index.html",
            self.root / "SUMMARY.html",
            self.root / "docs/USAGE.html",
            self.root / "system-map.html",
            self.root / "generated/ignition-system-map.svg",
        ]

    def test_authoritative_surfaces_exist_and_are_nonempty(self):
        missing = [
            path.relative_to(self.root).as_posix()
            for path in self.surfaces
            if not path.is_file() or path.stat().st_size == 0
        ]
        self.assertEqual(missing, [])

    def test_every_direct_internal_reference_resolves_inside_artifact(self):
        failures = []
        for surface in self.surfaces:
            refs, _ = _artifact_refs(surface)
            source_public = surface.relative_to(self.root).as_posix()
            for raw in refs:
                parsed = urllib.parse.urlparse(raw)
                if raw.startswith("#"):
                    target = source_public
                else:
                    target = _public_path(source_public, raw)
                if target is None:
                    continue
                target_no_fragment = urllib.parse.urldefrag(target)[0]
                if target_no_fragment == "":
                    target_path = self.root / "index.html"
                else:
                    target_path = _artifact_target(self.root, target_no_fragment)
                if target_path is None:
                    failures.append((source_public, raw, target_no_fragment))
                    continue
                if parsed.fragment:
                    fragment = urllib.parse.unquote(parsed.fragment)
                    if fragment not in _artifact_ids(target_path):
                        failures.append((source_public, raw, f"missing anchor: {fragment}"))
        self.assertEqual(failures, [], f"candidate artifact broken references: {failures}")

    def test_candidate_has_no_duplicate_baseurl_or_path_semantic_drift(self):
        failures = []
        for surface in self.surfaces:
            refs, _ = _artifact_refs(surface)
            for raw in refs:
                decoded = urllib.parse.unquote(raw)
                if decoded.casefold().count(BASE_PATH.rstrip("/").casefold()) > 1:
                    failures.append((surface.name, raw, "duplicate baseurl"))
                if decoded.startswith("./pages/"):
                    failures.append((surface.name, raw, "repository pages prefix"))
                if decoded != unicodedata.normalize("NFC", decoded):
                    failures.append((surface.name, raw, "non-NFC path"))
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
