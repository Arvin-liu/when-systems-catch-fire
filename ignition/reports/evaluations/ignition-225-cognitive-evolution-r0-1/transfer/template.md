# Transfer task template R0.1

This template is identical for every transfer conversation. The orchestration layer supplies one opaque task bundle containing a family-specific case set and its method/evidence material. This prompt contains no condition label or target.

Inputs:

- `case_A.md`
- `case_B.md`
- `case_C.md`
- `method.md`
- optional evidence/revision files under opaque names
- `PROMPT.md`
- `schema.json`

The task returns only a transfer response JSON. Opaque task IDs are supplied as conversation metadata, not as an input field.
