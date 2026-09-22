---
name: release-conventions
description: >-
  Semver, tag format, and what a release is. Use when choosing a version or
  cutting a release. Not for branching or publishing.
metadata:
  domain: release
  role: norm
---

# Release conventions

The policy: **what a version number means, and what makes a release well formed.**
[release-intent](../release-intent/SKILL.md) is what executes it — this file runs nothing.

Two neighbours own the rest, and saying where they start is part of the job.
**[git-conventions](../git-conventions/SKILL.md) owns branches, commits, and merges.**
**[documentation-conventions](../documentation-conventions/SKILL.md) owns the CHANGELOG's
format.** This skill owns the number, the tag, and the moment.

## Precedence

The project repository wins when it already releases its own way. Check, in order:

1. `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/`
2. `CONTRIBUTING.md`, `RELEASING.md`, or a release section under `docs/`
3. The tags that already exist (`git tag --list`) — match a clear convention, including one
   this guide would not have chosen

A repository tagging `2024.03` has a calendar scheme and does not want semver. Follow it, and
say so once.

## The version of record

**One file holds the version, and the project knows which.** It is the one its ecosystem
already reads:

| Ecosystem     | Version of record             |
| ------------- | ----------------------------- |
| Node          | `package.json`                |
| Rust          | `Cargo.toml`                  |
| Python        | `pyproject.toml`              |
| Go            | the tag itself, no file       |
| Anything else | a plain `VERSION` at the root |

When more than one file carries a version, the project names the authoritative one and the
rest follow it:

```json
{ "ai-plugin-dev": { "adopted": { "release": { "scheme": "semver", "version-file": "package.json" } } } }
```

**Never guess between two candidates**, and never hand-edit a version some tool owns — a
lockfile, a generated manifest, a stamp written by a scaffolder. Those are outputs. Editing
one desynchronises it from whatever writes it, and the next run overwrites the edit anyway.

## Semantic versioning

`MAJOR.MINOR.PATCH`. The number is **derived from what shipped**, never picked by feel.

| Committed since the last tag                         | Next       |
| ---------------------------------------------------- | ---------- |
| any `feat!`, or a `BREAKING CHANGE:` footer          | **major**  |
| any `feat:`                                          | **minor**  |
| only `fix:`, `perf:`, `refactor:`, `docs:`, `chore:` | **patch**  |
| nothing a consumer can observe                       | no release |

Deriving the version from commit types is what the commit convention buys — a history that
cannot answer "was anything breaking" makes every release a guess.

**Breaking means a consumer must change something to keep working**: a removed export, a
renamed flag, a changed default, a new required argument, a raised minimum runtime.
Restructuring nobody outside can observe is not breaking, however large the diff.

**Below `1.0.0` the promise is weaker, not absent.** A breaking change bumps the minor
(`0.4.2` → `0.5.0`); a feature bumps the patch. Reaching `1.0.0` is a decision someone makes
out loud — never one inferred from a commit.

## Tags

`v<version>`, so `v1.4.0`. **Annotated, never lightweight** — `git tag -a v1.4.0 -m "…"` —
because an annotated tag carries its own date and author, and a lightweight one carries
nothing.

- One tag per release, on the commit that carries the version bump
- On the default branch. A tag on a branch that never merged points at history nobody has
- **Never move or delete a published tag.** Something is already pinned to it. A botched
  release is corrected by the next release, not by rewriting the last one

## Prereleases

`v1.4.0-rc.1`, `-beta.2`, `-alpha.1` — a suffix on the version that is *coming*, never on one
that shipped. Only when someone actually installs it to test; a prerelease nobody consumes is
ceremony. The final release drops the suffix and keeps the number.

## The CHANGELOG at release time

`documentation-conventions` owns the format. This is the one transition it does not describe:

- `## [Unreleased]` becomes `## [1.4.0] - 2026-08-16`, dated the day it is tagged, ISO 8601
- A fresh, empty `## [Unreleased]` goes back on top
- **The entries themselves are not rewritten.** They were written when each change shipped, by
  someone who knew what it did. Regrouping them under `Added` / `Changed` / `Fixed` is fine;
  rephrasing them after the fact is how a changelog turns into fiction
- **An empty `[Unreleased]` means there is nothing to release.** Say so and stop. Never read
  the commits and invent the entries that should have been written

## A release is well formed when

- every entry under the new version describes a change someone outside can notice
- the version of record, the tag, and the CHANGELOG heading say the same thing
- the tag is annotated and sits on the default branch
- nothing was left behind under `[Unreleased]`

## Out of scope

| Not here                                | There                                                              |
| --------------------------------------- | ------------------------------------------------------------------ |
| Branch names, commits, merges, PRs      | [git-conventions](../git-conventions/SKILL.md)                     |
| The CHANGELOG's format and its sections | [documentation-conventions](../documentation-conventions/SKILL.md) |
| Publishing to a registry, CI pipelines  | the project's own CI                                               |

Publishing is absent on purpose. `npm publish`, a container push, a store submission are
per-project, credentialed, and irreversible. **A release ends at the tag** — what watches for
that tag is the project's business, not this convention's.
