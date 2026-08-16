# Hermes Adapter R1

Hermes Agent's observed stable non-interactive surface is `-z/--oneshot
PROMPT`.  It prints only a final text response; it is not a structured event
stream.  The adapter therefore exposes a deliberately degraded, read-only
bridge and declares only `repo.read`:

```text
hermes --safe-mode --ignore-user-config --ignore-rules -z <literal task body>
```

The task body is a bounded canonical JSON description embedded as one argv
value.  The adapter never passes `--yolo` or `--accept-hooks`, never enables a
Gateway/channel/send command, and does not read Hermes config, memory,
sessions, skills, provider state or auth.  An optional constructor-supplied
resume value is an external pointer and is passed only through the observed
official `--resume` flag; it is not OS state.

Because Hermes one-shot approvals are auto-bypassed and final stdout is text,
the bridge rejects every capability/effect except an explicit low-risk
`repo.read` envelope.  It reports no progress or cancellation and maps a
successful final response to `COMPLETED_UNVALIDATED`; receipts remain
`REQUIRES_RECONCILIATION` until Ignition validators establish evidence.

Step 05 used a captured final-text fixture and injected process runner.
`LIVE_SMOKE_NOT_RUN`: no inference, memory read, provider/config/auth change,
Gateway, message, installation or upgrade was performed.

Official CLI reference: <https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/cli.md>.
