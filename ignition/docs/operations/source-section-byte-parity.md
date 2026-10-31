# Source Section Byte Parity

`maintenance.compare_source_section_bytes` compares one explicitly marked text section from a caller-supplied UTF-8 source document with the same marked section in one checked-out human document. It returns section offsets, byte counts and SHA-256 values; it does not return either section's text.

The request must supply the exact source text, a source reference, and the source document SHA-256. The digest is checked against the supplied text but the tool does not fetch or authenticate the source reference. The source text is accepted from bounded stdin and is not stored by the tool.

The executable accepts one regular UTF-8 `.md`, `.txt`, `.rst`, `.html` or `.xml` file under `.github/`, `docs/` or `ignition/`, or one of the root reading documents `README.md`, `SUMMARY.md`, `HUMAN-READING.md` or `llms.txt`, when that path exists. File access uses no-follow descriptor opens. Symlinks, traversal, unsupported files, non-unique markers, reversed markers and oversized inputs fail closed.

The current route card narrows its declared read scope to the existing `.github/` and `ignition/` roots. The adaptive router leaves the candidate out by default. An explicit tool-ID allowlist and matching task input/output types can propose it; the route proposal does not invoke the tool or grant file access.

The selected byte range starts at the unique start marker and ends immediately before the unique end marker. Bytes are compared without newline, Unicode or whitespace normalization. The tool does not check semantic equivalence, authorship, approval, source authenticity, or whether editing or publishing is authorized. Use the existing homepage structure validator separately for component shape and the authorized source for provenance.

Example:

```sh
python3 -B ignition/tools/toolbox_compare_source_section_bytes.py --stdin < request.json
```

The tool reads at most 512,000 bytes from stdin (source text at most 384,000 UTF-8 bytes) and at most 2 MiB from the selected candidate file. It writes one JSON result to stdout, performs no network request and changes no file.
