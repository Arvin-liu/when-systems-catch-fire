#!/usr/bin/env python3
"""Single-request Task229-R4 runtime adapter, frozen for preregistration R1.

The CLI is intentionally inert unless a later, separate owner-authorized task
sets TASK229_R4_EXECUTION_AUTHORIZATION=OWNER_AUTHORIZED_R4_EXECUTION.  Tests
exercise only local byte fixtures and never call the provider.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import platform
import ssl
import sys
from pathlib import Path
from typing import Any

MODEL = "gpt-6-astra"
EFFORT = "medium"
HOST = "api.openai.com"
PATH = "/v1/responses"
PROCESS_TIMEOUT_SECONDS = 300
SUCCESSOR_PAYLOAD_MAX_BYTES = 16_384
TRANSPORT_BODY_MAX_BYTES = 1_048_576
AUTHORIZATION_ENV = "TASK229_R4_EXECUTION_AUTHORIZATION"
AUTHORIZATION_VALUE = "OWNER_AUTHORIZED_R4_EXECUTION"
CANARY_TEXT = "Output exactly the ASCII token RUNTIME_CANARY_OK; no other characters."
CANARY_EXPECTED = "RUNTIME_CANARY_OK"
_REQUESTS_STARTED = 0

SUCCESSOR_KEYS = {
    "case_prose",
    "policy_json_utf8",
    "reference_execution_json_utf8",
    "typed_binding_json_utf8",
}
INPUT_HASH_KEYS = {
    "case_prose": "case_prose_sha256",
    "policy_json_utf8": "policy_sha256",
    "reference_execution_json_utf8": "reference_execution_sha256",
    "typed_binding_json_utf8": "binding_sha256",
}
REQUIRED_INPUT_HASH_FIELDS = {
    "policy_sha256", "binding_sha256", "source_case_record_sha256", "case_prose_sha256",
    "reference_execution_sha256", "prompt_template_sha256", "response_schema_sha256",
    "route_trace_schema_sha256",
}


class RuntimeContractError(ValueError):
    """A fail-closed protocol or capture error."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8", errors="strict")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RuntimeContractError("DUPLICATE_JSON_OBJECT_KEY")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise RuntimeContractError("NONFINITE_JSON_NUMBER")


def strict_json(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
        return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeContractError("TRANSPORT_RESPONSE_NOT_STRICT_UTF8_JSON") from exc


def load_unit_record(raw: bytes) -> dict[str, Any]:
    row = strict_json(raw)
    if not isinstance(row, dict) or set(row) != {"run_id", "successor_inputs", "input_hashes"}:
        raise RuntimeContractError("UNIT_RECORD_SHAPE_MISMATCH")
    successor_inputs = row["successor_inputs"]
    hashes = row["input_hashes"]
    if not isinstance(successor_inputs, dict) or set(successor_inputs) != SUCCESSOR_KEYS:
        raise RuntimeContractError("SUCCESSOR_INPUT_FIELDS_MISMATCH")
    if not isinstance(hashes, dict):
        raise RuntimeContractError("INPUT_HASHES_NOT_OBJECT")
    if set(hashes) != REQUIRED_INPUT_HASH_FIELDS:
        raise RuntimeContractError("INPUT_HASH_FIELDS_MISMATCH")
    if any(not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value)
           for value in hashes.values()):
        raise RuntimeContractError("INPUT_HASH_FORMAT_INVALID")
    for field, digest_field in INPUT_HASH_KEYS.items():
        value = successor_inputs[field]
        if not isinstance(value, str):
            raise RuntimeContractError("SUCCESSOR_INPUT_NOT_STRING:" + field)
        try:
            encoded = value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise RuntimeContractError("SUCCESSOR_INPUT_NOT_SCALAR_UTF8:" + field) from exc
        if hashes.get(digest_field) != sha256(encoded):
            raise RuntimeContractError("SUCCESSOR_INPUT_HASH_MISMATCH:" + field)
    if not isinstance(row["run_id"], str) or not row["run_id"]:
        raise RuntimeContractError("RUN_ID_MISSING")
    return row


def build_model_input(prompt_template: bytes, response_schema: bytes,
                      successor_inputs: dict[str, str]) -> bytes:
    """Use frozen source bytes with fixed, documented framing; do not add advice."""
    if set(successor_inputs) != SUCCESSOR_KEYS:
        raise RuntimeContractError("SUCCESSOR_INPUT_FIELDS_MISMATCH")
    for raw in (prompt_template, response_schema):
        raw.decode("utf-8", errors="strict")
    inputs_raw = canonical_json_bytes(successor_inputs)
    return (
        prompt_template
        + b"\n\nFROZEN_RESPONSE_SCHEMA_JSON_UTF8:\n"
        + response_schema
        + b"\n\nSUCCESSOR_INPUTS_CANONICAL_JSON_UTF8:\n"
        + inputs_raw
    )


def build_request_body(model_input: bytes, *, model: str = MODEL, effort: str = EFFORT) -> bytes:
    try:
        input_text = model_input.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeContractError("MODEL_INPUT_NOT_STRICT_UTF8") from exc
    request = {
        "input": input_text,
        "model": model,
        "reasoning": {"effort": effort},
        "store": False,
        "tool_choice": "none",
        "tools": [],
    }
    return canonical_json_bytes(request)


def build_canary_request() -> bytes:
    """Synthetic target-blind fixture request; this function does not send it."""
    return build_request_body(CANARY_TEXT.encode("ascii"))


def record_canary_outcome(result: dict[str, Any], capture_dir: Path) -> dict[str, Any]:
    outcome: dict[str, Any] = {
        "target_blind": True,
        "contains_task229_material": False,
        "r4_unit_count": 0,
        "request_model": MODEL,
        "request_reasoning_effort": EFFORT,
        "request_tools": [],
        "request_tool_choice": "none",
        "runtime_capture_status": result.get("status"),
        "http_status": result.get("http_status"),
        "accepted_model_echo": result.get("accepted_model_echo"),
        "reasoning_effort_echo": result.get("reasoning_effort_echo"),
        "backend_effort_echo_claimed": False,
        "request_body_sha256": result.get("request_body_sha256"),
        "transport_response_sha256": result.get("transport_response_sha256"),
        "transport_response_bytes": result.get("transport_response_bytes"),
        "successor_payload_sha256": result.get("successor_payload_sha256"),
        "successor_payload_bytes": result.get("successor_payload_bytes"),
    }
    effort_echo_ok = result.get("reasoning_effort_echo") in {None, EFFORT}
    model_echo_ok = result.get("accepted_model_echo") == MODEL
    if result.get("reasoning_effort_echo") is None:
        outcome["effort_acceptance_basis"] = "medium was sent; a completed HTTP response accepted the request; no backend effort echo available"
    else:
        outcome["effort_acceptance_basis"] = "provider response reasoning.effort echo"
    if result.get("status") != "CAPTURED_AWAITING_FROZEN_SCHEMA_VALIDATION" or not effort_echo_ok or not model_echo_ok:
        outcome["status"] = "CANARY_RUNTIME_GATE_FAILED"
    else:
        payload_path = capture_dir / "successor-payload.bin"
        outcome["output_exact_match"] = payload_path.is_file() and payload_path.read_bytes() == CANARY_EXPECTED.encode("ascii")
        hashes_present = all(outcome[key] for key in (
            "request_body_sha256", "transport_response_sha256", "successor_payload_sha256"
        ))
        if not outcome["output_exact_match"]:
            outcome["status"] = "CANARY_OUTPUT_MISMATCH"
        elif not hashes_present or result.get("http_status") != 200:
            outcome["status"] = "CANARY_CAPTURE_INCOMPLETE"
        else:
            outcome["status"] = "CANARY_RUNTIME_GATE_PASSED"
    write_json_new(capture_dir / "canary-result.json", outcome)
    return outcome


def _safe_headers(headers: http.client.HTTPMessage) -> dict[str, str]:
    allowed = {
        "content-type", "content-encoding", "content-length", "transfer-encoding",
        "date", "x-request-id",
    }
    return {key.lower(): value for key, value in headers.items() if key.lower() in allowed}


def write_new(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def write_json_new(path: Path, value: Any) -> None:
    write_new(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                               allow_nan=False).encode("utf-8") + b"\n")


def extract_successor_payload(transport_response_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
    """Extract one completed assistant text block without parsing its JSON payload."""
    response = strict_json(transport_response_bytes)
    if not isinstance(response, dict):
        raise RuntimeContractError("RESPONSE_ENVELOPE_NOT_OBJECT")
    if response.get("status") != "completed" or response.get("error") is not None:
        raise RuntimeContractError("RESPONSE_NOT_COMPLETED")
    if response.get("incomplete_details") is not None:
        raise RuntimeContractError("RESPONSE_INCOMPLETE_DETAILS_PRESENT")
    if response.get("model") != MODEL:
        raise RuntimeContractError("ACCEPTED_MODEL_ECHO_MISMATCH")
    output = response.get("output")
    if not isinstance(output, list):
        raise RuntimeContractError("RESPONSE_OUTPUT_NOT_ARRAY")
    messages: list[dict[str, Any]] = []
    for item in output:
        if not isinstance(item, dict):
            raise RuntimeContractError("RESPONSE_OUTPUT_ITEM_NOT_OBJECT")
        item_type = item.get("type")
        if item_type == "message":
            if item.get("role") != "assistant":
                raise RuntimeContractError("NON_ASSISTANT_MESSAGE_PRESENT")
            messages.append(item)
        elif item_type != "reasoning":
            raise RuntimeContractError("NON_TEXT_OR_REASONING_OUTPUT_PRESENT")
    if len(messages) != 1:
        raise RuntimeContractError("ASSISTANT_MESSAGE_COUNT_NOT_ONE")
    content = messages[0].get("content")
    if not isinstance(content, list):
        raise RuntimeContractError("ASSISTANT_CONTENT_NOT_ARRAY")
    text_items = [item for item in content if isinstance(item, dict) and item.get("type") == "output_text"]
    if len(text_items) != 1 or len(content) != 1:
        raise RuntimeContractError("OUTPUT_TEXT_BLOCK_COUNT_NOT_ONE")
    text = text_items[0].get("text")
    if not isinstance(text, str):
        raise RuntimeContractError("OUTPUT_TEXT_NOT_STRING")
    try:
        payload = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise RuntimeContractError("OUTPUT_TEXT_NOT_SCALAR_UTF8") from exc
    metadata = {
        "response_id": response.get("id"),
        "accepted_model_echo": response.get("model"),
        "response_status": response.get("status"),
        "reasoning_effort_echo": (
            response.get("reasoning", {}).get("effort")
            if isinstance(response.get("reasoning"), dict) else None
        ),
    }
    if metadata["reasoning_effort_echo"] is not None and metadata["reasoning_effort_echo"] != EFFORT:
        raise RuntimeContractError("ACCEPTED_REASONING_EFFORT_ECHO_MISMATCH")
    return payload, metadata


def persist_response(transport_response_bytes: bytes, capture_dir: Path, *,
                     http_status: int, headers: dict[str, str],
                     transport_capture_complete: bool = True,
                     request_body_sha256: str | None = None,
                     transport_incomplete_reason: str | None = None) -> dict[str, Any]:
    """Persist/hash transport first, then extract/persist/hash payload, then size-gate."""
    capture_dir.mkdir(parents=True, exist_ok=True)
    if (capture_dir / "transport-response.bin").exists() or (capture_dir / "capture-result.json").exists():
        raise RuntimeContractError("CAPTURE_DIRECTORY_NOT_EMPTY")
    transport_hash = sha256(transport_response_bytes)
    write_new(capture_dir / "transport-response.bin", transport_response_bytes)
    write_new(capture_dir / "transport-response.sha256", (transport_hash + "\n").encode("ascii"))
    transport_meta = {
        "capture_layer": "HTTP response entity-body octets after transfer framing removal; before JSON decoding",
        "capture_complete": transport_capture_complete,
        "http_status": http_status,
        "headers": headers,
        "transport_response_bytes": len(transport_response_bytes),
        "transport_response_sha256": transport_hash,
    }
    write_json_new(capture_dir / "transport-metadata.json", transport_meta)

    result: dict[str, Any] = {
        "http_status": http_status,
        "request_body_sha256": request_body_sha256,
        "transport_capture_complete": transport_capture_complete,
        "transport_response_bytes": len(transport_response_bytes),
        "transport_response_sha256": transport_hash,
        "status": "CAPTURED_TRANSPORT_ONLY",
    }
    if not transport_capture_complete:
        result["status"] = transport_incomplete_reason or "TRANSPORT_BODY_LIMIT_EXCEEDED"
        write_json_new(capture_dir / "capture-result.json", result)
        return result
    if http_status != 200:
        result["status"] = "HTTP_STATUS_NOT_200"
        write_json_new(capture_dir / "capture-result.json", result)
        return result
    if headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
        result["status"] = "UNSUPPORTED_CONTENT_ENCODING"
        write_json_new(capture_dir / "capture-result.json", result)
        return result
    try:
        payload, response_meta = extract_successor_payload(transport_response_bytes)
    except RuntimeContractError as exc:
        result["status"] = "RESPONSE_EXTRACTION_REJECTED"
        result["reason"] = str(exc)
        write_json_new(capture_dir / "capture-result.json", result)
        return result

    payload_hash = sha256(payload)
    write_new(capture_dir / "successor-payload.bin", payload)
    write_new(capture_dir / "successor-payload.sha256", (payload_hash + "\n").encode("ascii"))
    result.update(response_meta)
    result["successor_payload_bytes"] = len(payload)
    result["successor_payload_sha256"] = payload_hash
    result["status"] = (
        "SUCCESSOR_PAYLOAD_TOO_LARGE"
        if len(payload) > SUCCESSOR_PAYLOAD_MAX_BYTES
        else "CAPTURED_AWAITING_FROZEN_SCHEMA_VALIDATION"
    )
    result["schema_parse_performed"] = False
    write_json_new(capture_dir / "capture-result.json", result)
    return result


def send_one_request(request_body: bytes, capture_dir: Path, api_key: str,
                     task_context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Make exactly one direct HTTPS request; no proxy, redirect, retry, or session reuse."""
    global _REQUESTS_STARTED
    if not api_key:
        raise RuntimeContractError("OPENAI_API_KEY_MISSING")
    if _REQUESTS_STARTED != 0:
        raise RuntimeContractError("ONE_PROVIDER_REQUEST_PER_PROCESS_ENFORCED")
    capture_dir.mkdir(parents=True, exist_ok=True)
    if any(capture_dir.iterdir()):
        raise RuntimeContractError("CAPTURE_DIRECTORY_NOT_EMPTY")
    request_digest = sha256(request_body)
    write_new(capture_dir / "request-body.sha256", (request_digest + "\n").encode("ascii"))
    try:
        source_digest = sha256(Path(__file__).read_bytes())
    except OSError:
        source_digest = None
    context = {
        "runtime": "direct-openai-responses-http-r1",
        "python_version": platform.python_version(),
        "runtime_executor_sha256": source_digest,
        "requested_model": MODEL,
        "requested_reasoning_effort": EFFORT,
        "request_body_sha256": request_digest,
        "provider_requests_in_process": 1,
        "retry_count": 0,
    }
    if task_context:
        context.update(task_context)
    write_json_new(capture_dir / "runtime-context.json", context)
    tls_context = ssl.create_default_context()
    conn = http.client.HTTPSConnection(HOST, timeout=PROCESS_TIMEOUT_SECONDS, context=tls_context)
    try:
        _REQUESTS_STARTED += 1
        conn.request("POST", PATH, body=request_body, headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Connection": "close",
        })
        response = conn.getresponse()
        response_headers = _safe_headers(response.headers)
        read_error: str | None = None
        try:
            body = response.read(TRANSPORT_BODY_MAX_BYTES + 1)
        except http.client.IncompleteRead as exc:
            body = exc.partial
            read_error = "INCOMPLETE_HTTP_RESPONSE_BODY"
        except (OSError, http.client.HTTPException) as exc:
            body = b""
            read_error = "HTTP_BODY_READ_ERROR:" + type(exc).__name__
        complete = read_error is None and len(body) <= TRANSPORT_BODY_MAX_BYTES
        incomplete_reason = read_error
        if len(body) > TRANSPORT_BODY_MAX_BYTES:
            complete = False
            incomplete_reason = "TRANSPORT_BODY_LIMIT_EXCEEDED"
        content_length = response_headers.get("content-length")
        if complete and content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError:
                complete = False
                incomplete_reason = "INVALID_CONTENT_LENGTH_HEADER"
            else:
                if declared_length != len(body):
                    complete = False
                    incomplete_reason = "CONTENT_LENGTH_MISMATCH"
        return persist_response(body, capture_dir, http_status=response.status,
                                headers=response_headers,
                                transport_capture_complete=complete,
                                request_body_sha256=request_digest,
                                transport_incomplete_reason=incomplete_reason)
    except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
        write_json_new(capture_dir / "transport-failure.json", {
            "status": "TRANSPORT_REQUEST_FAILED",
            "request_body_sha256": request_digest,
            "error_type": type(exc).__name__,
            "retry_count": 0,
            "provider_requests_started": 1,
            "response_body_captured": False,
        })
        return {"status": "TRANSPORT_REQUEST_FAILED", "request_body_sha256": request_digest,
                "error_type": type(exc).__name__, "retry_count": 0}
    finally:
        conn.close()


def _authorized() -> bool:
    return os.environ.get(AUTHORIZATION_ENV) == AUTHORIZATION_VALUE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-live", action="store_true", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--unit-json", type=Path)
    mode.add_argument("--canary", action="store_true")
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--response-schema-file", type=Path)
    parser.add_argument("--capture-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if not _authorized():
        print("EXPLICIT_FOLLOW_ON_OWNER_AUTHORIZATION_REQUIRED", file=sys.stderr)
        return 3
    task_context: dict[str, Any] = {"run_id": "SYNTHETIC-CANARY-R1", "input_hashes": {}}
    if args.canary:
        body = build_canary_request()
    else:
        if args.prompt_file is None or args.response_schema_file is None:
            print("FROZEN_PROMPT_AND_SCHEMA_REQUIRED", file=sys.stderr)
            return 2
        row = load_unit_record(args.unit_json.read_bytes())
        model_input = build_model_input(args.prompt_file.read_bytes(),
                                        args.response_schema_file.read_bytes(),
                                        row["successor_inputs"])
        body = build_request_body(model_input)
        task_context = {"run_id": row["run_id"], "input_hashes": row["input_hashes"]}
    api_key = os.environ.get("OPENAI_API_KEY", "")
    result = send_one_request(body, args.capture_dir, api_key, task_context)
    if args.canary:
        result = record_canary_outcome(result, args.capture_dir)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    success = result.get("status") in {
        "CAPTURED_AWAITING_FROZEN_SCHEMA_VALIDATION",
        "CANARY_RUNTIME_GATE_PASSED",
    }
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
