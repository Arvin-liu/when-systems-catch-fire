"""CLI entry point with hard mode boundaries (design B §1).

RUN is the default and never imports or calls the review/engineering modes;
those are imported lazily only inside their own dispatch branches, so the RUN
code path never loads them (static + runtime mode gate).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import AuthorizationError, ModeBoundaryError
from .providers import FixtureProvider, FileSystemProvider
from .store import StoreLayout


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ignition_runtime", description="Ignition RUN/PROMOTE/EVOLVE runtime")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_store(sp):
        sp.add_argument("--store", required=True, type=Path, help="store directory")
        sp.add_argument("--provider", default="fixture", help="fixture | filesystem")
        sp.add_argument("--inputs", type=Path, default=None, help="inputs root for filesystem provider")
        sp.add_argument("--materials", default=None, help="comma-separated material ids (fixture)")

    runp = sub.add_parser("run")
    add_store(runp)
    runp.add_argument("--authorize", default=None,
                      help="forbidden on RUN (raises ModeBoundaryError if set)")
    runp.add_argument("--crash-after", default="none",
                      choices=["none", "write_files", "manifest", "staged", "swap"])

    resp = sub.add_parser("resume")
    add_store(resp)
    resp.add_argument("--authorize", default=None,
                      help="forbidden on RESUME (raises ModeBoundaryError if set)")

    recp = sub.add_parser("recover")
    add_store(recp)
    recp.add_argument("--authorize", default=None,
                      help="forbidden on RECOVER (raises ModeBoundaryError if set)")

    promp = sub.add_parser("promote")
    add_store(promp)
    promp.add_argument("--authorize", required=True, help="promote:<token>")
    promp.add_argument("--candidate", default=None, help="comma-separated candidate ids")
    promp.add_argument("--approve", default=None, help="request generation id to approve")
    promp.add_argument("--crash-after", default="none",
                       choices=["none", "write_files", "manifest", "staged", "swap"])

    evp = sub.add_parser("evolve")
    add_store(evp)
    evp.add_argument("--authorize", required=True, help="evolve:<token>")
    evp.add_argument("--approved-signal", required=True, help="approved engineering signal id")
    evp.add_argument("--crash-after", default="none",
                     choices=["none", "write_files", "manifest", "staged", "swap"])
    return p


def make_provider(args) -> object:
    if getattr(args, "provider", "fixture") == "filesystem":
        if args.inputs is None:
            raise ModeBoundaryError("filesystem provider requires --inputs")
        return FileSystemProvider(args.inputs)
    return FixtureProvider(
        refs=[m for m in (args.materials or "").split(",") if m] or None
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = StoreLayout(args.store)

    if args.cmd == "run":
        # RUN path: never touches the review/engineering modes.
        if getattr(args, "authorize", None):
            raise ModeBoundaryError("RUN must not carry promotion/evolution authorization")
        from .run import run

        gen_id = run(store, make_provider(args), crash_after=args.crash_after)
        print(gen_id)
        return 0

    if args.cmd == "resume":
        from .recovery import resume

        gen_id = resume(store, make_provider(args))
        print(gen_id)
        return 0

    if args.cmd == "recover":
        from .recovery import recover

        gen_id = recover(store)
        print(gen_id or "")
        return 0

    if args.cmd == "promote":
        # Review pathway: lazy import keeps it out of the RUN path.
        if not args.authorize.startswith("promote:"):
            raise AuthorizationError("promotion requires --authorize promote:<token>")
        token = args.authorize[len("promote:"):]
        from .promote import promote_approval, promote_request

        if args.approve:
            gen_id = promote_approval(
                store, make_provider(args), authorized_by=token, request_gen_id=args.approve,
                crash_after=args.crash_after,
            )
        else:
            cand = [c for c in (args.candidate or "").split(",") if c] or None
            gen_id = promote_request(
                store, make_provider(args), authorized_by=token, candidate_refs=cand,
                crash_after=args.crash_after,
            )
        print(gen_id)
        return 0

    if args.cmd == "evolve":
        if not args.authorize.startswith("evolve:"):
            raise AuthorizationError("engineering work requires --authorize evolve:<token>")
        token = args.authorize[len("evolve:"):]
        from .evolve import evolve

        gen_id = evolve(
            store, make_provider(args), authorized_by=token,
            approved_signal_id=args.approved_signal, crash_after=args.crash_after,
        )
        print(gen_id)
        return 0

    raise ModeBoundaryError(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
