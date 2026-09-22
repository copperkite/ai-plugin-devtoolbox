#!/usr/bin/env python3
"""Tests for git_state.py — temp repositories, no network."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "skills" / "git-intent" / "scripts" / "git_state.py"


def load_git_state():
    spec = importlib.util.spec_from_file_location("git_state", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


git_state = load_git_state()


def git(root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    env_cmd = ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test"]
    return subprocess.run(
        [*env_cmd, *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=check,
    )


def init_repo(tmp: Path, branch: str = "main") -> Path:
    root = tmp / "repo"
    root.mkdir()
    git(root, ["init", "-b", branch])
    git(root, ["config", "user.email", "test@example.com"])
    git(root, ["config", "user.name", "Test"])
    return root


def commit(root: Path, rel: str, content: str, message: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    git(root, ["add", rel])
    git(root, ["commit", "-m", message])


class GitStateTests(unittest.TestCase):
    def test_not_a_repo_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(SCRIPT), "--project", tmp, "--mode", "state", "--json"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("not a git repository", result.stderr)

    def test_named_committed_on_clean_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "a.txt", "a\n", "feat: add a")
            payload = git_state.collect_state(root)
            self.assertEqual(payload["named"], "committed")
            self.assertEqual(payload["counts"]["dirtyFiles"], 0)
            self.assertGreater(payload["counts"]["unpushed"], 0)
            self.assertIn("on-default-branch", payload["flags"])

    def test_named_dirty_when_uncommitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "a.txt", "a\n", "feat: add a")
            (root / "b.txt").write_text("b\n", encoding="utf-8")
            payload = git_state.collect_state(root)
            self.assertEqual(payload["named"], "dirty")
            self.assertEqual(payload["counts"]["dirtyFiles"], 1)

    def test_on_default_branch_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "a.txt", "a\n", "feat: add a")
            git(root, ["checkout", "-b", "feat/thing"])
            payload = git_state.collect_state(root)
            self.assertEqual(payload["branch"], "feat/thing")
            self.assertNotIn("on-default-branch", payload["flags"])
            self.assertEqual(payload["defaultBranch"], "main")

    def test_audit_off_convention_subject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "a.txt", "a\n", "wip stuff")
            payload = git_state.collect_audit(root)
            kinds = [f["kind"] for f in payload["findings"]]
            self.assertIn("off-convention-subject", kinds)

    def test_audit_skips_conventional_subject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "a.txt", "a\n", "feat: add a")
            git(root, ["checkout", "-b", "feat/thing"])
            payload = git_state.collect_audit(root)
            kinds = [f["kind"] for f in payload["findings"]]
            self.assertNotIn("off-convention-subject", kinds)

    def test_cli_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "a.txt", "a\n", "feat: add a")
            result = subprocess.run(
                ["python3", str(SCRIPT), "--project", str(root), "--mode", "state", "--json"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schemaVersion"], 1)
            self.assertEqual(payload["mode"], "state")
            self.assertEqual(payload["named"], "committed")


if __name__ == "__main__":
    unittest.main()
