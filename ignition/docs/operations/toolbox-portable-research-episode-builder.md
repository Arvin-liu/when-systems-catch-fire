# Portable Research Episode Builder

This optional, default-off tool builds the existing R0 Portable Research Episode manifest from caller-supplied event declarations and local included-file paths.

It reads regular files beneath an explicit workspace root under `ignition/`, computes SHA-256 and byte-count observations, resolves artifact-version references, and emits one manifest plus a file-receipt list. It does not copy file contents or write files.

## Run

```sh
python3 -B ignition/tools/toolbox_build_portable_research_episode.py \
  --stdin \
  --workspace-root ignition \
  < ignition/data/operations/toolbox-portable-research-episode-builder-input-r0.json
```

The input schema is `toolbox-portable-research-episode-builder-input-r0.schema.json`; the output envelope is described by `toolbox-portable-research-episode-builder-output-r0.schema.json`. The returned `episode` conforms to `toolbox-portable-research-episode-r0.schema.json`.

For included artifact rows, callers provide IDs, versions, safe paths relative to the selected root, dependency/event relations, and required/current flags. SHA-256 values are computed from the observed bytes; references in parent/dependency/run/review relations are resolved from artifact ID and version. Missing items belong in the explicit `omissions` list, not in the included-file list.

## Limits and follow-up

- Maximum input: 262,144 bytes; 64 included artifacts; 8 MiB per file; 32 MiB total bytes read.
- Absolute paths, traversal, symlinks, non-regular files, roots outside `ignition/`, and files that change while read are rejected.
- The tool records one local read observation. It does not authenticate a source, actor, run, review, timestamp, permission or scientific claim, and does not prove bytes remain unchanged after the read.
- A successful build means only that an episode envelope was assembled and declared local file bytes were hashed. Run `collaboration.validate_portable_research_episode` separately to check schema and cross-reference consistency. Use an authorized receiver/byte-verification process for actual transfer.
- The tool is not selected by default. Explicit router allowlisting proposes selection only; it does not execute the tool or authorize file reads outside the caller's selected workspace.

The manifest builder complements the episode validator, which consumes an already-built manifest, and the handoff byte verifier, which compares files against a different receipt contract. It does not replace either tool.
