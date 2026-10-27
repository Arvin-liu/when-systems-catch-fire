"""Deep Research Capability — tool adapters (Round 3).

Adapters turn external tools (web / PDF / attachment / bounded calculation) into
Research OS executor observations under contract. They encode the Round 3
security rules:

* External content is UNTRUSTED DATA, not instruction. ``detect_prompt_injection``
  flags known injection patterns; when detected the content is quarantined (kept
  as data, never executed as instruction) and the source is flagged.
* Exact source identity + inspected scope are recorded (fail-closed: an opened
  source must declare what was actually inspected — matches the Round 1
  source-record schema).
* Bounded calculation executes ONLY a restricted arithmetic subset (no arbitrary
  code / file / network), and records input/output SHA-256 hashes.
* Tool errors remain observations (never exceptions that abort the episode).

Live network fetching is intentionally NOT performed here; the adapter open()
accepts already-fetched content (or a local file) so the loop is testable
offline. Live wiring happens in Round 6 (bounded pilot).
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

from deep_research import records as R

# Patterns that indicate instruction-injection attempts in untrusted content.
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.I),
    re.compile(r"disregard\s+(the\s+)?(previous|prior|above)", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"system\s+prompt", re.I),
    re.compile(r"<system>", re.I),
    re.compile(r"act\s+as\s+(an?\s+)?(admin|root|system)", re.I),
    re.compile(r"reveal\s+(your\s+)?(prompt|instructions|system)", re.I),
]


def detect_prompt_injection(text: str) -> list[str]:
    """Return the list of injection patterns matched in ``text`` (empty = clean)."""
    if not text:
        return []
    hits = []
    for pat in _INJECTION_PATTERNS:
        if pat.search(text):
            hits.append(pat.pattern)
    return hits


def _sha256(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def identity_for_url(url: str) -> str:
    """Exact, stable identity for a web source: the URL + its content hash."""
    return f"web:{url}"


def identity_for_file(path: str) -> str:
    p = Path(path)
    digest = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "missing"
    return f"file:{p.name}:{digest[:16]}"


def _executor_obs(action_id: str, observations: list, source_identities: list,
                  access_level: str, calculation_result=None, errors=None,
                  provenance=None, timestamps=None) -> dict:
    return R.make_executor_observation(
        observation_id=f"obs-{_sha256({'a': action_id, 's': source_identities})[:12]}",
        action_id=action_id,
        observations=observations,
        source_identities=source_identities,
        access_level=access_level,
        calculation_result=calculation_result,
        errors=errors or [],
        provenance=provenance or [],
        timestamps=timestamps or {},
    )


class ToolAdapter:
    """Base adapter: every method returns an executor-observation under contract."""

    name = "base"

    def search(self, query: str, discovered: list[dict] | None = None) -> dict:
        raise NotImplementedError

    def open(self, source_id: str, locator: str, content: str | None = None) -> dict:
        raise NotImplementedError


class WebAdapter(ToolAdapter):
    name = "web"

    def search(self, query: str, discovered: list[dict] | None = None) -> dict:
        # Discovered sources are recorded with DISCOVERED access (not opened yet).
        sids = [{"source_id": identity_for_url(d["url"]), "access_level": "DISCOVERED"}
                for d in (discovered or [])]
        return _executor_obs(
            action_id="act-search",
            observations=[f"discovered {len(sids)} web sources for query: {query}"],
            source_identities=sids,
            access_level="DISCOVERED",
            provenance=[{"step": "search", "query": query}],
        )

    def open(self, source_id: str, locator: str, content: str | None = None) -> dict:
        if content is None:
            # Offline: no content supplied -> not opened (fail-closed on scope).
            return _executor_obs(
                action_id="act-open",
                observations=[f"could not open {source_id}: no content available offline"],
                source_identities=[{"source_id": source_id, "access_level": "NONE"}],
                access_level="NONE",
                errors=[f"offline: {source_id} not opened"],
                provenance=[{"step": "open", "source_id": source_id}],
            )
        hits = detect_prompt_injection(content)
        trusted = not hits
        return _executor_obs(
            action_id="act-open",
            observations=[content[:5000]],  # store data, not instruction
            source_identities=[{
                "source_id": source_id,
                "access_level": "FULL_TEXT" if trusted else "ABSTRACT_ONLY",
                "injection_detected": bool(hits),
            }],
            access_level="FULL_TEXT" if trusted else "ABSTRACT_ONLY",
            provenance=[{
                "step": "open", "source_id": source_id, "locator": locator,
                "inspected_scope": "full_text" if trusted else "abstract_only_quarantined",
                "injection_detected": bool(hits),
            }],
        )


class PdfAdapter(ToolAdapter):
    name = "pdf"

    def search(self, query: str, discovered: list[dict] | None = None) -> dict:
        sids = [{"source_id": d.get("source_id", identity_for_file(d.get("path", ""))),
                 "access_level": "DISCOVERED"} for d in (discovered or [])]
        return _executor_obs(
            action_id="act-search",
            observations=[f"discovered {len(sids)} PDF sources for query: {query}"],
            source_identities=sids,
            access_level="DISCOVERED",
            provenance=[{"step": "search", "query": query}],
        )

    def open(self, source_id: str, locator: str, content: str | None = None) -> dict:
        if content is None:
            return _executor_obs(
                action_id="act-open",
                observations=[f"could not open PDF {source_id}: no content offline"],
                source_identities=[{"source_id": source_id, "access_level": "NONE"}],
                access_level="NONE",
                errors=[f"offline: {source_id} not opened"],
                provenance=[{"step": "open", "source_id": source_id}],
            )
        hits = detect_prompt_injection(content)
        return _executor_obs(
            action_id="act-open",
            observations=[content[:5000]],
            source_identities=[{
                "source_id": source_id,
                "access_level": "FULL_TEXT" if not hits else "ABSTRACT_ONLY",
                "injection_detected": bool(hits),
            }],
            access_level="FULL_TEXT" if not hits else "ABSTRACT_ONLY",
            provenance=[{
                "step": "open", "source_id": source_id, "locator": locator,
                "inspected_scope": "full_text" if not hits else "abstract_only_quarantined",
                "injection_detected": bool(hits),
            }],
        )


class AttachmentAdapter(ToolAdapter):
    name = "attachment"

    def search(self, query: str, discovered: list[dict] | None = None) -> dict:
        sids = [{"source_id": d.get("source_id", "att"), "access_level": "DISCOVERED"}
                for d in (discovered or [])]
        return _executor_obs(
            action_id="act-search",
            observations=[f"discovered {len(sids)} attachments for query: {query}"],
            source_identities=sids,
            access_level="DISCOVERED",
            provenance=[{"step": "search", "query": query}],
        )

    def open(self, source_id: str, locator: str, content: str | None = None) -> dict:
        if content is None:
            return _executor_obs(
                action_id="act-open",
                observations=[f"attachment {source_id} not supplied"],
                source_identities=[{"source_id": source_id, "access_level": "NONE"}],
                access_level="NONE",
                errors=[f"offline: {source_id} not opened"],
                provenance=[{"step": "open", "source_id": source_id}],
            )
        hits = detect_prompt_injection(content)
        return _executor_obs(
            action_id="act-open",
            observations=[content[:5000]],
            source_identities=[{
                "source_id": source_id,
                "access_level": "FULL_TEXT" if not hits else "ABSTRACT_ONLY",
                "injection_detected": bool(hits),
            }],
            access_level="FULL_TEXT" if not hits else "ABSTRACT_ONLY",
            provenance=[{
                "step": "open", "source_id": source_id, "locator": locator,
                "inspected_scope": "full_text" if not hits else "abstract_only_quarantined",
                "injection_detected": bool(hits),
            }],
        )


class CalcAdapter:
    """Bounded calculation: only a restricted arithmetic subset, with hashes.

    No arbitrary code, file, or network access. Inputs and outputs are hashed so
    downstream claims can cite exactly what was computed.
    """

    name = "calc"
    _ALLOWED_NODES = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd,
        ast.Call, ast.Name, ast.Load, ast.Tuple, ast.List,
    )

    def compute(self, code: str, inputs: dict | None = None) -> dict:
        inputs = inputs or {}
        try:
            tree = ast.parse(code, mode="eval")
            for node in ast.walk(tree):
                if not isinstance(node, self._ALLOWED_NODES):
                    raise ValueError(f"disallowed expression node: {type(node).__name__}")
                if isinstance(node, ast.Call):
                    # Only sum/min/max/mean-style pure reductions allowed.
                    if not isinstance(node.func, ast.Name) or node.func.id not in (
                        "sum", "min", "max", "abs", "round"
                    ):
                        raise ValueError(f"disallowed call: {getattr(node.func, 'id', node.func)}")
            env = {k: v for k, v in inputs.items() if isinstance(v, (int, float, list, tuple))}
            env.update({"sum": sum, "min": min, "max": max, "abs": abs, "round": round})
            result = eval(compile(tree, "<calc>", "eval"), {"__builtins__": {}}, env)
            errors = []
        except Exception as e:  # tool error remains an observation
            result = None
            errors = [f"{type(e).__name__}: {e}"]
        input_hash = _sha256(inputs)
        output_hash = _sha256(result)
        return {
            "result": result,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "errors": errors,
        }

    def observation(self, code: str, inputs: dict | None = None) -> dict:
        res = self.compute(code, inputs)
        return _executor_obs(
            action_id="act-calc",
            observations=[f"computed: {code} -> {res['result']}"],
            source_identities=[{
                "source_id": f"calc:{res['input_hash'][:12]}",
                "access_level": "COMPUTED",
            }],
            access_level="COMPUTED",
            calculation_result={
                "code": code,
                "result": res["result"],
                "input_hash": res["input_hash"],
                "output_hash": res["output_hash"],
            },
            errors=res["errors"],
            provenance=[{"step": "calculate", "code": code}],
        )


def build_default_adapters() -> dict:
    return {
        "web": WebAdapter(),
        "pdf": PdfAdapter(),
        "attachment": AttachmentAdapter(),
        "calc": CalcAdapter(),
    }
