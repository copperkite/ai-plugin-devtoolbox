#!/usr/bin/env python3
"""Tests for the extra docs_index checks — temp trees, no network."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "skills" / "documentation-intent" / "scripts" / "docs_index.py"


def load_docs_index():
    spec = importlib.util.spec_from_file_location("docs_index", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


docs_index = load_docs_index()
TODAY = date(2026, 8, 17)


def git(root: Path, args: list[str]) -> None:
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", *args],
        cwd=root, check=True, capture_output=True, text=True,
    )


def init_git(root: Path) -> None:
    git(root, ["init", "-b", "main"])
    git(root, ["config", "user.email", "test@example.com"])
    git(root, ["config", "user.name", "Test"])


class DocsIndexExtraTests(unittest.TestCase):
    def test_missing_unreleased_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "architecture").mkdir(parents=True)
            (root / "docs" / "architecture" / "OVERVIEW.md").write_text(
                "---\ntitle: Overview\nsummary: Map.\nstatus: draft\n"
                "last_verified: 2026-08-01\ncovers: []\n---\n\n# Overview\n",
                encoding="utf-8",
            )
            (root / "docs" / "INDEX.md").write_text(
                docs_index.render_index(docs_index.collect_docs(root)), encoding="utf-8")
            (root / "CHANGELOG.md").write_text("# Changelog\n\n## [0.1.0]\n", encoding="utf-8")
            result = docs_index.run_check(root, TODAY)
            kinds = [w["check"] for w in result["warnings"]]
            self.assertIn("changelog", kinds)

    def test_project_marker_in_body_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "architecture").mkdir(parents=True)
            (root / "docs" / "architecture" / "OVERVIEW.md").write_text(
                "---\ntitle: Overview\nsummary: Map.\nstatus: draft\n"
                "last_verified: 2026-08-01\ncovers: []\n---\n\n"
                "# Overview\n\n<!-- PROJECT: goal -->\n",
                encoding="utf-8",
            )
            (root / "docs" / "INDEX.md").write_text(
                docs_index.render_index(docs_index.collect_docs(root)), encoding="utf-8")
            result = docs_index.run_check(root, TODAY)
            msgs = [w for w in result["warnings"] if w["check"] == "placeholder"]
            self.assertTrue(any("PROJECT marker" in w["message"] for w in msgs))

    def test_single_file_presumed_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git(root)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print(1)\n", encoding="utf-8")
            git(root, ["add", "src/main.py"])
            git(root, ["commit", "-m", "feat: code"])
            (root / "DOCUMENTATION.md").write_text(
                "---\ntitle: Docs\nsummary: All of it.\nstatus: verified\n"
                "last_verified: 2020-01-01\ncovers:\n  - \"src/**\"\n---\n\n"
                "# Purpose\n\n# Architecture\n\n# Development\n\n# Decisions\n",
                encoding="utf-8",
            )
            git(root, ["add", "DOCUMENTATION.md"])
            git(root, ["commit", "-m", "docs: add"])
            (root / "src" / "main.py").write_text("print(2)\n", encoding="utf-8")
            git(root, ["add", "src/main.py"])
            git(root, ["commit", "-m", "feat: change code"])
            result = docs_index.run_check(root, TODAY)
            self.assertTrue(result["presumed_stale"])
            self.assertEqual(result["presumed_stale"][0]["file"], "DOCUMENTATION.md")
            self.assertFalse(any(e["check"] == "index" for e in result["errors"]))


    def test_flat_index_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "ARCHITECTURE.md").write_text(
                "---\ntitle: Architecture\nsummary: How it is built.\nstatus: draft\n"
                "last_verified: 2026-08-01\ncovers: []\n---\n\n# Architecture\n",
                encoding="utf-8",
            )
            (docs / "DECISIONS.md").write_text(
                "---\ntitle: Decisions\nsummary: Settled choices.\nstatus: draft\n"
                "last_verified: 2026-08-01\ncovers: []\n---\n\n# Decisions\n",
                encoding="utf-8",
            )
            (docs / "DEVELOPMENT.md").write_text(
                "---\ntitle: Development\nsummary: How to run it.\nstatus: draft\n"
                "last_verified: 2026-08-01\ncovers: []\n---\n\n# Development\n",
                encoding="utf-8",
            )
            collected = docs_index.collect_docs(root)
            by_name = {d.path.name: d.category for d in collected}
            self.assertEqual(by_name["ARCHITECTURE.md"], "architecture")
            self.assertEqual(by_name["DECISIONS.md"], "decisions")
            self.assertEqual(by_name["DEVELOPMENT.md"], "operations")
            self.assertEqual(docs_index.detect_shape(root), "flat")
            index = docs_index.render_index(collected)
            self.assertIn("Architecture — how it is built", index)
            self.assertIn("[ARCHITECTURE.md](./ARCHITECTURE.md)", index)
            (docs / "INDEX.md").write_text(index, encoding="utf-8")
            result = docs_index.run_check(root, TODAY)
            self.assertFalse(any(e["check"] == "index" for e in result["errors"]))

    def test_flat_subdir_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            (docs / "extra").mkdir(parents=True)
            (docs / "ARCHITECTURE.md").write_text(
                "---\ntitle: Architecture\nsummary: Map.\nstatus: draft\n"
                "last_verified: 2026-08-01\ncovers: []\n---\n\n# Architecture\n",
                encoding="utf-8",
            )
            (docs / "INDEX.md").write_text(
                docs_index.render_index(docs_index.collect_docs(root)), encoding="utf-8")
            result = docs_index.run_check(root, TODAY)
            shape_warns = [w for w in result["warnings"] if w["check"] == "shape"]
            self.assertTrue(any("docs/extra/" in w["file"] for w in shape_warns))

    def test_write_refuses_foreign_index_unless_forced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "ARCHITECTURE.md").write_text(
                "---\ntitle: Architecture\nsummary: Map.\nstatus: draft\n"
                "last_verified: 2026-08-01\ncovers: []\n---\n\n# Architecture\n",
                encoding="utf-8",
            )
            (docs / "INDEX.md").write_text("# Their own index\n", encoding="utf-8")
            refused = subprocess.run(
                ["python3", str(SCRIPT), "--project", str(root), "--write", "--json"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(refused.returncode, 1)
            self.assertIn('"refused"', refused.stdout)
            self.assertEqual((docs / "INDEX.md").read_text(encoding="utf-8"), "# Their own index\n")
            forced = subprocess.run(
                ["python3", str(SCRIPT), "--project", str(root), "--write", "--force"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(forced.returncode, 0)
            self.assertTrue(docs_index.index_is_generated(docs / "INDEX.md"))
            again = subprocess.run(
                ["python3", str(SCRIPT), "--project", str(root), "--write"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(again.returncode, 0)


if __name__ == "__main__":
    unittest.main()
