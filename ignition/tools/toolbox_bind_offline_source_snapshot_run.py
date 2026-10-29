#!/usr/bin/env python3
"""Run the E37 saved-source adapter with digest locks and no repository writes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from ignition.research_workflow import slot  # noqa: E402


RUN_FIELDS = (
    "question",
    "output_dir",
    "draft",
    "claim_reviews",
    "task_id",
    "episode_id",
    "source_set_id",
    "namespace",
    "authorization_scope",
    "expected_source_set_digest",
)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _outside_repository_output(value: str) -> Path:
    requested = Path(value).expanduser()
    if requested.is_symlink():
        raise ValueError("output directory must not be a symlink")
    resolved = requested.resolve()
    repository = REPO_ROOT.resolve()
    try:
        resolved.relative_to(repository)
    except ValueError:
        pass
    else:
        raise ValueError("output directory must be outside the checked-out repository")
    try:
        repository.relative_to(resolved)
    except ValueError:
        pass
    else:
        raise ValueError("output directory must not contain the checked-out repository")
    return resolved


def _current_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise ValueError("cannot read the checked-out implementation commit") from exc
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError("cannot read the checked-out implementation commit")
    return result.stdout.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-snapshots", required=True)
    parser.add_argument("--expected-digests", required=True)
    parser.add_argument("--query-count", type=_positive_int, default=12)
    parser.add_argument(
        "--print-source-set-digest",
        action="store_true",
        help="verify capture locks and print the canonical source-set digest without creating run files",
    )
    parser.add_argument("--question")
    parser.add_argument("--output-dir")
    parser.add_argument("--draft")
    parser.add_argument("--claim-reviews")
    parser.add_argument("--task-id")
    parser.add_argument("--episode-id")
    parser.add_argument("--source-set-id")
    parser.add_argument("--namespace")
    parser.add_argument("--authorization-scope")
    parser.add_argument("--expected-source-set-digest")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.print_source_set_digest:
            if any(getattr(args, field) is not None for field in RUN_FIELDS):
                parser.error("digest preview does not accept run-only arguments")
            sources, _, _, _, _ = slot._snapshot_sources(
                args.source_snapshots,
                args.expected_digests,
                args.query_count,
            )
            digest = slot._canonical_source_set_digest(sources)
            print(json.dumps({
                "adapter_id": "e37-source-snapshot-v1",
                "source_count": len(sources),
                "canonical_source_set_sha256": digest,
                "network_requests": 0,
            }, ensure_ascii=False, sort_keys=True))
            return 0

        missing = [field.replace("_", "-") for field in RUN_FIELDS if not getattr(args, field)]
        if missing:
            parser.error("run mode requires " + ", ".join("--" + field for field in missing))
        output_dir = _outside_repository_output(args.output_dir)
        receipt = slot.run_binding(
            adapter_id="e37-source-snapshot-v1",
            question=args.question,
            output_dir=output_dir,
            draft_path=args.draft,
            claim_review_path=args.claim_reviews,
            task_id=args.task_id,
            episode_id=args.episode_id,
            source_set_id=args.source_set_id,
            namespace=args.namespace,
            authorization_scope=args.authorization_scope,
            implementation_commit=_current_commit(),
            expected_source_set_digest=args.expected_source_set_digest,
            source_snapshots_path=args.source_snapshots,
            expected_digests_path=args.expected_digests,
            query_count=args.query_count,
        )
    except (ValueError, FileExistsError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "adapter_id": receipt["context"]["adapter_id"],
        "status": receipt["status"],
        "acquisition_status": receipt["acquisition_status"],
        "claim_review_status": receipt["claim_review_status"],
        "receipt": str(output_dir / "receipt.json"),
    }, ensure_ascii=False, sort_keys=True))
    return 0 if receipt["status"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
