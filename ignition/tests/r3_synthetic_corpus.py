# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Deterministic synthetic corpus builder for R3 corpus-runtime tests.

Contains NO private WAIC content. The corpus is small, fully synthetic, and
exercises every mechanism the runtime must handle: type variety, byte-identical
and normalized-identical duplicates, near-duplicate clusters, shared-source
derivatives (false-consensus risk), an explicit framed event date, a missing
created_at field, and a malformed frontmatter (quarantine). Tests build it into a
temp dir, so the public repository ships zero note bodies.
"""
from __future__ import annotations

from pathlib import Path

EXPECTED_NOTE_COUNT = 29  # 20 base + 9 special cases (see builder)
INDEX_FILE = "索引.md"

# Deliberate expectations used by the acceptance tests.
EXACT_DUP_PAIR = ("dup_a", "dup_b")
NEAR_DUP_PAIR = ("near_a", "near_b")
SHARED_HOST = "shared.example.com"
SHARED_PAIR = ("shared_1", "shared_2")
EVT_NOTE = "evt"
NO_CREATE_NOTE = "nocreate"
BADFM_NOTE = "badfm"

_DUP_BODY = "Identical synthetic paragraph used to prove normalized-text deduplication."
_NEAR_HEAD = "NEAR-HEAD-" + "x" * 300
_NEAR_TAIL = "NEAR-TAIL-" + "y" * 300


def _fm(note_id: str, ntype: str, created_at: str | None = "2026-07-10 10:00:00") -> str:
    lines = ['---', f'note_id: "{note_id}"', f'title: "Synthetic {note_id}"', f'note_type: "{ntype}"']
    if created_at is not None:
        lines.append(f'created_at: "{created_at}"')
    lines.append('tags: ["synthetic", "r3-test"]')
    lines.append('---')
    return "\n".join(lines) + "\n"


def build_synthetic_corpus(root: str | Path) -> Path:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    # 20 base notes: link 8, plain_text 6, local_audio 3, recorder_audio 3
    plan = (
        ["link"] * 8 + ["plain_text"] * 6 + ["local_audio"] * 3 + ["recorder_audio"] * 3
    )
    for i, ntype in enumerate(plan):
        nid = f"syn-{i:03d}"
        body = (
            f"Synthetic base note {i} about a fictional topic. "
            f"Speaker claimed something. Source: https://example.com/case/{i}\n"
        )
        (root / f"{nid}.md").write_text(_fm(nid, ntype) + body, encoding="utf-8")

    # exact byte-identical duplicate pair
    for nid in EXACT_DUP_PAIR:
        (root / f"{nid}.md").write_text(
            _fm(nid, "plain_text") + _DUP_BODY + "\n", encoding="utf-8"
        )

    # near-duplicate pair (same type, same head+tail, different middle)
    for nid in NEAR_DUP_PAIR:
        mid = f"MIDDLE-{nid}-" + "z" * 50
        (root / f"{nid}.md").write_text(
            _fm(nid, "plain_text") + _NEAR_HEAD + mid + _NEAR_TAIL + "\n", encoding="utf-8"
        )

    # shared-source pair (false-consensus risk)
    for nid in SHARED_PAIR:
        (root / f"{nid}.md").write_text(
            _fm(nid, "link")
            + f"Both notes cite the same secondary source. Source: https://{SHARED_HOST}/article\n",
            encoding="utf-8",
        )

    # explicit framed event date
    (root / f"{EVT_NOTE}.md").write_text(
        _fm(EVT_NOTE, "plain_text")
        + "The 2026年7月26日，世界人工智能大会正式开幕，规模为历届之最。\n",
        encoding="utf-8",
    )

    # missing created_at
    (root / f"{NO_CREATE_NOTE}.md").write_text(
        _fm(NO_CREATE_NOTE, "plain_text", created_at=None)
        + "Note without a created_at timestamp, for temporal-contract testing.\n",
        encoding="utf-8",
    )

    # malformed frontmatter (no closing delimiter) -> quarantine
    (root / f"{BADFM_NOTE}.md").write_text(
        "---\nnote_id: \"badfm\"\ntitle: \"Bad\"\nnote_type: \"plain_text\"\n"
        "This file never closes its frontmatter.\n",
        encoding="utf-8",
    )

    # index file (counts as +1 path, not a note)
    (root / INDEX_FILE).write_text(
        "# Synthetic index\n\n笔记总数：**29 条**\n", encoding="utf-8"
    )
    return root
