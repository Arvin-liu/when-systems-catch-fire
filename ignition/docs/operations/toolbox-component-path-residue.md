# Component path residue grouper

maintenance.summarize_component_path_residue groups caller-supplied unmapped_path
rows by their exact parent directory and by a conservative normalized
filename prefix. It is a read-only, offline triage helper.

## Input and output

The CLI reads one JSON object from standard input, validates it against
toolbox-component-path-residue-input-r0.schema.json, and writes one deterministic
JSON object to standard output. The request is capped at 1 MiB and 5,000 unique
repository-relative POSIX paths.

Example invocation:

    python3 -B ignition/tools/toolbox_component_path_residue.py --stdin < residue.json

The result includes exact input and source digests, directory cohorts, repeated
filename-prefix cohorts, and singleton paths. Family labels are mechanical
string groups. They do not identify a canonical component.

## Limits and permissions

- The tool accepts only unmapped_path records; ambiguous or other residue types
  stop with an error.
- It does not read the checkout, inspect source contents, suggest component IDs
  or path patterns, edit any registry, or select validation targets.
- It does not prove that paths in one cohort share an owner, meaning, risk, or
  validation requirement.
- A responsible human must decide whether a canonical mapping is warranted.
- The operation uses the Python standard library, makes no network request, and
  writes no files.
- The existing route validator remains authoritative for exact path ownership
  and validation selection.
