#!/usr/bin/env python3

"""Fetch, verify and build the pinned inputs the duel-engine tests need, then
run those tests with no skips allowed.

    python scripts/engine_env.py prepare --dest DIR   # network: fetch + build
    python scripts/engine_env.py verify  --dest DIR   # offline: re-check pins
    python scripts/engine_env.py run     --dest DIR --expect-at-least N

`tests/engine/` needs three things the standard-library-only main suite does
not have: the ocgcore library, BabelCDB and CardScripts. Every one of them is
taken at the revision this project claims, so a moved upstream cannot silently
change what is tested (docs/engine-testing.md, "Pinned inputs"):

- BabelCDB, CardScripts and ygopro-core are fetched by full commit hash at the
  `revision` recorded in data/sources.json, then `git rev-parse HEAD` must equal
  that revision and no tracked file may differ from it.
- Lua is the core's own submodule (`lua/src`); its commit is read from the
  core's tree at the pinned revision and fetched and checked the same way.
- premake5 (the core's own build tool) is downloaded and its SHA-256 checked
  against the checksum in this file before it is unpacked.
- The core is then compiled from that source. A prebuilt binary is deliberately
  not used: nothing ties one to a source revision (see docs/engine-testing.md).

`run` refuses to pass unless every discovered engine test executed. A skip, a
failure, an error, an expected failure, or fewer executed tests than
`--expect-at-least` all exit non-zero, because a job that goes green by
skipping is the failure this exists to prevent.

Standard library only (Python 3.10+); needs git, a C++17 compiler and make.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources.json"

# Local name -> id of the record in data/sources.json that pins it.
PINNED_REPOS = {
    "babelcdb": "ignis-babelcdb",
    "cardscripts": "ignis-cardscripts",
    "core": "ygopro-core",
}

# The build tool the core's own scripts/install-premake5.sh downloads.
PREMAKE_VERSION = "5.0.0-beta2"
PREMAKE_SHA256 = {
    "linux": "4186b8fd66b55df935280f55663c6e46fd568799d89b7ff6a3cfb20d58ff6224",
    "macosx": "620778e24847d4f8e2380cd98922977afec77cc8e805a77edcae1c05e0f6d44a",
}

_REVISION = re.compile(r"^[0-9a-f]{40}$")


class EngineEnvError(RuntimeError):
    pass


# -- pins ---------------------------------------------------------------------


def load_pins(sources_path: Path = SOURCES) -> dict[str, tuple[str, str]]:
    """{local name: (repository url, full 40-hex commit)} from data/sources.json."""
    records = {s["id"]: s for s in json.loads(sources_path.read_text(encoding="utf-8"))["sources"]}
    pins = {}
    for name, source_id in PINNED_REPOS.items():
        record = records.get(source_id)
        if record is None:
            raise EngineEnvError(f"data/sources.json has no record {source_id!r}")
        revision = str(record.get("revision", ""))
        if not _REVISION.match(revision):
            raise EngineEnvError(f"{source_id}: revision {revision!r} is not a full 40-hex commit")
        pins[name] = (str(record["url"]), revision)
    return pins


# -- git ----------------------------------------------------------------------


def _git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise EngineEnvError(f"git {' '.join(args)} (in {cwd}) exited {proc.returncode}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def verify_checkout(path: Path, revision: str) -> None:
    """The checkout is exactly `revision`, and no tracked file differs from it."""
    if not (path / ".git").exists():
        raise EngineEnvError(f"{path} is not a git checkout")
    head = _git(["rev-parse", "HEAD"], path)
    if head != revision:
        raise EngineEnvError(f"{path} is at {head}, expected pinned {revision}")
    dirty = _git(["status", "--porcelain", "--untracked-files=no"], path)
    if dirty:
        raise EngineEnvError(f"{path} has modified tracked files:\n{dirty}")


def fetch_pinned(url: str, revision: str, dest: Path) -> None:
    """Fetch exactly `revision` of `url` into `dest` and verify it.

    An existing checkout that already verifies is reused; anything else is
    discarded and fetched again. Fetching by full commit hash means the
    server either serves that commit or the fetch fails - a moved branch
    cannot substitute a different one.
    """
    try:
        verify_checkout(dest, revision)
        return
    except EngineEnvError:
        pass
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    _git(["init", "-q"], dest)
    _git(["remote", "add", "origin", url], dest)
    _git(["fetch", "-q", "--depth", "1", "origin", revision], dest)
    _git(["checkout", "-q", "--detach", "FETCH_HEAD"], dest)
    verify_checkout(dest, revision)


def fetch_lua(core: Path) -> str:
    """Fetch the core's Lua submodule at the commit the core's tree pins."""
    entry = _git(["ls-tree", "HEAD", "lua/src"], core)
    mode, kind, rest = entry.split(None, 2)
    if (mode, kind) != ("160000", "commit"):
        raise EngineEnvError(f"lua/src in the core is {mode} {kind}, expected a submodule gitlink")
    lua_revision = rest.split()[0]
    url = _git(["config", "-f", ".gitmodules", "--get", "submodule.lua/src.url"], core)
    fetch_pinned(url, lua_revision, core / "lua" / "src")
    return lua_revision


# -- premake and the core build -----------------------------------------------


def _premake_platform() -> str:
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "macosx"
    raise EngineEnvError(f"no pinned premake5 for platform {sys.platform!r}")


def download_verified(url: str, sha256: str, dest: Path) -> None:
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 - fixed https URL
        data = response.read()
    digest.update(data)
    if digest.hexdigest() != sha256:
        raise EngineEnvError(f"{url}: sha256 {digest.hexdigest()} != pinned {sha256}")
    dest.write_bytes(data)


def install_premake(work: Path) -> Path:
    plat = _premake_platform()
    archive = work / f"premake-{PREMAKE_VERSION}-{plat}.tar.gz"
    download_verified(
        f"https://github.com/premake/premake-core/releases/download/v{PREMAKE_VERSION}/{archive.name}",
        PREMAKE_SHA256[plat],
        archive,
    )
    target = work / "premake"
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir()
    binary = target / "premake5"
    with tarfile.open(archive) as tar:
        source = tar.extractfile("./premake5")
        if source is None:
            raise EngineEnvError(f"{archive.name} has no ./premake5 file")
        binary.write_bytes(source.read())
    binary.chmod(0o755)
    return binary


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_core(core: Path, premake: Path) -> Path:
    """Build the shared ocgcore exactly as the core's scripts/build-premake5.sh does."""
    shutil.copy2(premake, core / "premake5")
    subprocess.run([str(core / "premake5"), "gmake2"], cwd=core, check=True)
    subprocess.run(
        ["make", "-C", "build", "ocgcoreshared", "config=release", f"-j{os.cpu_count() or 2}"],
        cwd=core,
        check=True,
    )
    matches = sorted((core / "bin" / "release").glob("libocgcore.*"))
    if not matches:
        raise EngineEnvError(f"build produced no libocgcore.* under {core / 'bin' / 'release'}")
    return matches[0]


# -- commands -----------------------------------------------------------------


def _compiler_version() -> str:
    for cc in ("c++", "g++", "clang++"):
        if shutil.which(cc):
            out = subprocess.run([cc, "--version"], capture_output=True, text=True, check=False).stdout
            return out.splitlines()[0] if out else cc
    return "unknown"


def prepare(dest: Path) -> dict:
    pins = load_pins()
    repos = dest / "repos"
    engine = dest / "engine"
    work = dest / "work"
    for directory in (repos, engine, work):
        directory.mkdir(parents=True, exist_ok=True)

    fetch_pinned(*pins["babelcdb"], repos / "babelcdb")
    fetch_pinned(*pins["cardscripts"], repos / "cardscripts")
    core = work / "ygopro-core"
    fetch_pinned(*pins["core"], core)
    lua_revision = fetch_lua(core)
    premake = install_premake(work)
    built = build_core(core, premake)

    library = engine / built.name
    shutil.copy2(built, library)
    manifest = {
        "babelcdb": pins["babelcdb"][1],
        "cardscripts": pins["cardscripts"][1],
        "ygopro_core_source": pins["core"][1],
        "lua_source": lua_revision,
        "premake": f"{PREMAKE_VERSION} ({_premake_platform()}) sha256 {PREMAKE_SHA256[_premake_platform()]}",
        "library": library.name,
        "library_sha256": _sha256_file(library),
        "library_size": library.stat().st_size,
        "compiler": _compiler_version(),
        "platform": f"{platform.system()} {platform.machine()}",
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify(dest: Path) -> dict:
    """Offline re-check that what is on disk is what the pins and the manifest say."""
    pins = load_pins()
    manifest_path = dest / "manifest.json"
    if not manifest_path.exists():
        raise EngineEnvError(f"{manifest_path} missing - run `prepare` first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verify_checkout(dest / "repos" / "babelcdb", pins["babelcdb"][1])
    verify_checkout(dest / "repos" / "cardscripts", pins["cardscripts"][1])
    verify_checkout(dest / "work" / "ygopro-core", pins["core"][1])
    if manifest.get("ygopro_core_source") != pins["core"][1]:
        raise EngineEnvError("manifest was built from a different ygopro-core revision than data/sources.json pins")
    library = dest / "engine" / manifest["library"]
    if not library.exists() or _sha256_file(library) != manifest["library_sha256"]:
        raise EngineEnvError(f"{library} does not match the checksum recorded when it was built")
    return manifest


def evaluate_result(result: unittest.TestResult, expect_at_least: int) -> list[str]:
    """Why this engine run must not count as a pass; empty means it may."""
    problems = []
    executed = result.testsRun - len(result.skipped)
    if result.skipped:
        names = ", ".join(sorted(str(test) for test, _ in result.skipped)[:5])
        problems.append(f"{len(result.skipped)} engine test(s) skipped (first: {names})")
    if result.failures or result.errors:
        problems.append(f"{len(result.failures)} failure(s), {len(result.errors)} error(s)")
    if result.expectedFailures or result.unexpectedSuccesses:
        problems.append(
            f"{len(result.expectedFailures)} expected failure(s), "
            f"{len(result.unexpectedSuccesses)} unexpected success(es) - engine tests must simply pass"
        )
    if executed < expect_at_least:
        problems.append(f"only {executed} engine test(s) executed, at least {expect_at_least} required")
    return problems


def run(dest: Path, expect_at_least: int) -> int:
    manifest = verify(dest)
    print("engine environment (verified against data/sources.json):", flush=True)
    print(json.dumps(manifest, indent=2), flush=True)
    os.environ["RETROFORMATS_OCGCORE"] = str(dest / "engine" / manifest["library"])
    os.environ["RETROFORMATS_REPOS"] = str(dest / "repos")
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.discover(start_dir="tests/engine", top_level_dir=".")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    problems = evaluate_result(result, expect_at_least)
    executed = result.testsRun - len(result.skipped)
    print(
        f"engine-tests: executed={executed} skipped={len(result.skipped)} "
        f"failures={len(result.failures)} errors={len(result.errors)} "
        f"(required: at least {expect_at_least} executed, 0 skipped)"
    )
    if problems:
        for problem in problems:
            print(f"engine-tests: FAIL - {problem}", file=sys.stderr)
        return 1
    print("engine-tests: PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "verify", "run"):
        p = sub.add_parser(name)
        p.add_argument("--dest", type=Path, required=True, help="directory holding repos/, engine/ and work/")
        if name == "run":
            p.add_argument("--expect-at-least", type=int, required=True, help="minimum engine tests that must execute")
    args = parser.parse_args(argv)
    dest = args.dest.resolve()
    try:
        if args.command == "prepare":
            print(json.dumps(prepare(dest), indent=2))
            return 0
        if args.command == "verify":
            print(json.dumps(verify(dest), indent=2))
            return 0
        return run(dest, args.expect_at_least)
    except (EngineEnvError, subprocess.CalledProcessError, OSError) as exc:
        print(f"engine_env: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
