"""Build all generated outputs into dist/."""

from __future__ import annotations

from pathlib import Path

from .lflist import build_lflist
from .repo import Repository


def build_all(repo: Repository, dist: Path | None = None) -> dict[str, Path]:
    """Regenerate every dist/ artifact. Returns {format id: written path}.

    Outputs are deterministic; running twice without data changes must be a
    no-op at the byte level (tests/test_build.py enforces this).
    """
    dist = dist or (repo.root / "dist")
    lflist_dir = dist / "lflists"
    lflist_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for fmt_id in sorted(repo.formats):
        fmt = repo.formats[fmt_id]
        if fmt.banlist_id not in repo.banlists or fmt.pool_id not in repo.pools:
            continue  # validator reports the broken reference
        built = build_lflist(fmt, repo)
        out = lflist_dir / f"{fmt.id}.lflist.conf"
        out.write_text(built.text, encoding="utf-8", newline="\n")
        written[fmt.id] = out
    return written
