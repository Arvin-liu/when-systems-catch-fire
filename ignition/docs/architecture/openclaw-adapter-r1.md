# OpenClaw Adapter R1

`OpenClawAdapter` is a narrow External Agent Federation boundary over the
observed public `openclaw agent` CLI.  The Step 00 probe recorded JSON output,
UTF-8 message-file input, session-key/session-id pointers, and a bounded
timeout.  The adapter therefore uses:

```text
openclaw agent --json [--agent ID] [--session-key KEY] \
  --message-file <disposable UTF-8 envelope> --timeout <seconds>
```

The command is assembled as literal argv with `shell=False`; task text never
passes through shell interpolation.  Gateway, channel, browser, device,
private SQLite/session databases, OpenClaw memory, and the OpenClaw internal
plan/tool loop remain OpenClaw-owned and are not copied into the Ignition OS.
The adapter reports no progress, cancellation, or native resume capability
because the observed `agent --help` did not prove those operations.

An executor-reported completion becomes `COMPLETED_UNVALIDATED` progress and a
`REQUIRES_RECONCILIATION` receipt until Ignition validators establish evidence.
External session IDs are pointer-only references.  Step 04 intentionally used
captured JSON fixtures and injected runners; `LIVE_SMOKE_NOT_RUN` because no
external inference, channel action, configuration change, or permanent daemon
was authorized.

Official machine-facing reference: <https://github.com/openclaw/openclaw/blob/main/docs/cli/agent.md>.
