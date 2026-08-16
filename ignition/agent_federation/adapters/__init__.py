"""Public, vendor-specific adapter boundaries for External Agent Federation R1."""

from .codex import CodexAdapter, CodexAdapterError
from .hermes import HermesAdapter, HermesAdapterError
from .openclaw import OpenClawAdapter, OpenClawAdapterError

__all__ = [
    "CodexAdapter",
    "CodexAdapterError",
    "HermesAdapter",
    "HermesAdapterError",
    "OpenClawAdapter",
    "OpenClawAdapterError",
]
