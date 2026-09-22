#!/usr/bin/env python3
"""Tests for testing_state.py — temp repositories, no network."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "skills" / "testing-intent" / "scripts" / "testing_state.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("testing_state", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


testing_state = load_mod()


def git(root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", *args],
        cwd=root, capture_output=True, text=True, check=check,
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


def write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestingStateTests(unittest.TestCase):
    def test_not_a_repo_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(SCRIPT), "--project", tmp, "--json"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("not a git repository", result.stderr)

    def test_makefile_test_target_is_the_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "Makefile", "test:\n\tpython3 -m unittest\n", "chore: makefile")
            payload = testing_state.collect_state(root)
            self.assertEqual(payload["runner"]["command"], ["make", "test"])
            self.assertEqual(payload["runner"]["source"], "makefile")

    def test_package_json_prefers_pnpm_when_lockfile_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(
                root, "package.json",
                json.dumps({"scripts": {"test": "vitest run"}}),
                "chore: package",
            )
            write(root, "pnpm-lock.yaml", "lockfileVersion: '9.0'\n")
            git(root, ["add", "pnpm-lock.yaml"])
            git(root, ["commit", "-m", "chore: lockfile"])
            payload = testing_state.collect_state(root)
            self.assertEqual(payload["runner"]["command"], ["pnpm", "test"])
            self.assertEqual(payload["runner"]["source"], "package.json")

    def test_unpaired_when_source_has_no_test_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "src/keep.py", "x = 1\n", "feat: keep")
            write(root, "src/parse.py", "def parse():\n    return 1\n")
            payload = testing_state.collect_state(root)
            self.assertIn("src/parse.py", payload["unpaired"])
            self.assertIn("src/parse.py", payload["changedSource"])

    def test_colocated_test_is_not_unpaired(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "src/parse.py", "def parse():\n    return 1\n", "feat: parse")
            write(root, "src/parse.py", "def parse():\n    return 2\n")
            write(root, "src/parse_test.py", "def test_parse():\n    assert True\n")
            payload = testing_state.collect_state(root)
            self.assertNotIn("src/parse.py", payload["unpaired"])
            self.assertIn("src/parse.py", payload["changedSource"])
            self.assertIn("src/parse_test.py", payload["changedTests"])

    def test_tests_dir_pairing_by_stem(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(
                root, "src/skills/foo/scripts/testing_state.py",
                "SCHEMA = 1\n",
                "feat: script",
            )
            commit(
                root, "tests/testing_state_test.py",
                "import unittest\n",
                "test: script",
            )
            write(root, "src/skills/foo/scripts/testing_state.py", "SCHEMA = 2\n")
            payload = testing_state.collect_state(root)
            self.assertNotIn(
                "src/skills/foo/scripts/testing_state.py", payload["unpaired"],
            )
            self.assertIn(
                "src/skills/foo/scripts/testing_state.py",
                payload["pairedUnchanged"],
            )

    def test_no_runner_notes_when_nothing_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "README.md", "hi\n", "docs: readme")
            payload = testing_state.collect_state(root)
            self.assertIsNone(payload["runner"])
            self.assertIn("no-runner", payload["notes"])

    def test_makefile_wins_over_package_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = init_repo(Path(tmp))
            commit(root, "Makefile", "test:\n\techo ok\n", "chore: makefile")
            commit(
                root, "package.json",
                json.dumps({"scripts": {"test": "vitest"}}),
                "chore: package",
            )
            payload = testing_state.collect_state(root)
            self.assertEqual(payload["runner"]["source"], "makefile")
