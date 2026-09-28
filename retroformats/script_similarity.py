"""How close a generated card script is to an upstream one (roadmap item 7).

A generated script labelled `original` (data/custom-cards/c<passcode>.json,
`authorship.kind`) must measurably differ from Project Ignis's script for the
same card, whose licence is AGPL-3.0-or-later. Rounds 029 and 031 showed that a
script written "from scratch" by a model can still reproduce Ignis's from
memory, so the label is checked by measurement, not trusted:
tests/engine/test_script_origin.py compares every `original` script with
Ignis's script for its alias at the pinned CardScripts revision and fails
above `ORIGINAL_MAX_RATIO`.

The measure is the one rounds 029 and 031's reviews used: normalise both
files to their code lines (comments and blank lines dropped, whitespace
collapsed), then take difflib's line-sequence ratio. Shared 4-line windows are
reported as supporting detail only; they do not decide.

Standard library only.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

# Round 032 calibration (docs/rounds/032-derived-scripts-licence/builder.md),
# each script against Ignis's official script for its alias at CardScripts
# 383bfbd6:
#   too close (reviews found them to be adaptations):
#     Goddess of Whim 0.72, Soul Rope 0.71, Night Assailant 0.69,
#     Green Baboon 0.61, Rise of the Snake Deity 0.58, Strike Ninja 0.51
#   accepted as original: Stealth Union 0.31, Metalzoa 0.27, Malefic Blue-Eyes 0.13
# 0.40 sits in the gap between 0.31 and 0.51, nearer the accepted side, so a
# borderline script is flagged rather than passed: the cost of a false flag is
# a relabel to `derived`; the cost of a false pass is mislicensed code.
ORIGINAL_MAX_RATIO = 0.40

WINDOW = 4

_COMMENT = re.compile(r"--.*$")
_SPACE = re.compile(r"\s+")


def code_lines(text: str) -> list[str]:
    """The script's code lines: line comments removed, whitespace collapsed,
    blank lines dropped. A `--` inside a string literal is also cut, which
    only ever makes two scripts look slightly less alike, never more."""
    lines = []
    for raw in text.splitlines():
        line = _SPACE.sub(" ", _COMMENT.sub("", raw)).strip()
        if line:
            lines.append(line)
    return lines


@dataclass(frozen=True)
class Similarity:
    ratio: float
    identical_lines: int
    lines: int
    shared_windows: int
    windows: int


def measure(script: str, upstream: str) -> Similarity:
    a, b = code_lines(script), code_lines(upstream)
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    same = sum(block.size for block in matcher.get_matching_blocks())
    wins_a = [tuple(a[i : i + WINDOW]) for i in range(len(a) - WINDOW + 1)]
    wins_b = {tuple(b[i : i + WINDOW]) for i in range(len(b) - WINDOW + 1)}
    return Similarity(
        ratio=matcher.ratio(),
        identical_lines=same,
        lines=len(a),
        shared_windows=sum(1 for w in wins_a if w in wins_b),
        windows=len(wins_a),
    )


def too_close(similarity: Similarity) -> bool:
    return similarity.ratio >= ORIGINAL_MAX_RATIO
