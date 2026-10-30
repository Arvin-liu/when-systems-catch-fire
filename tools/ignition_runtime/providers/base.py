"""Provider interface (the single seam to source materials)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MaterialRecord:
    material_id: str
    source_bytes: bytes
    source_tier: str
    provider_id: str
    provider_mode: str
    observed_at: str | None = None
    published_at: str | None = None
    event_at: str | None = None
    candidate_seeds: list[dict] = field(default_factory=list)
    unknown_seeds: list[dict] = field(default_factory=list)
    signal_seeds: list[dict] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


class MaterialProvider(ABC):
    @abstractmethod
    def list_materials(self, refs: list[str] | None = None) -> list[MaterialRecord]:
        """Return material records (optionally filtered by id)."""

    @abstractmethod
    def read_material(self, material_id: str) -> MaterialRecord:
        """Return a single material record by id."""

    @abstractmethod
    def provider_identity(self) -> str:
        """Stable (id+mode) identity of this provider."""
