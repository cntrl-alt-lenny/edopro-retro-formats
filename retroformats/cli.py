"""Command line interface: python -m retroformats <command>."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build import build_all
from .deckcheck import FORBIDDEN_TYPE_NOTE, parse_ydk, check_deck
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
    _report_errata(repo, verbose=args.verbose)
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


def _report_errata(repo: Repository, verbose: bool = False) -> None:
    """Certification state of the historical-card-behaviour dataset, and the
    per-format consequences: which cards each format substitutes, and which
    period behaviours it is knowingly NOT reproducing."""
    from collections import Counter

    from .lflist import historical_identity, select_applicable_errata
    from .model import ErratumV2

    errata = list(repo.errata.values())
    if not errata:
        return
    # v1 and v2 are entirely different record shapes (design doc §8's hard
    # legacy/v2 boundary) — the existing v1-only stats block stays exactly
    # as it was, scoped to v1 records, so today's all-v1 corpus prints
    # byte-identical output; v2 gets its own small, separate summary line.
    v1_errata = [e for e in errata if not isinstance(e, ErratumV2)]
    v2_errata = [e for e in errata if isinstance(e, ErratumV2)]

    reviewed = [e for e in v1_errata if e.review_status == "reviewed"]
    kinds = Counter(e.classification for e in v1_errata)
    strategies = Counter(e.implementation.get("strategy") for e in v1_errata)
    dated = sum(
        1
        for e in reviewed
        if any((c.get("effective") or {}).get("date") for c in e.relevant_changes())
    )
    bounded = sum(
        1
        for e in reviewed
        if not any((c.get("effective") or {}).get("date") for c in e.relevant_changes())
        and any(
            (c.get("effective") or {}).get("old_attested_through")
            or (c.get("effective") or {}).get("new_attested_from")
            for c in e.relevant_changes()
        )
    )
    multi = [e for e in v1_errata if len(e.relevant_changes()) > 1]
    # Behavioural coverage is per IMPLEMENTATION, not per record: a card with
    # three eras can have one of them executed against the engine.
    tested = sum(
        1
        for e in v1_errata
        for impl in [e.implementation, *(c.get("resulting_implementation") for c in e.changes)]
        if impl and impl.get("tested")
    )
    tested_records = sum(
        1
        for e in v1_errata
        if any(
            impl and impl.get("tested")
            for impl in [
                e.implementation,
                *(c.get("resulting_implementation") for c in e.changes),
            ]
        )
    )

    print(
        f"\nerrata: {len(v1_errata)} records ({len(reviewed)} reviewed) -> "
        + ", ".join(f"{n} {k}" for k, n in sorted(kinds.items()))
    )
    print(
        f"  chronology: {dated} exactly dated, {bounded} bounded, "
        f"{len(reviewed) - dated - bounded} unresolved (of reviewed)"
    )
    print(
        "  strategies: " + ", ".join(f"{n} {s}" for s, n in sorted(strategies.items()))
        + f"; {len(multi)} with multiple historical revisions; "
        + f"{tested} implementations behaviourally tested across {tested_records} records"
    )
    if v2_errata:
        v2_reviewed = sum(1 for e in v2_errata if e.review_status == "reviewed")
        v2_kinds = Counter(e.classification for e in v2_errata)
        print(
            f"  v2 (historical-event DAG): {len(v2_errata)} records ({v2_reviewed} reviewed) -> "
            + ", ".join(f"{n} {k}" for k, n in sorted(v2_kinds.items()))
        )

    for fmt_id in sorted(repo.formats):
        fmt = repo.formats[fmt_id]
        if not fmt.snapshot:
            continue
        try:
            selected = select_applicable_errata(fmt, repo)
        except Exception as exc:  # ErrataSelectionError and friends
            print(f"  {fmt.id}: SELECTION BLOCKED - {exc}")
            continue
        divergences, known_wrong = [], []
        snapshot = _dt_date(fmt.snapshot)
        policy = (fmt.unresolved_policy or {}).get("choice")
        for erratum in repo.errata.values():
            if erratum.id in fmt.errata_exclude or erratum.review_status != "reviewed":
                continue
            if isinstance(erratum, ErratumV2):
                if not erratum.has_implementation_relevant_history():
                    continue
                from .model import Coverage

                selection = erratum.selection_at(snapshot)
                if (
                    selection.chronology == "determinate"
                    and selection.candidates[0].coverage.kind == Coverage.KNOWN_GAP
                ):
                    divergences.append(erratum)
                elif selection.chronology == "ambiguous" and policy == "modern" and not selection.modern_is_possible:
                    known_wrong.append(erratum)
                continue
            if not erratum.relevant_changes():
                continue
            selection = erratum.selection_at(snapshot)
            if selection.state == "gap" and selection.acknowledged_gap:
                divergences.append(erratum)
            elif (
                selection.state == "ambiguous"
                and policy == "modern"
                and not selection.modern_is_possible
            ):
                known_wrong.append(erratum)
        print(
            f"  {fmt.id}: {len(selected)} historical substitutions, "
            f"{len(divergences)} acknowledged behavioural divergences, "
            f"{len(known_wrong)} known-wrong modern fallbacks"
        )
        if verbose:
            for code, override in sorted(selected.items()):
                passcode, _variants = historical_identity(override.implementation)
                print(f"      {code} -> {passcode} {override.erratum.modern_card.name}")
            for erratum in sorted(divergences, key=lambda e: e.modern_card.name):
                print(f"      (divergence) {erratum.modern_card.name}")
            for erratum in sorted(known_wrong, key=lambda e: e.modern_card.name):
                print(f"      (known-wrong modern) {erratum.modern_card.name}")


def _dt_date(value: str):
    import datetime as _dt

    return _dt.date.fromisoformat(value)


def cmd_materialize(args: argparse.Namespace) -> int:
    import datetime as _dt

    from .importers.ignis_goat import write_json
    from .releases import ReleaseIndex, default_scope, materialize_pool

    repo = _load(args)

    # Same contract as build: never derive from invalid data. This is also
    # what keeps malformed dates from surfacing as raw tracebacks here.
    validator = Validator(repo)
    validator.validate()
    blocking = [
        f for f in validator.errors
        if f.code.startswith(("releases.", "coverage.", "gaps.", "load.", "pool.", "card.", "sources."))
    ]
    if blocking:
        for finding in blocking:
            print(finding, file=sys.stderr)
        print("materialize: refusing to derive pools from invalid data", file=sys.stderr)
        return 1

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
        if coverage is None or not coverage.covers(
            _dt.date.fromisoformat(str(cutoff_date)), scope, repo.release_gaps
        ):
            print(
                f"{pool.id}: refusing to materialise - coverage of {sorted(scope)} through "
                f"{cutoff_date} cannot be certified (no claimed-complete window, or an "
                "unresolved pool-impacting gap overlaps it)",
                file=sys.stderr,
            )
            failed = True
            continue
        raw, evaluation = materialize_pool(pool, repo, index)
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
        write_json(pool.path, raw)
        print(
            f"{pool.id}: materialised {len(raw['cards'])} cards "
            f"(cutoff {cutoff_date}, scope {'+'.join(sorted(scope))}, "
            f"{len(evaluation.forced_in)} forced in, {len(evaluation.forced_out)} forced out)"
        )
    return 1 if failed else 0


def cmd_check_deck(args: argparse.Namespace) -> int:
    repo = _load(args)
    fmt = repo.formats.get(args.format)
    if fmt is None:
        print(
            f"check-deck: unknown format {args.format!r}; known formats: "
            + ", ".join(sorted(repo.formats)),
            file=sys.stderr,
        )
        return 2
    path = Path(args.ydk)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"check-deck: cannot read {path}: {exc}", file=sys.stderr)
        return 2
    deck = parse_ydk(text)
    print(
        f"{path.name}: {len(deck.main)} main, {len(deck.extra)} extra, "
        f"{len(deck.side)} side against {fmt.id}"
    )
    result = check_deck(deck, fmt, repo)
    if result.legal:
        print("LEGAL: no violations found")
    else:
        print(f"ILLEGAL: {len(result.findings)} violation(s)")
        for finding in result.findings:
            print(f"  [{finding.code}] {finding.message}")
    print(FORBIDDEN_TYPE_NOTE)
    return 0 if result.legal else 1


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
    p_report.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="list every historical substitution and acknowledged divergence per format",
    )
    p_report.set_defaults(func=cmd_report)

    p_mat = sub.add_parser(
        "materialize",
        help="derive release-cutoff pool card lists from data/releases/ and write them into the pool files",
    )
    p_mat.add_argument("pools", nargs="*", help="pool ids (default: every release-cutoff pool)")
    p_mat.set_defaults(func=cmd_materialize)

    p_check = sub.add_parser(
        "check-deck",
        help="check a .ydk deck file against one of the three formats' shipped whitelist",
    )
    p_check.add_argument("ydk", help="path to a .ydk deck file")
    p_check.add_argument("format", help="format id, e.g. 2005-04-goat")
    p_check.set_defaults(func=cmd_check_deck)

    args = parser.parse_args(argv)
    return args.func(args)
