#!/usr/bin/env python3
"""Run the preregistered first OpenAlex census for task 110.

This program is deliberately limited to acquisition. It never changes the
population, applies a result-driven correction, or overwrites a run. The
first-run directory is sealed by the caller in a separate commit after all
117 records have an acquisition outcome.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parent
POPULATION = ROOT / "population-manifest.jsonl"
RUN_DIR = ROOT / "first-run-20260801"
API = "https://api.openalex.org/works"
USER_AGENT = "ignition-task-110-openalex-census/1.0"
TIMEOUT_SECONDS = 30
MIN_INTERVAL_SECONDS = 0.11
RETRY_DELAYS = (1.0, 2.0, 4.0)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def normalize_doi(value: str | None) -> str:
    value = (value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
    return value.strip()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_line(path: pathlib.Path, value: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def request_url(doi: str, mailto: str | None) -> tuple[str, str]:
    params = {"filter": f"doi:{doi}"}
    if mailto:
        params["mailto"] = mailto
    url = f"{API}?{urllib.parse.urlencode(params)}"
    redacted = f"{API}?{urllib.parse.urlencode({'filter': f'doi:{doi}'})}"
    if mailto:
        redacted += "&mailto=<redacted>"
    return url, redacted


def fetch_one(source_id: str, doi: str, mailto: str | None, raw_dir: pathlib.Path) -> dict:
    url, redacted_url = request_url(doi, mailto)
    attempts: list[dict] = []
    last_error: str | None = None

    for attempt in range(1, len(RETRY_DELAYS) + 2):
        started = utc_now()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
                body = response.read()
                status = int(response.status)
                headers = {
                    key.lower(): value
                    for key, value in response.headers.items()
                    if key.lower() in {"content-type", "etag", "last-modified", "retry-after"}
                }
            body_hash = sha256_bytes(body)
            raw_path = raw_dir / f"{source_id}.json"
            raw_path.write_bytes(body)
            attempts.append({
                "attempt": attempt,
                "started_at": started,
                "finished_at": utc_now(),
                "http_status": status,
                "response_sha256": body_hash,
            })
            return {
                "request_url": redacted_url,
                "request_method": "GET",
                "attempts": attempts,
                "final_http_status": status,
                "raw_response_path": str(raw_path.relative_to(ROOT)),
                "raw_response_sha256": body_hash,
                "response_headers": headers,
                "body": body,
                "error": None,
            }
        except urllib.error.HTTPError as exc:
            body = exc.read()
            body_hash = sha256_bytes(body)
            raw_path = raw_dir / f"{source_id}.attempt-{attempt}.http-{exc.code}.bin"
            raw_path.write_bytes(body)
            last_error = f"HTTPError {exc.code}: {exc.reason}"
            attempts.append({
                "attempt": attempt,
                "started_at": started,
                "finished_at": utc_now(),
                "http_status": int(exc.code),
                "response_sha256": body_hash,
                "error": last_error,
            })
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            if not retryable or attempt > len(RETRY_DELAYS):
                return {
                    "request_url": redacted_url,
                    "request_method": "GET",
                    "attempts": attempts,
                    "final_http_status": int(exc.code),
                    "raw_response_path": str(raw_path.relative_to(ROOT)),
                    "raw_response_sha256": body_hash,
                    "response_headers": {},
                    "body": None,
                    "error": last_error,
                }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            attempts.append({
                "attempt": attempt,
                "started_at": started,
                "finished_at": utc_now(),
                "http_status": None,
                "error": last_error,
            })
            if attempt > len(RETRY_DELAYS):
                return {
                    "request_url": redacted_url,
                    "request_method": "GET",
                    "attempts": attempts,
                    "final_http_status": None,
                    "raw_response_path": None,
                    "raw_response_sha256": None,
                    "response_headers": {},
                    "body": None,
                    "error": last_error,
                }

        time.sleep(RETRY_DELAYS[attempt - 1])

    raise AssertionError(last_error or "unreachable")


def select_result(payload: dict, expected_doi: str) -> tuple[dict | None, int | None, str]:
    results = payload.get("results")
    if not isinstance(results, list):
        return None, None, "results_not_list"
    matches = [
        (index, result)
        for index, result in enumerate(results)
        if isinstance(result, dict) and normalize_doi(result.get("doi")) == expected_doi
    ]
    if len(matches) != 1:
        return None, None, "no_exact_doi_match" if not matches else "multiple_exact_doi_matches"
    index, result = matches[0]
    return result, index, "exact_normalized_doi_match"


def main() -> None:
    if RUN_DIR.exists():
        raise SystemExit(f"refusing to overwrite existing first run: {RUN_DIR}")
    rows = [json.loads(line) for line in POPULATION.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 117:
        raise SystemExit(f"population must contain 117 records, found {len(rows)}")

    RUN_DIR.mkdir(parents=True)
    raw_dir = RUN_DIR / "raw"
    raw_dir.mkdir()
    source_path = RUN_DIR / "source-manifest.jsonl"
    run_path = RUN_DIR / "run-manifest.jsonl"
    mailto = os.environ.get("OPENALEX_MAILTO") or None
    started_at = utc_now()
    previous_request_at = 0.0
    acquired = 0

    for position, row in enumerate(rows, start=1):
        doi = normalize_doi(row["doi_normalized"])
        elapsed = time.monotonic() - previous_request_at
        if previous_request_at and elapsed < MIN_INTERVAL_SECONDS:
            time.sleep(MIN_INTERVAL_SECONDS - elapsed)
        result = fetch_one(row["source_id"], doi, mailto, raw_dir)
        previous_request_at = time.monotonic()
        payload = None
        selected = None
        selected_index = None
        selection_rationale = "no_payload"
        if result["body"] is not None:
            try:
                payload = json.loads(result["body"])
                selected, selected_index, selection_rationale = select_result(payload, doi)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                selection_rationale = f"invalid_json:{type(exc).__name__}"

        if result["final_http_status"] == 200 and result["body"] is not None:
            acquired += 1
        source_record = {
            "position": position,
            "source_id": row["source_id"],
            "doi_normalized": doi,
            "doi_raw": row["doi_raw"],
            "registry_title": row["title"],
            "crossref_title": row["crossref_title"],
            "crossref_year": row["crossref_year"],
            "registry_retraction_status": row["retraction_status"],
            "is_duplicate_doi": row["is_duplicate_doi"],
            "request_url": result["request_url"],
            "request_method": result["request_method"],
            "mailto_supplied": bool(mailto),
            "retrieved_at": utc_now(),
            "http_status": result["final_http_status"],
            "raw_response_path": result["raw_response_path"],
            "raw_response_sha256": result["raw_response_sha256"],
            "attempts": result["attempts"],
            "selected_result_index": selected_index,
            "selection_rationale": selection_rationale,
            "openalex_work_id": selected.get("id") if selected else None,
            "openalex_doi": selected.get("doi") if selected else None,
            "display_name": selected.get("display_name") if selected else None,
            "publication_year": selected.get("publication_year") if selected else None,
            "type": selected.get("type") if selected else None,
            "is_retracted": selected.get("is_retracted") if selected else None,
            "cited_by_count": selected.get("cited_by_count") if selected else None,
            "error": result["error"],
        }
        json_line(source_path, source_record)
        json_line(run_path, {
            "position": position,
            "source_id": row["source_id"],
            "doi_normalized": doi,
            "retrieved_at": source_record["retrieved_at"],
            "http_status": result["final_http_status"],
            "attempts": result["attempts"],
            "acquisition_state": "HTTP_200_JSON" if payload is not None else "FAILED_OR_INVALID",
            "selection_rationale": selection_rationale,
            "error": result["error"],
        })
        print(json.dumps({"position": position, "source_id": row["source_id"], "status": result["final_http_status"], "selected": bool(selected)}, ensure_ascii=False), flush=True)

    seal = {
        "run_id": "first-run-20260801",
        "started_at": started_at,
        "finished_at": utc_now(),
        "population_path": str(POPULATION.relative_to(ROOT)),
        "population_sha256": sha256_bytes(POPULATION.read_bytes()),
        "population_records": len(rows),
        "http_200_json_records": acquired,
        "mailto_supplied": bool(mailto),
        "endpoint": API,
        "user_agent": USER_AGENT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "minimum_interval_seconds": MIN_INTERVAL_SECONDS,
        "retry_delays_seconds": list(RETRY_DELAYS),
        "status": "COMPLETE_ACQUISITION_RUN",
    }
    (RUN_DIR / "RUN-SEAL.json").write_text(json.dumps(seal, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
