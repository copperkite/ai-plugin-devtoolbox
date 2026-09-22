#!/usr/bin/env python3
"""Named git state and mechanical audit, as JSON.

Workflows and audits consume this output. They do not re-parse raw git commands.
Stdlib only. Deterministic. Safe to run in a repository of any language.

schemaVersion is bumped only when an existing field changes meaning. New fields
are additive.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
STALE_BRANCH_DAYS = 90

BRANCH_TYPES = (
    "feat", "fix", "docs", "refactor", "perf", "test", "chore",
    "build", "ci", "hotfix", "release",
)
COMMIT_TYPES = BRANCH_TYPES + ("revert",)

# release/<name> is a valid branch; default-branch names are not findings.
BRANCH_NAME_RE = re.compile(
    r"^(?:" + "|".join(BRANCH_TYPES) + r")/[a-z0-9]+(?:-[a-z0-9]+)*$"
)
COMMIT_SUBJECT_RE = re.compile(
    r"^(?:" + "|".join(COMMIT_TYPES) + r")(\([^)]+\))?(!)?: .+"
)
SECRET_PATH_RE = re.compile(
    r"(?:^|/)\.env(?:$|\.)|\.pem$|\.p12$|(?:^|/)id_rsa$"
)
PROTECTED_BRANCHES = {"main", "master", "develop"}


def git(root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=check,
    )


def git_out(root: Path, args: list[str], check: bool = True) -> str:
    result = git(root, args, check=check)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def is_git_repo(root: Path) -> bool:
    result = git(root, ["rev-parse", "--is-inside-work-tree"], check=False)
    return result.returncode == 0 and result.stdout.strip() == "true"


def current_branch(root: Path) -> str | None:
    name = git_out(root, ["branch", "--show-current"], check=False)
    return name or None


def is_detached(root: Path) -> bool:
    result = git(root, ["symbolic-ref", "-q", "HEAD"], check=False)
    return result.returncode != 0


def rebase_in_progress(root: Path) -> bool:
    git_dir = Path(git_out(root, ["rev-parse", "--git-dir"]))
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    return (git_dir / "rebase-merge").is_dir() or (git_dir / "rebase-apply").is_dir()


def has_commits(root: Path) -> bool:
    result = git(root, ["rev-parse", "-q", "--verify", "HEAD"], check=False)
    return result.returncode == 0


def default_branch(root: Path) -> str | None:
    origin_head = git_out(
        root, ["symbolic-ref", "refs/remotes/origin/HEAD", "--short"], check=False,
    )
    if origin_head.startswith("origin/"):
        return origin_head[len("origin/"):]
    for name in ("main", "master"):
        if git_out(root, ["rev-parse", "--verify", f"refs/heads/{name}"], check=False):
            return name
    return current_branch(root)


def local_branches(root: Path) -> list[str]:
    raw = git_out(root, ["for-each-ref", "--format=%(refname:short)", "refs/heads"])
    return [line for line in raw.splitlines() if line]


def infer_base(root: Path, branch: str | None, default: str | None) -> str | None:
    """Base this branch will merge into. Never assumes main when a release is the parent."""
    if not branch or not has_commits(root):
        return default
    if branch.startswith("release/"):
        return default
    releases = [b for b in local_branches(root) if b.startswith("release/")]
    ancestors = []
    for release in releases:
        result = git(root, ["merge-base", "--is-ancestor", release, "HEAD"], check=False)
        if result.returncode == 0 and release != branch:
            ancestors.append(release)
    if ancestors:
        # Newest tip among ancestor release branches.
        dated = []
        for name in ancestors:
            stamp = git_out(root, ["log", "-1", "--format=%ct", name], check=False)
            dated.append((int(stamp or "0"), name))
        dated.sort(reverse=True)
        return dated[0][1]
    return default


def porcelain_files(root: Path) -> list[str]:
    raw = git_out(root, ["status", "--porcelain=v1"], check=False)
    return [line[3:] for line in raw.splitlines() if len(line) > 3]


def ahead_behind(root: Path, other: str) -> tuple[int, int]:
    """(ahead of other, behind other). 0,0 when other is missing or no commits."""
    if not other or not has_commits(root):
        return 0, 0
    if not git_out(root, ["rev-parse", "--verify", other], check=False):
        # Try origin/other for a remote default.
        remote = f"origin/{other}" if not other.startswith("origin/") else other
        if not git_out(root, ["rev-parse", "--verify", remote], check=False):
            return 0, 0
        other = remote
    raw = git_out(root, ["rev-list", "--left-right", "--count", f"HEAD...{other}"], check=False)
    if not raw:
        return 0, 0
    parts = raw.split()
    if len(parts) != 2:
        return 0, 0
    return int(parts[0]), int(parts[1])


def upstream(root: Path) -> str | None:
    name = git_out(root, ["rev-parse", "--abbrev-ref", "@{upstream}"], check=False)
    return name or None


def read_pr(root: Path) -> tuple[dict | None, list[str]]:
    notes: list[str] = []
    result = subprocess.run(
        ["gh", "pr", "view",
         "--json", "number,state,isDraft,mergeable,statusCheckRollup,reviewDecision,baseRefName"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        notes.append("gh-unavailable")
        return None, notes
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        notes.append("gh-unavailable")
        return None, notes
    return {
        "number": data.get("number"),
        "state": data.get("state"),
        "isDraft": data.get("isDraft"),
        "mergeable": data.get("mergeable"),
        "reviewDecision": data.get("reviewDecision"),
        "baseRefName": data.get("baseRefName"),
    }, notes


def name_state(
    dirty_count: int,
    unpushed: int,
    has_upstream: bool,
    pr: dict | None,
) -> str:
    """Primary named state. Dirty wins: uncommitted work blocks every later step."""
    if dirty_count:
        return "dirty"
    if pr:
        state = (pr.get("state") or "").upper()
        if state == "MERGED":
            return "merged"
        if pr.get("isDraft"):
            return "draft-pr"
        return "ready-pr"
    if unpushed:
        return "committed"
    if has_upstream:
        return "pushed"
    return "clean"


def collect_state(root: Path) -> dict:
    notes: list[str] = []
    branch = current_branch(root)
    default = default_branch(root)
    detached = is_detached(root)
    files = porcelain_files(root)
    tracking = upstream(root)
    ahead_up, behind_up = ahead_behind(root, tracking) if tracking else (0, 0)
    unpushed = ahead_up if tracking else (1 if has_commits(root) and not tracking else 0)
    # No upstream + commits: treat every local commit as unpushed for naming.
    if not tracking and has_commits(root):
        unpushed = int(git_out(root, ["rev-list", "--count", "HEAD"], check=False) or "0")

    pr, pr_notes = read_pr(root)
    notes.extend(pr_notes)
    base = None
    if pr and pr.get("baseRefName"):
        base = pr["baseRefName"]
    else:
        base = infer_base(root, branch, default)

    _, behind_base = ahead_behind(root, base) if base else (0, 0)

    named = name_state(len(files), unpushed, bool(tracking), pr)
    # Empty repo, no files: clean, not committed.
    if not has_commits(root) and not files:
        named = "clean"
        unpushed = 0
    elif not has_commits(root) and files:
        named = "dirty"
        unpushed = 0

    flags: list[str] = []
    if behind_base:
        flags.append("behind-base")
    if branch and default and branch == default:
        flags.append("on-default-branch")
    if detached:
        flags.append("detached")
    if rebase_in_progress(root):
        flags.append("rebase-in-progress")

    return {
        "schemaVersion": SCHEMA_VERSION,
        "mode": "state",
        "branch": branch,
        "defaultBranch": default,
        "base": base,
        "named": named,
        "flags": flags,
        "counts": {
            "dirtyFiles": len(files),
            "unpushed": unpushed,
            "unpulled": behind_up,
            "behindBase": behind_base,
        },
        "pr": pr,
        "notes": notes,
    }


def branch_age_days(root: Path, name: str, today: date) -> int | None:
    raw = git_out(root, ["log", "-1", "--format=%cI", name], check=False)
    if not raw:
        return None
    try:
        committed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (today - committed.date()).days


def collect_audit(root: Path, today: date | None = None) -> dict:
    if today is None:
        today = datetime.now(timezone.utc).date()
    default = default_branch(root)
    branch = current_branch(root)
    findings: list[dict] = []

    files = porcelain_files(root)
    if files and branch and branch in PROTECTED_BRANCHES:
        findings.append({
            "severity": "blocking",
            "kind": "on-default-dirty",
            "detail": f"{len(files)} uncommitted path(s) on {branch}",
        })

    tracking = upstream(root)
    if tracking:
        ahead, _ = ahead_behind(root, tracking)
        if ahead:
            findings.append({
                "severity": "cleanup",
                "kind": "unpushed",
                "detail": f"{ahead} local commit(s) not on {tracking}",
            })
    elif has_commits(root) and branch and branch not in PROTECTED_BRANCHES:
        findings.append({
            "severity": "cleanup",
            "kind": "unpushed",
            "detail": f"{branch} has no upstream",
        })

    tracked = git_out(root, ["ls-files"], check=False).splitlines()
    for path in tracked:
        if SECRET_PATH_RE.search(path):
            findings.append({
                "severity": "blocking",
                "kind": "tracked-secret-path",
                "detail": path,
            })

    if default and has_commits(root):
        merged = git_out(root, ["branch", "--merged", default, "--format=%(refname:short)"])
        for name in merged.splitlines():
            if not name or name == default or name in PROTECTED_BRANCHES:
                continue
            findings.append({
                "severity": "cleanup",
                "kind": "merged-undeleted",
                "detail": name,
            })

    for name in local_branches(root):
        if name in PROTECTED_BRANCHES or name == default:
            continue
        if not BRANCH_NAME_RE.match(name):
            findings.append({
                "severity": "convention",
                "kind": "off-convention-branch",
                "detail": name,
            })
        age = branch_age_days(root, name, today)
        if age is not None and age >= STALE_BRANCH_DAYS:
            merged_into_default = False
            if default:
                result = git(
                    root, ["merge-base", "--is-ancestor", name, default], check=False,
                )
                merged_into_default = result.returncode == 0
            if not merged_into_default:
                findings.append({
                    "severity": "cleanup",
                    "kind": "stale-branch",
                    "detail": f"{name} last commit {age} day(s) ago",
                })

    if default and has_commits(root) and branch:
        ahead, behind = ahead_behind(root, infer_base(root, branch, default) or default)
        if behind and ahead:
            findings.append({
                "severity": "cleanup",
                "kind": "adrift-from-base",
                "detail": f"{ahead} ahead / {behind} behind base",
            })

    if has_commits(root):
        log = git_out(root, ["log", "--format=%s", "-30"], check=False)
        off = [s for s in log.splitlines() if s and not COMMIT_SUBJECT_RE.match(s)]
        if off:
            findings.append({
                "severity": "convention",
                "kind": "off-convention-subject",
                "detail": f"{len(off)} of the last {min(30, len(log.splitlines()))} subjects",
            })

    return {
        "schemaVersion": SCHEMA_VERSION,
        "mode": "audit",
        "branch": branch,
        "defaultBranch": default,
        "findings": findings,
        "notes": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Named git state and mechanical audit, as JSON.")
    parser.add_argument("--project", default=".", help="Repository root (default: cwd)")
    parser.add_argument(
        "--mode", choices=("state", "audit"), default="state",
        help="state: named workflow state; audit: mechanical findings",
    )
    parser.add_argument("--json", action="store_true", default=True,
                        help="JSON on stdout (always; flag kept for skill symmetry)")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1
    if not is_git_repo(root):
        print(f"not a git repository: {root}", file=sys.stderr)
        return 1

    payload = collect_state(root) if args.mode == "state" else collect_audit(root)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
