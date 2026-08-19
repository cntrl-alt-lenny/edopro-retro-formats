"""Command line interface: python -m retroformats <command>."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build import build_all
from .repo import Repository, find_repo_root
from .validate import Validator


def _load(args: argparse.Namespace) -> Repository:
    root = Path(args.root).resolve() if args.root else find_repo_root()
    return Repository.load(root)


def cmd_validate(args: argparse.Namespace) -> int:
    repo = _load(args)
    validator = Validator(repo)
    findings = validator.validate()
    for finding in findings:
        print(finding)
    print(
        f"\nvalidate: {len(repo.formats)} formats, {len(repo.banlists)} banlists, "
        f"{len(repo.pools)} pools, {len(repo.rule_profiles)} rule profiles, "
        f"{len(repo.errata)} errata -> {len(validator.errors)} errors, "
        f"{len(validator.warnings)} warnings"
    )
    if validator.errors:
        return 1
    if args.strict and validator.warnings:
        return 1
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    repo = _load(args)
    validator = Validator(repo)
    validator.validate()
    if validator.errors:
        for finding in validator.errors:
            print(finding, file=sys.stderr)
        print("build: refusing to build from invalid data", file=sys.stderr)
        return 1
    written = build_all(repo)
    for fmt_id, path in written.items():
        print(f"built {fmt_id} -> {path.relative_to(repo.root)}")
    if args.check:
        import subprocess

        diff = subprocess.run(
            ["git", "-C", str(repo.root), "status", "--porcelain", "--", "dist"],
            capture_output=True,
            text=True,
        )
        if diff.stdout.strip():
            print("build --check: dist/ is out of date with canonical data:", file=sys.stderr)
            print(diff.stdout, file=sys.stderr)
            return 1
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    repo = _load(args)
    print(f"{'format':<24} {'banlist':<14} {'pool':<10} {'rules':<8} {'errata':<8} overall")
    for fmt_id in sorted(repo.formats):
        fmt = repo.formats[fmt_id]
        s = fmt.implementation_status
        print(
            f"{fmt.id:<24} {s.get('banlist', '?'):<14} {s.get('card_pool', '?'):<10} "
            f"{s.get('rule_profile', '?'):<8} {s.get('errata', '?'):<8} {s.get('overall', '?')}"
        )
    if repo.products:
        from .releases import ReleaseIndex

        index = ReleaseIndex.build(repo)
        printings = sum(len(p.printings) for p in repo.products.values())
        events = sum(
            len(p.events) + sum(len(pr.events) for pr in p.printings)
            for p in repo.products.values()
        )
        undated = sum(
            1 for a in index.by_canonical.values() if not a.events and a.undated_printings
        )
        print(
            f"\nreleases: {len(repo.products)} products, {printings} printings, "
            f"{events} release events -> {index.dated_canonical_count()} dated canonical cards"
            + (f", {undated} undated" if undated else "")
        )
        if repo.release_coverage:
            for window in repo.release_coverage.windows:
                print(
                    f"  coverage [{window.get('status')}] {window.get('from')} .. {window.get('through')} "
                    f"({', '.join(window.get('territories', []))})"
                )
    return 0


def cmd_materialize(args: argparse.Namespace) -> int:
    from .importers.ignis_goat import write_json
    from .releases import ReleaseIndex, default_scope, evaluate_cutoff

    repo = _load(args)
    targets = [
        pool for pool in repo.pools.values()
        if pool.kind == "release-cutoff" and (not args.pools or pool.id in args.pools)
    ]
    for wanted in args.pools or []:
        if wanted not in {p.id for p in targets}:
            print(f"materialize: no release-cutoff pool with id {wanted!r}", file=sys.stderr)
            return 1
    if not targets:
        print("materialize: no release-cutoff pools found", file=sys.stderr)
        return 1

    index = ReleaseIndex.build(repo)
    failed = False
    for pool in sorted(targets, key=lambda p: p.id):
        cutoff_date = (pool.cutoff or {}).get("cutoff_date")
        scope = frozenset((pool.cutoff or {}).get("territories") or default_scope(pool.region))
        coverage = repo.release_coverage
        import datetime as _dt

        if coverage is None or not coverage.covers(_dt.date.fromisoformat(str(cutoff_date)), scope):
            print(
                f"{pool.id}: refusing to materialise - data/releases/coverage.json does not claim "
                f"complete coverage of {sorted(scope)} through {cutoff_date}",
                file=sys.stderr,
            )
            failed = True
            continue
        evaluation = evaluate_cutoff(pool, repo, index)
        if evaluation.ambiguous:
            for code in sorted(evaluation.ambiguous):
                refs = evaluation.ambiguous[code]
                spans = "; ".join(
                    f"{r.product_id} {r.event.date} ({r.event.precision}/{r.event.status})"
                    for r in refs[:3]
                )
                print(
                    f"{pool.id}: AMBIGUOUS passcode {code}: {spans} straddles cutoff {cutoff_date}; "
                    "add a sourced cutoff.include/exclude entry",
                    file=sys.stderr,
                )
            failed = True
            continue
        raw = dict(pool.raw)
        raw["cards"] = evaluation.cards()
        write_json(pool.path, raw)
        print(
            f"{pool.id}: materialised {len(evaluation.cards())} cards "
            f"(cutoff {cutoff_date}, scope {'+'.join(sorted(scope))}, "
            f"{len(evaluation.forced_in)} forced in, {len(evaluation.forced_out)} forced out)"
        )
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="retroformats",
        description="Validate canonical historical-format data and build EDOPro assets.",
    )
    parser.add_argument("--root", help="repository root (default: auto-detect from cwd)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="run all semantic checks")
    p_validate.add_argument("--strict", action="store_true", help="warnings also fail")
    p_validate.set_defaults(func=cmd_validate)

    p_build = sub.add_parser("build", help="regenerate dist/ from canonical data")
    p_build.add_argument(
        "--check", action="store_true", help="fail if dist/ changed (for CI: catches hand-edits)"
    )
    p_build.set_defaults(func=cmd_build)

    p_report = sub.add_parser("report", help="implementation status per format")
    p_report.set_defaults(func=cmd_report)

    p_mat = sub.add_parser(
        "materialize",
        help="derive release-cutoff pool card lists from data/releases/ and write them into the pool files",
    )
    p_mat.add_argument("pools", nargs="*", help="pool ids (default: every release-cutoff pool)")
    p_mat.set_defaults(func=cmd_materialize)

    args = parser.parse_args(argv)
    return args.func(args)
