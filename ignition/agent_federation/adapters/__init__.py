"""Public, vendor-specific adapter boundaries for External Agent Federation R1."""

from .openclaw import OpenClawAdapter, OpenClawAdapterError

__all__ = ["OpenClawAdapter", "OpenClawAdapterError"]
