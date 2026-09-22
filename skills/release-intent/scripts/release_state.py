#!/usr/bin/env python3
"""Release snapshot as JSON: last tag, commits since, changelog, version of record.

Does not choose the next version — that judgement stays in release-intent.
Stdlib only. schemaVersion is bumped only when an existing field changes meaning.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCHEMA_VERSION = 1
UNRELEASED_RE = re.compile(r"^## \[Unreleased\]\s*$", re.M | re.I)
VERSION_JSON_RE = re.compile(r'"version"\s*:\s*"([^"]+)"')
VERSION_TOML_RE = re.compile(r'(?m)^version\s*=\s*"([^"]+)"')


def git(root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=check,
    )


def git_out(root: Path, args: list[str]) -> str:
    result = git(root, args, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


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


def is_dirty(root: Path) -> bool:
    return bool(git_out(root, ["status", "--porcelain"]))


def recent_tags(root: Path, limit: int = 5) -> list[str]:
    raw = git_out(root, ["tag", "--list", "--sort=-v:refname"])
    tags = [t for t in raw.splitlines() if t]
    return tags[:limit]


def last_tag(root: Path) -> str | None:
    name = git_out(root, ["describe", "--tags", "--abbrev=0"])
    return name or None


def commits_since(root: Path, tag: str | None) -> list[dict]:
    rng = f"{tag}..HEAD" if tag else "HEAD"
    raw = git_out(root, ["log", "--format=%H%x09%s", rng])
    out = []
    for line in raw.splitlines():
        if "\t" not in line:
            continue
        sha, subject = line.split("\t", 1)
        out.append({"sha": sha, "subject": subject})
    return out


def unreleased_section(root: Path) -> dict:
    path = root / "CHANGELOG.md"
    if not path.is_file():
        return {"present": False, "empty": True, "headings": [], "entryCount": 0}
    text = path.read_text(encoding="utf-8")
    if not UNRELEASED_RE.search(text):
        return {"present": False, "empty": True, "headings": [], "entryCount": 0}
    # Slice from Unreleased until the next ## [version] heading.
    parts = re.split(r"(?m)^## \[", text)
    body = ""
    for part in parts[1:]:
        if part.lower().startswith("unreleased]"):
            body = part.split("]", 1)[-1]
            break
    headings = re.findall(r"(?m)^###\s+(.+?)\s*$", body)
    bullets = re.findall(r"(?m)^[-*]\s+\S", body)
    return {
        "present": True,
        "empty": not bullets,
        "headings": headings,
        "entryCount": len(bullets),
    }


def read_conventions(root: Path) -> dict:
    path = root / ".agent-adoptions.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    slice_ = data.get("ai-plugin-dev")
    return slice_ if isinstance(slice_, dict) else {}


def parse_version(text: str, suffix: str) -> str | None:
    if suffix in (".json",):
        m = VERSION_JSON_RE.search(text)
        return m.group(1) if m else None
    if suffix in (".toml",):
        m = VERSION_TOML_RE.search(text)
        return m.group(1) if m else None
    line = text.strip().splitlines()
    return line[0].strip() if line else None


def version_of_record(root: Path) -> dict | None:
    adopted = read_conventions(root).get("adopted") or {}
    release = adopted.get("release")
    if not isinstance(release, dict):
        return None
    rel = release.get("version-file")
    if not isinstance(rel, str) or not rel:
        return None
    path = root / rel
    if not path.is_file():
        return {"file": rel, "version": None, "missing": True}
    version = parse_version(path.read_text(encoding="utf-8"), path.suffix)
    return {"file": rel, "version": version, "missing": False}


def collect_release(root: Path) -> dict:
    tag = last_tag(root)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "mode": "release",
        "branch": current_branch(root),
        "defaultBranch": default_branch(root),
        "dirty": is_dirty(root),
        "lastTag": tag,
        "recentTags": recent_tags(root),
        "commitsSinceTag": commits_since(root, tag),
        "unreleased": unreleased_section(root),
        "versionOfRecord": version_of_record(root),
        "notes": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Release snapshot as JSON. Does not choose the next version.")
    parser.add_argument("--project", default=".", help="Repository root (default: cwd)")
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args()

    root = Path(args.project).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1
    if not is_git_repo(root):
        print(f"not a git repository: {root}", file=sys.stderr)
        return 1

    print(json.dumps(collect_release(root), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
