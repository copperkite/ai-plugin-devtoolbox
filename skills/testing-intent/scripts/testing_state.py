#!/usr/bin/env python3
"""Named testing state as JSON: runner, changed source, unpaired files.

Workflows consume this output. They do not re-walk the tree to recompute pairing.
Stdlib only. Deterministic. Safe to run in a repository of any language.

schemaVersion is bumped only when an existing field changes meaning. New fields
are additive.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCHEMA_VERSION = 1

SKIP_DIRS = {
    ".git", ".hg", ".svn",
    "node_modules", "vendor", "dist", "build", "coverage",
    ".venv", "venv", "__pycache__", ".tox", "target",
}

CODE_SUFFIXES = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".py", ".go", ".rs", ".java", ".kt", ".rb", ".swift",
}

TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec"}

MAKE_TEST_RE = re.compile(r"^test\s*:", re.M)
PYTEST_TOML_RE = re.compile(r"(?m)^\[tool\.pytest")


def git(root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=check,
    )


def git_out(root: Path, args: list[str]) -> str:
    result = git(root, args, check=False)
    if result.returncode != 0:
        return ""
    # rstrip only — porcelain " M path" carries a leading space that strip() would eat.
    return result.stdout.rstrip("\n")


def is_git_repo(root: Path) -> bool:
    result = git(root, ["rev-parse", "--is-inside-work-tree"], check=False)
    return result.returncode == 0 and result.stdout.strip() == "true"


def current_branch(root: Path) -> str | None:
    name = git_out(root, ["branch", "--show-current"])
    return name or None


def default_branch(root: Path) -> str | None:
    origin_head = git_out(root, ["symbolic-ref", "refs/remotes/origin/HEAD", "--short"])
    if origin_head.startswith("origin/"):
        return origin_head[len("origin/"):]
    for name in ("main", "master"):
        if git_out(root, ["rev-parse", "--verify", f"refs/heads/{name}"]):
            return name
    return current_branch(root)


def posix(rel: Path | str) -> str:
    return Path(rel).as_posix()


def is_test_path(rel: str) -> bool:
    parts = Path(rel).parts
    if any(part in TEST_DIR_NAMES for part in parts):
        return True
    stem = Path(rel).stem
    if stem.startswith("test_") or stem.endswith("_test"):
        return True
    if ".test." in Path(rel).name or ".spec." in Path(rel).name:
        return True
    return False


def is_source_path(rel: str) -> bool:
    path = Path(rel)
    if any(part in SKIP_DIRS for part in path.parts):
        return False
    if path.name.endswith(".d.ts"):
        return False
    if is_test_path(rel):
        return False
    return path.suffix in CODE_SUFFIXES


def changed_paths(root: Path) -> list[str]:
    names: set[str] = set()
    default = default_branch(root)
    branch = current_branch(root)
    if default and branch and default != branch:
        merge_base = git_out(root, ["merge-base", default, "HEAD"])
        if merge_base:
            raw = git_out(root, ["diff", "--name-only", f"{merge_base}...HEAD"])
            names.update(line for line in raw.splitlines() if line)
    # Working tree: staged, unstaged, untracked (not ignored).
    raw = git_out(root, ["status", "--porcelain", "-uall"])
    for line in raw.splitlines():
        if len(line) < 4 or line[2] != " ":
            continue
        # status --porcelain: two-char XY, a space, then PATH (or "orig -> PATH").
        body = line[3:]
        if " -> " in body:
            body = body.split(" -> ", 1)[1]
        names.add(body)
    return sorted(posix(n) for n in names if n)


def discover_runner(root: Path) -> dict | None:
    makefile = root / "Makefile"
    if makefile.is_file():
        try:
            text = makefile.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if MAKE_TEST_RE.search(text):
            return {"command": ["make", "test"], "source": "makefile"}

    package = root / "package.json"
    if package.is_file():
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        scripts = data.get("scripts") if isinstance(data, dict) else None
        if isinstance(scripts, dict) and "test" in scripts:
            if (root / "pnpm-lock.yaml").is_file() or (root / "pnpm-workspace.yaml").is_file():
                return {"command": ["pnpm", "test"], "source": "package.json"}
            if (root / "yarn.lock").is_file():
                return {"command": ["yarn", "test"], "source": "package.json"}
            if (root / "bun.lockb").is_file() or (root / "bun.lock").is_file():
                return {"command": ["bun", "test"], "source": "package.json"}
            return {"command": ["npm", "test"], "source": "package.json"}

    if (root / "Cargo.toml").is_file():
        return {"command": ["cargo", "test"], "source": "cargo"}
    if (root / "go.mod").is_file():
        return {"command": ["go", "test", "./..."], "source": "go"}

    pyproject = root / "pyproject.toml"
    if (root / "pytest.ini").is_file() or (root / "conftest.py").is_file():
        return {"command": ["python3", "-m", "pytest"], "source": "pytest"}
    if pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if PYTEST_TOML_RE.search(text) or "pytest" in text:
            return {"command": ["python3", "-m", "pytest"], "source": "pytest"}

    tests_dir = root / "tests"
    if tests_dir.is_dir():
        for _dirpath, dirnames, filenames in os.walk(tests_dir):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            if any(name.endswith("_test.py") or name.startswith("test_") for name in filenames):
                return {
                    "command": [
                        "python3", "-m", "unittest", "discover",
                        "-s", "tests", "-p", "*_test.py",
                    ],
                    "source": "unittest",
                }

    return None


def colocated_candidates(rel: str) -> list[str]:
    path = Path(rel)
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    names = [
        f"{stem}.test{suffix}",
        f"{stem}.spec{suffix}",
        f"{stem}_test{suffix}",
        f"test_{stem}{suffix}",
    ]
    return [posix(parent / name) for name in names]


def index_test_files(root: Path) -> list[str]:
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel_dir = Path(dirpath).relative_to(root)
        for name in filenames:
            rel = posix(rel_dir / name) if str(rel_dir) != "." else name
            if is_test_path(rel):
                found.append(rel)
    return found


def stem_matches(test_rel: str, source_stem: str) -> bool:
    test_stem = Path(test_rel).stem
    return test_stem in {
        source_stem,
        f"{source_stem}_test",
        f"test_{source_stem}",
        f"{source_stem}.test",
        f"{source_stem}.spec",
    }


def existing_pairs(root: Path, rel: str, test_index: list[str]) -> list[str]:
    source_stem = Path(rel).stem
    hits: set[str] = set()
    for candidate in colocated_candidates(rel):
        if (root / candidate).is_file():
            hits.add(candidate)
    for test_rel in test_index:
        if stem_matches(test_rel, source_stem) and (root / test_rel).is_file():
            hits.add(test_rel)
    return sorted(hits)


def collect_state(root: Path) -> dict:
    notes: list[str] = []
    runner = discover_runner(root)
    if runner is None:
        notes.append("no-runner")

    changed = changed_paths(root)
    test_index = index_test_files(root)

    changed_tests = sorted(p for p in changed if is_test_path(p))
    changed_source = sorted(p for p in changed if is_source_path(p))

    unpaired: list[str] = []
    paired_unchanged: list[str] = []
    for src in changed_source:
        if not (root / src).is_file():
            continue
        pairs = existing_pairs(root, src, test_index)
        if not pairs:
            unpaired.append(src)
            continue
        pair_set = set(pairs)
        if not pair_set.intersection(changed):
            paired_unchanged.append(src)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "runner": runner,
        "changedSource": changed_source,
        "changedTests": changed_tests,
        "unpaired": unpaired,
        "pairedUnchanged": paired_unchanged,
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Named testing state, as JSON.")
    parser.add_argument("--project", default=".", help="Repository root (default: cwd)")
    parser.add_argument(
        "--json", action="store_true", default=True,
        help="JSON on stdout (always; flag kept for skill symmetry)",
    )
    args = parser.parse_args()

    root = Path(args.project).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1
    if not is_git_repo(root):
        print(f"not a git repository: {root}", file=sys.stderr)
        return 1

    print(json.dumps(collect_state(root), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
