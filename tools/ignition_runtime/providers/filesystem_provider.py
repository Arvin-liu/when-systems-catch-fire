"""FileSystemProvider: reads real material files from a local directory.

Used for the five materials under ``/tmp/ctrl-1111/inputs/...``. All reads are
confined to the inputs root (path-escape guard). Each ``.md`` file (except the
index) becomes one material of tier ``SECONDARY_ACADEMIC_INTERPRETATION`` with a
single generic candidate / UNKNOWN / engineering-signal seed derived from its
content. This is a reproducer seam; it never changes the production architecture.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..errors import PathEscapeError
from ..hashutil import assert_under_root
from .base import MaterialProvider, MaterialRecord

INDEX_NAME = "INPUT_INDEX.md"

# The filesystem provider is confined to the repository or the designated control
# inputs area. A root such as "/" escapes both boundaries -> refuse (path-escape
# guard). The control area can be overridden via IGNITION_ALLOWED_INPUTS_ROOT.
REPO_ROOT = Path(__file__).resolve().parents[3]
_ALLOWED_INPUTS_ROOT = Path(
    os.environ.get("IGNITION_ALLOWED_INPUTS_ROOT", "/tmp/ctrl-1111")
).resolve()


def _assert_root_within_boundary(root: Path) -> None:
    resolved = root.resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        return
    if resolved == _ALLOWED_INPUTS_ROOT or _ALLOWED_INPUTS_ROOT in resolved.parents:
        return
    raise PathEscapeError(f"inputs root escapes allowed boundary: {root}")


class FileSystemProvider(MaterialProvider):
    def __init__(self, root: Path):
        self.root = Path(root)
        if not self.root.is_dir():
            raise PathEscapeError(f"inputs root is not a directory: {self.root}")

    def provider_identity(self) -> str:
        return "upload://" + self.root.resolve().as_uri().rsplit("/", 1)[-1]

    def _material_file(self, name: str) -> Path:
        _assert_root_within_boundary(self.root)
        p = (self.root / name).resolve()
        return assert_under_root(p, self.root)

    def read_index(self) -> str:
        path = self._material_file(INDEX_NAME)
        return path.read_text(encoding="utf-8", errors="replace")

    def list_materials(self, refs: list[str] | None = None) -> list[MaterialRecord]:
        _assert_root_within_boundary(self.root)
        files = sorted(self.root.glob("*.md"))
        records = []
        for f in files:
            if f.name == INDEX_NAME:
                continue
            if refs and f.stem not in refs:
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), f.stem)
            records.append(
                MaterialRecord(
                    material_id=f.stem,
                    source_bytes=text.encode("utf-8"),
                    source_tier="SECONDARY_ACADEMIC_INTERPRETATION",
                    provider_id=self.provider_identity(),
                    provider_mode="UPLOAD",
                    candidate_seeds=[
                        {"claim_text": f"{f.stem} content: {first_line}", "inference_claims": [], "source_claims": [first_line]},
                    ],
                    unknown_seeds=[
                        {"question": f"Is {f.stem} fully verified against its primary source?", "scope": f.stem},
                    ],
                    signal_seeds=[
                        {"description": f"{f.stem} needs a verification signal"},
                    ],
                )
            )
        return records

    def read_material(self, material_id: str) -> MaterialRecord:
        _assert_root_within_boundary(self.root)
        for rec in self.list_materials():
            if rec.material_id == material_id:
                return rec
        raise PathEscapeError(f"material not found under inputs root: {material_id}")
