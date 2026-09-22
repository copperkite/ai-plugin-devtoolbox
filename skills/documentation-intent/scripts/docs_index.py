#!/usr/bin/env python3
"""Documentation index generator and drift checker.

Reads the frontmatter of every document under ``docs/``, regenerates
``docs/INDEX.md``, and reports documentation that has fallen behind the code it
claims to describe.

The drift signal: each document declares ``covers`` (globs of the code it
describes) and ``last_verified`` (when that claim was checked). When git shows a
commit on the covered code newer than that date, the document is presumed stale
— no human review required.

Stdlib only. Deterministic. Safe to run in a repository of any language.
"""

from __future__ import annotations

import argparse
import glob as globmod
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

CATEGORIES = [
    ("context", "Context — why and what"),
    ("architecture", "Architecture — how it is built"),
    ("decisions", "Decisions — what was already settled"),
    ("operations", "Operations — how to work here"),
]

# Flat shape: files live directly under docs/; map each name to an index category.
FLAT_CATEGORY = {
    "PRODUCT.md": "context",
    "ARCHITECTURE.md": "architecture",
    "DATA-MODEL.md": "architecture",
    "THREAT-MODEL.md": "architecture",
    "DECISIONS.md": "decisions",
    "DEVELOPMENT.md": "operations",
    "TESTING.md": "operations",
    "RUNBOOKS.md": "operations",
    "TROUBLESHOOTING.md": "operations",
}

TREE_DIR_NAMES = frozenset({"context", "architecture", "decisions", "operations"})

REQUIRED_FIELDS = ("title", "summary", "status", "last_verified", "covers")
VALID_STATUS = {"draft", "verified", "stale"}
VALID_ADR_STATUS = {"proposed", "accepted", "rejected", "superseded", "deprecated"}

FRESHNESS_BUDGET_DAYS = 180
FRESHNESS_BUDGET_DAYS_NO_COVERS = 365

# Directories that are never project source.
IGNORED_TOP_LEVEL = {
    ".git", ".github", ".nola", ".agents", ".cursor", ".claude", ".vscode", ".idea",
    "docs", "node_modules", "vendor", "dist", "build", "target", "out", "coverage",
    ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".next", ".turbo",
}

PLACEHOLDER_RE = re.compile(r"<!--.*?-->", re.S)
PROJECT_MARKER_RE = re.compile(r"<!--\s*PROJECT:")
UNRELEASED_RE = re.compile(r"^## \[Unreleased\]\s*$", re.M | re.I)
ALTERNATIVES_RE = re.compile(r"^#{2,}\s+Alternatives considered\s*$", re.M | re.I)


# --------------------------------------------------------------------------- #
# Frontmatter parsing (YAML subset: scalars, block lists, inline lists, null)
# --------------------------------------------------------------------------- #

def _scalar(raw: str):
    v = raw.strip()
    if v in ("null", "~", ""):
        return None
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part) for part in inner.split(",")]
    return v


def parse_frontmatter(text: str) -> dict | None:
    """Parse leading YAML frontmatter. Returns None when absent or unterminated."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None

    data: dict = {}
    key: str | None = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.lstrip().startswith("- ") and key is not None:
            data.setdefault(key, [])
            if isinstance(data[key], list):
                data[key].append(_scalar(raw.lstrip()[2:]))
            continue
        m = re.match(r"^([A-Za-z_][\w.-]*)\s*:\s*(.*)$", raw)
        if not m:
            continue
        key, rest = m.group(1), m.group(2)
        data[key] = [] if rest.strip() == "" else _scalar(rest)
    return data


def is_placeholder(value) -> bool:
    """True when a field still holds an unfilled `<!-- PROJECT: ... -->` marker."""
    if isinstance(value, str):
        return bool(PLACEHOLDER_RE.search(value))
    if isinstance(value, list):
        return any(is_placeholder(v) for v in value)
    return False


# --------------------------------------------------------------------------- #
# Repository model
# --------------------------------------------------------------------------- #

class Doc:
    def __init__(self, path: Path, root: Path):
        self.path = path
        self.rel = path.relative_to(root).as_posix()
        docs_dir = root / "docs"
        try:
            self.docs_rel = path.relative_to(docs_dir).as_posix()
            if "/" in self.docs_rel:
                self.category = self.docs_rel.split("/")[0]
            else:
                self.category = FLAT_CATEGORY.get(path.name, "")
        except ValueError:
            self.docs_rel = ""
            self.category = ""
        self.text = path.read_text(encoding="utf-8")
        self.fm = parse_frontmatter(self.text) or {}
        self.has_fm = parse_frontmatter(self.text) is not None
        self.is_adr = bool(re.match(r"^ADR-\d{4}-", path.name))

    @property
    def covers(self) -> list[str]:
        raw = self.fm.get("covers") or []
        if isinstance(raw, str):
            raw = [raw]
        return [c for c in raw if isinstance(c, str) and not is_placeholder(c)]

    @property
    def last_verified(self) -> date | None:
        raw = self.fm.get("last_verified")
        if not isinstance(raw, str) or is_placeholder(raw):
            return None
        try:
            return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None


def collect_docs(root: Path) -> list[Doc]:
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return []
    out = []
    for p in sorted(docs_dir.rglob("*.md")):
        if p.name == "INDEX.md" or "node_modules" in p.parts:
            continue
        out.append(Doc(p, root))
    return out


# --------------------------------------------------------------------------- #
# Git
# --------------------------------------------------------------------------- #

def git_last_commit_date(root: Path, pathspecs: list[str]) -> date | None:
    """Newest commit date touching any pathspec. None when git or history absent."""
    if not pathspecs:
        return None
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", *pathspecs],
            cwd=root, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if res.returncode != 0 or not res.stdout.strip():
        return None
    try:
        return datetime.fromisoformat(res.stdout.strip()).date()
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

class Report:
    def __init__(self):
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def error(self, check: str, file: str, message: str, **extra):
        self.errors.append({"check": check, "file": file, "message": message, **extra})

    def warn(self, check: str, file: str, message: str, **extra):
        self.warnings.append({"check": check, "file": file, "message": message, **extra})


def expand(root: Path, pattern: str) -> list[str]:
    """Expand one glob relative to root. Returns repo-relative posix paths.

    Avoids ``glob(root_dir=...)`` so the script runs on Python 3.8+.
    """
    base = str(root)
    matches = globmod.glob(os.path.join(base, pattern), recursive=True)
    return sorted(os.path.relpath(m, base).replace(os.sep, "/") for m in matches)


def resolve_covers(root: Path, patterns: list[str]) -> tuple[list[str], list[str]]:
    """Return (matched paths, patterns that matched nothing). `!` negates."""
    positive = [p for p in patterns if not p.startswith("!")]
    negative = [p[1:] for p in patterns if p.startswith("!")]
    excluded: set[str] = set()
    for pat in negative:
        excluded.update(expand(root, pat))
    matched: set[str] = set()
    empty: list[str] = []
    for pat in positive:
        hits = [h for h in expand(root, pat) if h not in excluded]
        if not hits:
            empty.append(pat)
        matched.update(hits)
    return sorted(matched), empty


def check_frontmatter(doc: Doc, rep: Report) -> None:
    if not doc.has_fm:
        rep.error("frontmatter", doc.rel, "no YAML frontmatter")
        return

    if doc.is_adr or doc.docs_rel == "decisions/ADR-TEMPLATE.md":
        status = doc.fm.get("status")
        if status not in VALID_ADR_STATUS and not is_placeholder(status):
            rep.error("frontmatter", doc.rel, f"status {status!r} not in {sorted(VALID_ADR_STATUS)}")
        if status == "superseded" and not doc.fm.get("superseded_by"):
            rep.error("adr", doc.rel, "status is 'superseded' but superseded_by is empty")
        return

    for field in REQUIRED_FIELDS:
        if field not in doc.fm:
            rep.error("frontmatter", doc.rel, f"missing required field '{field}'")

    status = doc.fm.get("status")
    if status is not None and status not in VALID_STATUS:
        rep.error("frontmatter", doc.rel, f"status {status!r} not in {sorted(VALID_STATUS)}")

    for field in ("title", "summary", "last_verified", "covers"):
        if field in doc.fm and is_placeholder(doc.fm[field]):
            rep.warn("placeholder", doc.rel, f"'{field}' still holds an unfilled placeholder")

    if "last_verified" in doc.fm and doc.last_verified is None \
            and not is_placeholder(doc.fm.get("last_verified")):
        rep.error("frontmatter", doc.rel, "last_verified is not a valid YYYY-MM-DD date")


def check_staleness(root: Path, doc: Doc, rep: Report, today: date) -> dict:
    """The check that justifies the contract. Returns per-doc drift facts."""
    info = {"file": doc.rel, "status": doc.fm.get("status"), "presumed_stale": False}
    covers = doc.covers
    verified = doc.last_verified
    if verified is None:
        return info

    if covers:
        matched, empty = resolve_covers(root, covers)
        for pat in empty:
            rep.error("covers", doc.rel, f"glob {pat!r} matches no path")
        code_date = git_last_commit_date(root, covers)
        if code_date and code_date > verified:
            gap = (code_date - verified).days
            info["presumed_stale"] = True
            info["days_behind"] = gap
            rep.warn(
                "stale", doc.rel,
                f"covered code changed {gap} day(s) after last_verified "
                f"({verified.isoformat()} → {code_date.isoformat()})",
                days_behind=gap,
            )
        info["matched_paths"] = len(matched)

    budget = FRESHNESS_BUDGET_DAYS if covers else FRESHNESS_BUDGET_DAYS_NO_COVERS
    age = (today - verified).days
    if doc.fm.get("status") == "verified" and age > budget:
        rep.warn("freshness", doc.rel,
                 f"verified {age} day(s) ago, over the {budget}-day budget", age_days=age)
    return info


def check_coverage(root: Path, docs: list[Doc], rep: Report) -> None:
    covered_tops: set[str] = set()
    for doc in docs:
        matched, _ = resolve_covers(root, doc.covers)
        for path in matched:
            covered_tops.add(path.split("/")[0])
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in IGNORED_TOP_LEVEL or child.name.startswith("."):
            continue
        if child.name not in covered_tops:
            rep.warn("coverage", child.name + "/",
                     "top-level directory is not covered by any document's 'covers'")


LINK_RE = re.compile(r"\[[^\]]*\]\((?!https?:|mailto:|#)([^)]+)\)")


def check_links(root: Path, files: list[Path], rep: Report) -> None:
    for path in files:
        # Strip HTML comments first: links to not-yet-created optional documents
        # are deliberately parked inside comments, and a commented-out link is
        # not a broken link.
        text = PLACEHOLDER_RE.sub("", path.read_text(encoding="utf-8"))
        for m in LINK_RE.finditer(text):
            target = m.group(1).split("#")[0].strip()
            if not target or target.startswith("<"):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                rep.error("link", path.relative_to(root).as_posix(),
                          f"broken relative link → {target}")


def check_adrs(root: Path, docs: list[Doc], rep: Report) -> None:
    adr_dir = root / "docs" / "decisions"
    if not adr_dir.is_dir():
        return
    adrs = [d for d in docs if d.is_adr]
    seen: dict[str, str] = {}
    for adr in adrs:
        num = adr.path.name[4:8]
        if num in seen:
            rep.error("adr", adr.rel, f"ADR number {num} already used by {seen[num]}")
        seen[num] = adr.rel
        if not ALTERNATIVES_RE.search(adr.text):
            rep.warn("adr", adr.rel, "missing 'Alternatives considered' heading")

    index = adr_dir / "README.md"
    if not index.is_file():
        if adrs:
            rep.error("adr", "docs/decisions/README.md", "decision index is missing")
        return
    index_text = index.read_text(encoding="utf-8")
    for adr in adrs:
        if adr.path.name not in index_text:
            rep.error("adr", adr.rel, "not listed in docs/decisions/README.md")


def check_index(root: Path, docs: list[Doc], rep: Report) -> None:
    """Regenerate and compare — catches missing rows *and* stale summaries."""
    index = root / "docs" / "INDEX.md"
    if not index.is_file():
        rep.error("index", "docs/INDEX.md", "index is missing — run with --write")
        return
    if index.read_text(encoding="utf-8") != render_index(docs):
        rep.error("index", "docs/INDEX.md",
                  "index is out of date with the documents' frontmatter — run with --write")


def check_body_placeholders(root: Path, files: list[Path], rep: Report) -> None:
    for path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        body = text
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                body = text[end + 4:]
        if PROJECT_MARKER_RE.search(body):
            rep.warn(
                "placeholder", path.relative_to(root).as_posix(),
                "body still holds an unfilled PROJECT marker",
            )


def check_changelog(root: Path, rep: Report) -> None:
    path = root / "CHANGELOG.md"
    if not path.is_file():
        return
    if not UNRELEASED_RE.search(path.read_text(encoding="utf-8")):
        rep.warn("changelog", "CHANGELOG.md", "missing '## [Unreleased]' heading")


# --------------------------------------------------------------------------- #
# INDEX.md generation
# --------------------------------------------------------------------------- #

GENERATED_MARKER = "<!-- Generated by docs_index.py"


def index_is_generated(index: Path) -> bool:
    """True when docs/INDEX.md is absent or was written by this script."""
    if not index.is_file():
        return True
    return index.read_text(encoding="utf-8").lstrip().startswith(GENERATED_MARKER)


def render_index(docs: list[Doc]) -> str:
    lines = [
        GENERATED_MARKER + " — do not edit by hand; edit the documents' frontmatter -->",
        "",
        "# Documentation index",
        "",
        "Start here. Pick the one or two documents that answer your question, then open only those.",
        "",
    ]
    by_cat: dict[str, list[Doc]] = {}
    for doc in docs:
        if doc.is_adr or doc.path.name == "ADR-TEMPLATE.md":
            continue
        by_cat.setdefault(doc.category, []).append(doc)

    for cat, heading in CATEGORIES:
        entries = sorted(by_cat.get(cat, []), key=lambda d: d.docs_rel)
        if not entries:
            continue
        lines += [f"## {heading}", "",
                  "| Document | Answers | Status | Verified |",
                  "| -------- | ------- | ------ | -------- |"]
        for doc in entries:
            summary = str(doc.fm.get("summary") or "—").replace("|", "\\|")
            status = doc.fm.get("status") or "—"
            verified = doc.fm.get("last_verified") or "—"
            if is_placeholder(summary):
                summary = "—"
            if is_placeholder(str(verified)):
                verified = "—"
            lines.append(f"| [{doc.docs_rel}](./{doc.docs_rel}) | {summary} | {status} | {verified} |")
        lines.append("")

    uncategorised = sorted(by_cat.get("", []), key=lambda d: d.docs_rel)
    if uncategorised:
        lines += ["## Other", "",
                  "| Document | Answers | Status | Verified |",
                  "| -------- | ------- | ------ | -------- |"]
        for doc in uncategorised:
            summary = str(doc.fm.get("summary") or "—").replace("|", "\\|")
            lines.append(f"| [{doc.docs_rel}](./{doc.docs_rel}) | {summary} "
                         f"| {doc.fm.get('status') or '—'} | {doc.fm.get('last_verified') or '—'} |")
        lines.append("")

    lines += [
        "## Status legend",
        "",
        "| Status | Meaning |",
        "| ------ | ------- |",
        "| `verified` | Checked against the code on `last_verified`; trust it |",
        "| `draft` | Written but never verified against the code; treat as intent, not fact |",
        "| `stale` | Known to be behind the code; read with suspicion |",
        "",
        "A document whose `covers` globs changed after its `last_verified` date is "
        "**presumed stale** even if it still says `verified`.",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Runners
# --------------------------------------------------------------------------- #

def _root_doc_paths(root: Path) -> list[Path]:
    return [root / name for name in ("README.md", "AGENTS.md", "CHANGELOG.md", "DOCUMENTATION.md")
            if (root / name).is_file()]


def _finish(rep: Report, docs: list[Doc], drift: list[dict]) -> dict:
    stale = [d for d in drift if d.get("presumed_stale")]
    stale.sort(key=lambda d: d.get("days_behind", 0), reverse=True)
    summary = (f"{len(docs)} document(s): {len(rep.errors)} error(s), "
               f"{len(rep.warnings)} warning(s), {len(stale)} presumed stale")
    return {"ok": not rep.errors, "errors": rep.errors, "warnings": rep.warnings,
            "documents": drift, "presumed_stale": stale, "summary": summary}


def detect_shape(root: Path) -> str | None:
    """Return 'single-file', 'flat', 'tree', or None when undecided."""
    docs_dir = root / "docs"
    single = (root / "DOCUMENTATION.md").is_file()
    has_docs = docs_dir.is_dir()
    if single and not has_docs:
        return "single-file"
    if not has_docs:
        return None
    for child in docs_dir.iterdir():
        if child.is_dir() and child.name in TREE_DIR_NAMES:
            return "tree"
    if any(docs_dir.glob("*.md")):
        return "flat"
    return None


def run_check(root: Path, today: date) -> dict:
    rep = Report()
    docs_dir = root / "docs"
    single = root / "DOCUMENTATION.md"
    if docs_dir.is_dir() and single.is_file():
        rep.warn("shape", ".", "both docs/ and DOCUMENTATION.md present — a project uses one shape")

    shape = detect_shape(root)
    if shape == "flat":
        for child in docs_dir.iterdir():
            if child.is_dir() and child.name not in {".", ".."}:
                rep.warn(
                    "shape", f"docs/{child.name}/",
                    "flat shape keeps all documents directly under docs/ — no subdirectories",
                )

    docs = collect_docs(root)
    if docs_dir.is_dir() and not docs:
        rep.error("structure", "docs/", "no documents found under docs/")
        return _finish(rep, [], [])

    if not docs and single.is_file():
        doc = Doc(single, root)
        docs = [doc]
        check_frontmatter(doc, rep)
        drift = [check_staleness(root, doc, rep, today)]
        check_coverage(root, docs, rep)
        link_files = [single, *_root_doc_paths(root)]
        check_links(root, list(dict.fromkeys(link_files)), rep)
        check_body_placeholders(root, link_files, rep)
        check_changelog(root, rep)
        return _finish(rep, docs, drift)

    if not docs:
        rep.error("structure", "docs/", "no documents found under docs/")
        return {"ok": False, "errors": rep.errors, "warnings": rep.warnings,
                "documents": [], "summary": "no documents found under docs/"}

    drift = []
    for doc in docs:
        check_frontmatter(doc, rep)
        if not (doc.is_adr or doc.path.name == "ADR-TEMPLATE.md"):
            drift.append(check_staleness(root, doc, rep, today))

    check_coverage(root, docs, rep)
    check_index(root, docs, rep)
    check_adrs(root, docs, rep)

    link_files = [d.path for d in docs]
    index = root / "docs" / "INDEX.md"
    if index.is_file():
        link_files.append(index)
    link_files.extend(_root_doc_paths(root))
    check_links(root, link_files, rep)
    check_body_placeholders(root, link_files, rep)
    check_changelog(root, rep)
    return _finish(rep, docs, drift)


def print_human(result: dict) -> None:
    for item in result.get("presumed_stale", []):
        print(f"STALE  {item['file']} — {item.get('days_behind', '?')} day(s) behind its covered code")
    for err in result["errors"]:
        print(f"ERROR  [{err['check']}] {err['file']}: {err['message']}")
    for warn in result["warnings"]:
        if warn["check"] == "stale":
            continue
        print(f"WARN   [{warn['check']}] {warn['file']}: {warn['message']}")
    print(result["summary"])


SAMPLE_DOCS = {
    "docs/architecture/OVERVIEW.md": (
        "---\ntitle: Architecture overview\n"
        "summary: How the system is organized and where to add code.\n"
        "status: verified\nlast_verified: 2020-01-01\n"
        "covers:\n  - \"src/**\"\n---\n\n# Architecture overview\n"
    ),
    "docs/operations/DEVELOPMENT.md": (
        "---\ntitle: Development\nsummary: Setup and everyday commands.\n"
        "status: draft\nlast_verified: 2020-01-01\n"
        "covers:\n  - \"tooling/**\"\n---\n\n# Development\n\n"
        "See [the missing one](./NOPE.md).\n"
    ),
}


def run_sample() -> dict:
    """Self-contained demo: a doc set with a dead glob and a broken link."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src").mkdir()
        (root / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
        for rel, body in SAMPLE_DOCS.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        (root / "docs" / "INDEX.md").write_text(
            render_index(collect_docs(root)), encoding="utf-8")
        result = run_check(root, date(2026, 8, 7))
    result["summary"] = "sample: " + result["summary"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate docs/INDEX.md and check documentation drift against the code.")
    parser.add_argument("--project", default=".", help="Repository root (default: cwd)")
    parser.add_argument("--check", action="store_true", help="Run checks, write nothing")
    parser.add_argument("--write", action="store_true", help="Regenerate docs/INDEX.md")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--sample", action="store_true", help="Run embedded demo data")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero on warnings too (default: errors only)")
    parser.add_argument("--force", action="store_true",
                        help="With --write: replace a docs/INDEX.md this script did not generate")
    args = parser.parse_args()

    if args.sample:
        result = run_sample()
        print(json.dumps(result, indent=2) if args.json else result["summary"])
        return 0

    root = Path(args.project).resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    if args.write:
        docs = collect_docs(root)
        if not docs:
            parser.error(f"no documents found under {root / 'docs'}")
        index = root / "docs" / "INDEX.md"
        if not args.force and not index_is_generated(index):
            msg = (f"refused: {index.relative_to(root)} was not generated by this script "
                   "— pass --force to replace it")
            print(json.dumps({"refused": str(index.relative_to(root)), "summary": msg}, indent=2)
                  if args.json else msg)
            return 1
        index.write_text(render_index(docs), encoding="utf-8")
        if not args.check:
            msg = f"wrote {index.relative_to(root)} ({len(docs)} document(s))"
            print(json.dumps({"written": str(index.relative_to(root)),
                              "documents": len(docs), "summary": msg}, indent=2)
                  if args.json else msg)
            return 0

    if not args.check and not args.write:
        parser.error("provide --check, --write, or --sample")

    result = run_check(root, date.today())
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human(result)
    if result["errors"]:
        return 1
    if args.strict and result["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
