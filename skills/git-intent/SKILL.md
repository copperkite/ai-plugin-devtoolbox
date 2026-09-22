---
name: git-intent
description: >-
  Commit, push, branch, rebase, or open a pull request. Use when the user names a
  git action or asks where the branch stands. Not for whole-project "ship this"
  requests — those belong to project-intent.
disable-model-invocation: true
metadata:
  domain: git
  role: workflow
---

# Git intent

The user names a destination — in their own words — and this skill gets the repository
there. It reads the actual state first, never assumes it.

Policy comes from **[git-conventions](../git-conventions/SKILL.md)**: branch names, commit
format, merge strategy, what is forbidden. This skill decides *what to do next*; that one
decides *what is allowed*. When the project repo has its own written policy, that wins — see
the precedence rules there.

## Step 1: Read the state

Always. Even when the user's request seems obvious. One command — do not re-run the git
queries it already wrapped. The script is `scripts/git_state.py` beside this SKILL.md;
`--project` is the repository being worked on (the session cwd):

```bash
python3 scripts/git_state.py \
  --project . --mode state --json
```

Act on the JSON. `named` is the primary state; `flags` are orthogonal (`behind-base`,
`on-default-branch`, `detached`, `rebase-in-progress`). `pr` is `null` when `gh` is missing
or unauthenticated — `notes` then contains `gh-unavailable`. Say so plainly, give the
command or the URL, and do the local half of the work. Never invent a PR number or a CI
result.

Then read `.agent-adoptions.json` → `ai-plugin-dev.adopted` when present — it records
which git model this project uses. Absent, or no `git` key: apply
[git-conventions](../git-conventions/SKILL.md) as written. **Read only the `git` key** —
what other domains (and other plugins) have adopted is none of this skill's business.

## Step 2: Name the current state

Use `named` from the JSON. Do not recompute it.

| `named`     | Means                                            |
| ----------- | ------------------------------------------------ |
| `dirty`     | Uncommitted changes in the working tree          |
| `clean`     | Nothing to commit, nothing unpushed              |
| `committed` | Commits exist locally that are not on the remote |
| `pushed`    | Branch exists on the remote, up to date, no PR   |
| `draft-pr`  | A PR is open, in draft                           |
| `ready-pr`  | The PR is marked ready for review                |
| `merged`    | The PR is merged                                 |

Report every `flags` entry. `behind-base` changes the plan.

## Step 3: Map the intent to a target

The user speaks freely. Map what they said onto one target state.

| They say something like…                      | Target       |
| --------------------------------------------- | ------------ |
| "save this", "commit", "wrap up what I did"   | `committed`  |
| "push", "back it up", "end of day"            | `pushed`     |
| "open a PR", "share it", "let people see it"  | `draft-pr`   |
| "mark it ready", "ask for review"             | `ready-pr`   |
| "merge the PR", "land it"                     | `merged`     |
| "update me on main", "catch up", "I'm behind" | `synced`     |
| "start something new", "new branch"           | a new branch |

**No intent given** — "git?", "where am I?" — do not print a menu. Report the state in two
lines and propose **the single next logical step**.

**"Ship it", "make this reviewable"** and similar whole-project requests are not git intents
— they may require conventions this skill knows nothing about. They belong to
[project-intent](../project-intent/SKILL.md), which calls this skill as one of its steps.

## Step 4: Show the plan, then act

Always print the plan before touching anything:

```
main..feat/import-csv
  now:    dirty (4 files) · 2 unpushed commits · behind release/q3 by 6
  target: draft-pr
  steps:  1. commit the parser changes (feat)
          2. commit the test fixtures (test)
          3. rebase onto release/q3
          4. push
          5. open a draft PR targeting release/q3
```

Ask **once** for the whole plan. Not step by step.

Two exceptions that get their own confirmation right before they happen, because they are
not reversible:

- **merging a PR**
- anything the user did not ask for that rewrites pushed history

Then execute. Stop at the first step that fails and explain — do not improvise past it.

## Step 5: Report

Two lines. Where the branch stands now, and the next step available. Nothing else.

## Awkward states

These are the reason this skill exists. Handle each explicitly.

**Commits sitting on the default branch** (`on-default-branch` in `flags`, and `named` is
not `clean`). Do not push. Propose: create the correct branch at HEAD, reset the default
branch back to its upstream, continue there.

```bash
git branch feat/<description>
git reset --hard @{upstream}    # only after the branch above exists and the user agreed
git checkout feat/<description>
```

**A working tree mixing several subjects.** Do not write one catch-all commit message.
Read the diff, propose a split into named commits, and stage them path by path. If the
split is genuinely impossible to determine, ask — do not guess.

**Behind the base.** Propose catching up *before* pushing, using the rule that matches the
branch: rebase a personal work branch, merge into a shared release branch.

**A rebase or merge conflict.** Stop. List the conflicted files, say what the two sides
are. Never resolve a conflict the user has not seen.

**Detached HEAD, unfinished rebase, stash in the way.** `flags` names `detached` and
`rebase-in-progress`. Say what unblocks it. Do not run `git rebase --abort` or drop a stash
on your own initiative.

**Base branch ambiguity.** A work branch inside a release cuts from the release branch, not
`main`. Use `base` from the JSON — never assume `main`.

## Before every commit

Scan the staged diff for secrets — `.env` files with real values, API keys, tokens, private
keys, credentials in fixtures. Refuse to stage them and say which file.

## Never, unless the user asks for it in those words

- Force-push `main` or a release branch
- `git reset --hard` with uncommitted work present
- Delete a remote branch
- Rewrite history that has been pushed
- Commit or push when the user only asked you to look

## Sample prompts

```
Where am I on this repo?
```

```
Commit this — I think it's two changes, not one.
```

```
I'm behind the release branch, catch me up.
```

```
I made a mess, commits ended up on main.
```
