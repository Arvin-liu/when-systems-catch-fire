# Local proof capture semantics

Each completed repetition persisted the raw JSON-RPC initialize/config/read/thread/start/turn/start request and response frames before interpreting them. `config/read` response bytes were hashed before examining effective provider fields. The exact `$CODEX_HOME/config.toml` was hashed before app-server launch and checked for realpath equality and TOML parse.

The local mock accepts only the expected loopback Responses endpoint. It writes the exact incoming HTTP bytes and entity body to separate files and hashes them before JSON parsing. The `tools` field and all recognized tool namespace fields are inspected only in a parsed copy. A deterministic mock response is persisted as raw HTTP response bytes. The exact assistant payload from app-server notifications is separately persisted and hashed.

The repository receipt contains SHA-256 values and assertions, not raw host requests or protocol frames. Those raw files can include Codex system/developer prompt material, so they remain in restricted local temporary roots. The `request-body` hash identifies the HTTP JSON body; the `full-loopback-http-request` hash includes HTTP headers and body. The mock response hash covers the local HTTP response bytes. These are local process captures, not a TCP/TLS wire capture.

A process-scoped macOS sandbox denies non-loopback egress except for the one exact `127.0.0.1` listener; the local proxy rejects any non-loopback destination without forwarding. The recorded proxy-attempt count is zero. This is not a host-wide network-isolation claim.

The synthetic model metadata fallback warning is retained as an app-server notification and in the run summaries. The initial aborted attempt is separately recorded; its lack of a model request means it cannot serve as a tools assertion.
