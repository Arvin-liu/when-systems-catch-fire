# Portable Research Episode Manifest Preflight

This optional read-only CLI checks one caller-supplied episode manifest from JSON on stdin. It validates artifact identity/version references, declared parent and dependency links, planned/attempted/executed/not-executed states, separate used and attached artifact references, review targets, explicit omissions, and identifier maps for a proposed read-only fork.

The implementation follows the portable, versioned research-episode scope in Workbench #75 at `acf2caebbb615d2827d1767a7a17358f8de38fc4`. It is an isolated `EXPERIMENTAL_AVAILABLE` candidate, excluded from routing by default. The C1 comparison record is `ignition/data/operations/toolbox-portable-research-episode-c1-comparison-r0.json`; it preserves `COMPARISON_UNKNOWN` because the adjacent agent-plan and handoff-byte tools do not accept the same task object, and no matched cost or quality trial exists.

Run from the repository root:

```bash
python3 -B ignition/tools/toolbox_portable_research_episode.py --stdin \
  < ignition/tests/fixtures/toolbox-portable-research-episode/valid-source-package-r0.json
```

The CLI reads at most 262,144 UTF-8 bytes and emits one JSON object. Exit status 0 means the manifest's declared relations are internally consistent. Exit status 2 means malformed input, schema failure, a cross-reference conflict, or a required omission. A historical review remains attached to its exact artifact version; the validator warns when that version is not marked current.

## What it does not establish

The manifest is caller-supplied. `EPISODE_MANIFEST_CONSISTENT` does not authenticate source bytes, actors, run records, review identities, permissions, or scientific claims. `artifact_bytes_verified`, `import_performed`, and `execution_authorized` remain false. The CLI does not read paths, copy files, import a package, execute code, or grant a fork authority.

If transferred artifact bytes also need checking, use [the handoff artifact byte verifier](toolbox-handoff-artifact-byte-check.md) with a separate receipt and explicit workspace root. If the work needs a multi-agent execution plan checked before any separately authorized run, use [Agent Episode Binding Plan Preflight](toolbox-agent-episode-binding.md). The two tools validate different objects; neither validates this manifest's episode history or review-version relationships.

The manifest contract is defined in `ignition/schemas/operations/toolbox-portable-research-episode-r0.schema.json`. Route evidence is recorded in `ignition/data/operations/toolbox-portable-research-episode-route-evidence-r0.json`; the PR #264 task-derived invocation is in `ignition/data/operations/toolbox-portable-research-episode-real-task-r0.json`. The tool does not change the Current registry or default routing.
