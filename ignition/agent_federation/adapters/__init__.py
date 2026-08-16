"""Public, vendor-specific adapter boundaries for External Agent Federation R1."""

from .hermes import HermesAdapter, HermesAdapterError
from .openclaw import OpenClawAdapter, OpenClawAdapterError

__all__ = [
    "HermesAdapter",
    "HermesAdapterError",
    "OpenClawAdapter",
    "OpenClawAdapterError",
]
