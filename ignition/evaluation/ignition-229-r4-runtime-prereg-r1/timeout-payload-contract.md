# Timeout and successor-payload contract

- An outer supervisor owns the 300-second wall timeout. It starts exactly one worker in a new POSIX session/process group. A timeout sends SIGTERM to the group, waits one second, then sends SIGKILL. The attempt is consumed, classified `EXTERNAL_TIMEOUT`, and never retried.
- A worker making a successful request still may not leave child processes behind; the supervisor checks and cleans the process group before returning.
- The network worker makes one HTTP request. No redirects, retry loops, SDK retry policy, connection reuse, or continuation request are present.
- The successor-payload maximum is exactly 16,384 bytes of strict UTF-8 bytes reconstructed from one response `output_text` string. It does not measure the JSON envelope, HTTP headers, chunk framing, or request bytes.
- Persist the complete extracted payload and SHA-256 before applying the maximum. A payload of 16,384 bytes passes the size gate; 16,385 bytes fails. Never truncate, normalize, trim, or re-encode after the hash.
- The 1 MiB HTTP entity-body safety limit is a separate transport guard. An over-limit response is an incomplete transport capture and non-pass, regardless of extracted-content length.
- Refusal, HTTP error, invalid JSON/UTF-8, duplicate envelope keys, incomplete response, unexpected model echo, output ambiguity, unsupported content encoding, timeout, or any protocol deviation is retained as a consumed non-pass attempt. No retry or replacement unit is allowed.
