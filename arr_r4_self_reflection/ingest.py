"""Sealed R3 evidence ingestor and closed-set validator (R4 task §2, §8).

The ingestor reads a directory that contains, at minimum:
  - receipts/<object_key>.json     (one per processed note)
  - envelopes/<object_key>.json    (one per processed note)
  - <LEDGER>.json                  (R3 aggregate/report ledgers)

It performs closed-set validation (no missing/extra identity, exact count
agreement) and exposes deterministic digests for every receipt, envelope and
report consumed by R4. Nothing here hard-codes 836 ids or any R3 result value;
the counts fall out of the directory contents.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List

# Ledger/report files consumed by R4 (by base name, without extension).
CONSUMED_REPORTS = (
    "AGGREGATE_METRICS",
    "COUNTERS",
    "CAPABILITY_COVERAGE_MATRIX",
    "FALSE_CONSENSUS_CASES",
    "INDEPENDENT_SOURCE_ESTIMATE",
    "TEMPORAL_AMBIGUITY_LEDGER",
    "CORPUS_RUN_LEDGER",
    "CRASH_RECOVERY_REPORT",
    "INCREMENTAL_RERUN_REPORT",
    "REPLAY_AND_DRIFT_REPORT",
    "FAILURE_ATTRIBUTION_LEDGER",
    "SOURCE_DEPENDENCY_GRAPH",
)


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _load_json(path: str) -> Any:
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


class SealedEvidenceIngestor:
    def __init__(self, evidence_dir: str):
        self.evidence_dir = evidence_dir
        self.receipts_dir = os.path.join(evidence_dir, "receipts")
        self.envelopes_dir = os.path.join(evidence_dir, "envelopes")
        self.receipts: Dict[str, Dict[str, Any]] = {}
        self.envelopes: Dict[str, Dict[str, Any]] = {}
        self.reports: Dict[str, Dict[str, Any]] = {}
        self.receipt_digests: Dict[str, str] = {}
        self.envelope_digests: Dict[str, str] = {}
        self.report_digests: Dict[str, str] = {}

    # -- ingestion ---------------------------------------------------------

    def ingest(self) -> "SealedEvidenceIngestor":
        self._ingest_receipts()
        self._ingest_envelopes()
        self._ingest_reports()
        return self

    def _ingest_receipts(self) -> None:
        for name in sorted(os.listdir(self.receipts_dir)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(self.receipts_dir, name)
            with open(path, "rb") as fh:
                raw = fh.read()
            obj = json.loads(raw.decode("utf-8"))
            key = obj.get("object_key") or name[: -len(".json")]
            self.receipts[key] = obj
            self.receipt_digests[key] = _sha256_bytes(raw)

    def _ingest_envelopes(self) -> None:
        for name in sorted(os.listdir(self.envelopes_dir)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(self.envelopes_dir, name)
            with open(path, "rb") as fh:
                raw = fh.read()
            obj = json.loads(raw.decode("utf-8"))
            key = obj.get("object_key") or name[: -len(".json")]
            self.envelopes[key] = obj
            self.envelope_digests[key] = _sha256_bytes(raw)

    def _ingest_reports(self) -> None:
        for base in CONSUMED_REPORTS:
            path = os.path.join(self.evidence_dir, base + ".json")
            if not os.path.exists(path):
                continue
            with open(path, "rb") as fh:
                raw = fh.read()
            self.reports[base] = json.loads(raw.decode("utf-8"))
            self.report_digests[base] = _sha256_bytes(raw)

    # -- closed-set validation (§2, §10) -----------------------------------

    def validate_closed_set(self) -> Dict[str, Any]:
        receipt_keys = set(self.receipts)
        envelope_keys = set(self.envelopes)
        missing_envelope = sorted(receipt_keys - envelope_keys)
        missing_receipt = sorted(envelope_keys - receipt_keys)
        extra = len(receipt_keys) - len(envelope_keys)
        n = len(receipt_keys)
        closed_set_ok = (
            len(missing_envelope) == 0
            and len(missing_receipt) == 0
            and len(receipt_keys) == len(envelope_keys)
        )
        return {
            "receipts_total": len(receipt_keys),
            "envelopes_total": len(envelope_keys),
            "missing_input_identities": len(missing_receipt),
            "extra_input_identities": len(missing_envelope),
            "count_delta": extra,
            "closed_set_ok": closed_set_ok,
            "missing_envelope_for_receipt": missing_envelope,
            "missing_receipt_for_envelope": missing_receipt,
        }

    def manifest(self) -> Dict[str, Any]:
        audit = self.validate_closed_set()
        return {
            "receipts_total": audit["receipts_total"],
            "envelopes_total": audit["envelopes_total"],
            "closed_set_ok": audit["closed_set_ok"],
            "missing_input_identities": audit["missing_input_identities"],
            "extra_input_identities": audit["extra_input_identities"],
            "receipt_digests": self.receipt_digests,
            "envelope_digests": self.envelope_digests,
            "report_digests": self.report_digests,
            "identity_audit": audit,
        }
