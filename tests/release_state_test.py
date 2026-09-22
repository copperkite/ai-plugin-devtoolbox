#!/usr/bin/env python3
"""Tests for release_state.py — temp repositories, no network."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "skills" / "release-intent" / "scripts" / "release_state.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("release_state", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


release_state = load_mod()


def git(root: Path, args: list[str]) -> None:
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", *args],
        cwd=root, check=True, capture_output=True, text=True,
    )


def init_repo(tmp: Path) -> Path:
    root = tmp / "repo"
    root.mkdir()
    git(root, ["init", "-b", "main"])
    git(root, ["config", "user.email", "test@example.com"])
    git(root, ["config", "user.name", "Test"])
    return root


def commit(root: Path, rel: str, content: str, message: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    git(root, ["add", rel])
    git(root, ["commit", "-m", message])


class ReleaseStateTests(unittest.TestCase):
    def test_commits_since_last_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "a.txt", "a\n", "feat: one")
            git(root, ["tag", "-a", "v0.1.0", "-m", "v0.1.0"])
            commit(root, "b.txt", "b\n", "feat: two")
            payload = release_state.collect_release(root)
            self.assertEqual(payload["lastTag"], "v0.1.0")
            self.assertEqual([c["subject"] for c in payload["commitsSinceTag"]], ["feat: two"])
            self.assertFalse(payload["dirty"])

    def test_unreleased_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n", "docs: changelog")
            payload = release_state.collect_release(root)
            self.assertTrue(payload["unreleased"]["present"])
            self.assertTrue(payload["unreleased"]["empty"])

    def test_version_of_record_from_conventions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            (root / "src").mkdir()
            (root / "src" / "plugin.json").write_text(
                '{"name": "x", "version": "0.1.0"}\n', encoding="utf-8")
            (root / ".agent-adoptions.json").write_text(
                json.dumps({"ai-plugin-dev": {"adopted": {"release": {
                    "scheme": "semver", "version-file": "src/plugin.json"}}}}),
                encoding="utf-8")
            commit(root, "src/plugin.json", '{"name": "x", "version": "0.1.0"}\n', "feat: plugin")
            git(root, ["add", ".agent-adoptions.json"])
            git(root, ["commit", "-m", "chore: conventions"])
            payload = release_state.collect_release(root)
            self.assertEqual(payload["versionOfRecord"]["version"], "0.1.0")
            self.assertEqual(payload["versionOfRecord"]["file"], "src/plugin.json")


if __name__ == "__main__":
    unittest.main()
