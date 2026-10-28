# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Registry-driven adapter dispatch protocol for the R2 real-object pilot (repair R1).

This module is the SINGLE SOURCE OF TRUTH for how each object class is dispatched
to its read-only adapter. The frozen R2 runner unconditionally passed
``declared_capabilities`` to every adapter, which raised ``TypeError`` on the five
adapters that do not declare that keyword (defect 4.1: 42 extraction failures).

The protocol here guarantees:

* every adapter receives only the context keys it has declared for its class;
* only the mechanism/state adapter receives the Function OS ``declared_capabilities``
  contract (it is the only adapter that may call a declared capability);
* an unknown object class OR an undeclared context key fails closed (raises
  ``ValueError``) instead of being silently dropped or dispatched;
* no introspection-based silent kwarg dropping is used.

Mutating ``ADAPTER_DISPATCH`` changes runtime behaviour, which the repair test
suite proves by mutation (changing the declared contract must change behavior).
"""
from __future__ import annotations

from typing import Any, Callable

from .adapters import (
    adapt_text_ref, adapt_git_pr_ci, adapt_structured_data,
    adapt_production_receipt, adapt_temporal_sequence, adapt_mechanism_state,
)

# The single source of truth for adapter dispatch, keyed by object_class.
#
#   adapter                    : the read-only callable (it owns its real signature)
#   context_keys               : the exact set of keys the adapter is allowed to
#                                receive from the locked manifest adapter_ref
#   passes_declared_capabilities: whether the Function OS declared-capabilities
#                                contract is forwarded (only the mechanism adapter)
ADAPTER_DISPATCH: dict[str, dict[str, Any]] = {
    "text_transcript_source": {
        "adapter": adapt_text_ref,
        "context_keys": {"object_id", "digest", "visibility", "short_paraphrase", "aggregate_counts"},
        "passes_declared_capabilities": False,
    },
    "git_pr_ci_chain": {
        "adapter": adapt_git_pr_ci,
        "context_keys": {"object_id", "digest", "repo", "ref", "ref_kind"},
        "passes_declared_capabilities": False,
    },
    "structured_data_object": {
        "adapter": adapt_structured_data,
        "context_keys": {"object_id", "data_kind", "digest", "aggregate_counts"},
        "passes_declared_capabilities": False,
    },
    "production_runtime_receipt": {
        "adapter": adapt_production_receipt,
        "context_keys": {"object_id", "op_kind", "digest"},
        "passes_declared_capabilities": False,
    },
    "temporal_event_sequence": {
        "adapter": adapt_temporal_sequence,
        "context_keys": {"object_id", "digest", "event_time", "observation_time", "ingestion_time"},
        "passes_declared_capabilities": False,
    },
    "mechanism_system_state": {
        "adapter": adapt_mechanism_state,
        "context_keys": {"object_id", "capability", "digest"},
        "passes_declared_capabilities": True,
    },
}


class AdapterProtocolError(ValueError):
    """Fail-closed dispatch error (unknown class or undeclared context key)."""


def dispatch(object_class: str, ref_payload: dict, *,
             declared_capabilities: set[str] | None = None,
             local_evidence_root: str | None = None) -> dict[str, Any]:
    """Dispatch a manifest object to its read-only adapter under the protocol.

    Fail-closed: an unknown object class or any context key not declared for that
    class raises ``AdapterProtocolError``. Only the mechanism adapter receives the
    Function OS declared-capabilities contract. No introspection-based silent kwarg
    dropping occurs.

    The caller is responsible for passing a COPY of the manifest ``adapter_ref``;
    this function never mutates ``ref_payload``.
    """
    entry = ADAPTER_DISPATCH.get(object_class)
    if entry is None:
        raise AdapterProtocolError(f"unknown adapter class for object (fail-closed): {object_class!r}")
    # Fail-closed on any undeclared context key.
    for key in ref_payload:
        if key not in entry["context_keys"]:
            raise AdapterProtocolError(
                f"undeclared context key for object class (fail-closed): "
                f"class={object_class!r} key={key!r}")
    adapter: Callable = entry["adapter"]
    kwargs: dict[str, Any] = {"local_evidence_root": local_evidence_root}
    if entry["passes_declared_capabilities"]:
        kwargs["declared_capabilities"] = declared_capabilities
    return adapter(ref_payload, **kwargs)


def declared_classes() -> list[str]:
    """The object classes the protocol knows how to dispatch."""
    return list(ADAPTER_DISPATCH.keys())


def context_keys_for(object_class: str) -> frozenset[str]:
    """The context keys declared for an object class (fail-closed if unknown)."""
    entry = ADAPTER_DISPATCH.get(object_class)
    if entry is None:
        raise AdapterProtocolError(f"unknown adapter class: {object_class!r}")
    return frozenset(entry["context_keys"])
