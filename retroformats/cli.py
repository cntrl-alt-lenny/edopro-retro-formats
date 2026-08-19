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
    return 0


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

    args = parser.parse_args(argv)
    return args.func(args)
