---
name: git-conventions
description: >-
  Branch names, conventional commits, and pull-request merge rules. Use when
  creating a branch, writing a commit, or opening a PR. Not for tags or semver.
metadata:
  domain: git
  role: norm
---

# Git conventions

The policy. `git-intent` is what executes it — this file is the single source of truth for
*what is allowed*, and it never runs commands itself.

## Precedence

The project repository wins when it has written its own policy. Check, in order:

1. `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/`
2. `CONTRIBUTING.md`, or a git section under `docs/`
3. The branches that already exist (`git branch -a`) — match a clear local convention

Only when none of those say anything do the rules below apply. When the repo contradicts
this guide, follow the repo and say so once.

## The one rule

**`main` is written to by pull request only.** Never commit on it, never merge into it
locally, never push to it directly. Every change reaches `main` through a reviewed PR.

## Branch naming

`<type>/<kebab-description>` — lowercase, hyphens, no spaces, no trailing slash.

| Type       | For                              |
| ---------- | -------------------------------- |
| `feat`     | New capability                   |
| `fix`      | Bug fix                          |
| `docs`     | Documentation only               |
| `refactor` | Restructure, no behaviour change |
| `perf`     | Performance                      |
| `test`     | Tests only                       |
| `chore`    | Maintenance, dependencies        |
| `build`    | Build system, packaging          |
| `ci`       | CI configuration                 |
| `hotfix`   | Urgent production fix, rare      |

A ticket number may prefix the description: `feat/1234-import-csv`. Use it or don't — but
be consistent within a repository.

## Release branches

Default: work branches cut from `main`, PR back to `main`. One branch, one PR, done.

Use a **release branch** only when several developers or agents are building a batch of
features that must ship together:

```
main
 └── release/<name>              cut from main, shared, long-lived
      ├── feat/import-csv        cut from the release branch → PR targets it
      ├── feat/export-xlsx       cut from the release branch → PR targets it
      └── fix/parser-crash       cut from the release branch → PR targets it
                                 ↓
                          PR release/<name> → main   (merge commit)
```

- Work branches inside a release keep normal names — no nested `feat/<release>/<thing>`.
- Their PRs target the release branch, not `main`.
- One final PR takes the release branch into `main`.

**Staying current — the rule differs by branch, because one is shared and one is not:**

| Branch           | Shared?             | How it catches up        |
| ---------------- | ------------------- | ------------------------ |
| `release/<name>` | yes, several people | **merge** `main` into it |
| a work branch    | no, one author      | **rebase** onto its base |

Never rebase a release branch — someone else has it checked out.

## Commits

Conventional commits, every time:

```
<type>[optional scope]: <description>
```

Same type list as the branch table, plus `revert`. Breaking change: `feat!:` or a
`BREAKING CHANGE:` footer.

- English, imperative, lowercase after the colon, no trailing period, subject ≤ 72 chars
- One logical change per commit — a commit that needs "and" in its subject is two commits
- A body only when the *why* is not obvious from the subject and the diff. Never paraphrase
  the diff in prose
- Footers when they carry information: `Closes #12`, `BREAKING CHANGE: …`

**Never in a commit message, a PR title, or a PR body:** `Co-Authored-By: Claude`,
`🤖 Generated with Claude Code`, any emoji, any attribution to a tool.

Never stage a secret — `.env` with real values, API keys, tokens, private keys.

## Pull requests

- **Title**: conventional commit format, same as the commit it summarises.
- **Opened as a draft on the first push.** Marked ready when it is genuinely reviewable.
- **Body**: three sections, nothing more.

```markdown
## Summary
One or two sentences: what this changes and why.

## Changes
- …

## Test plan
- [ ] …
```

- Link the issue in the body (`Closes #12`) rather than in the title.

## Merging

| PR                           | Strategy         | Why                                        |
| ---------------------------- | ---------------- | ------------------------------------------ |
| work branch → `main`         | **squash**       | One feature, one commit on `main`          |
| work branch → release branch | **squash**       | Same                                       |
| release branch → `main`      | **merge commit** | Keeps the per-feature history of the batch |

After a merge, delete the branch — local and remote.

## Rewriting history

- Force-push only onto your own unshared branch, and only with `--force-with-lease`.
- Never force-push `main` or a release branch.
- Prefer `git revert` over `reset --hard` on anything already pushed.
- Amend only a commit that has not been pushed.

## Out of scope

Tags, semver, and what a release is belong to
[release-conventions](../release-conventions/SKILL.md), not here — a tag has no meaning
outside a release. This guide governs branches, commits, and merges up to the point a version
is cut.

Publishing to a registry stays per-project: read the project's own docs.
