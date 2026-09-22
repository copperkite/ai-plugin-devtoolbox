---
name: git-audit
description: >-
  Audit git hygiene — merged branches left around, stale branches, off-convention
  names and subjects, tracked secret paths. Read-only. Use when asked to audit git
  or clean up branches.
disable-model-invocation: true
metadata:
  domain: git
  role: audit
---

# Git audit

Reports. **Changes nothing** — not a branch, not a commit, not a config. The output is a
numbered list of proposed actions; deleting a branch is the user's call, or `git-intent`'s
once they pick it.

Judge against [git-conventions](../git-conventions/SKILL.md), and against the repository's own
written policy when it has one — that wins.

## What to read

The script is git-intent's `scripts/git_state.py`, at `../git-intent/scripts/git_state.py`
from this skill. `--project` is the repository being worked on (the session cwd):

```bash
python3 ../git-intent/scripts/git_state.py \
  --project . --mode audit --json
```

The JSON `findings` are the mechanical half. Each has `severity` (`blocking` / `cleanup` /
`convention`), a closed `kind`, and a `detail`. Do not re-run the git queries behind it.

`kind` values: `merged-undeleted`, `stale-branch`, `adrift-from-base`,
`off-convention-branch`, `off-convention-subject`, `tracked-secret-path`, `unpushed`,
`on-default-dirty`.

## What to report

Rank and phrase the findings. The script does not decide consequence: a tracked key is the
finding; forty off-convention subjects are noise. `stale-branch` carries a date, not a
verdict — ask whether it is abandoned. Vague subjects (`wip`) that still match the
conventional-commit regex are not in the JSON; mention them only if they matter.

History predating the convention is not a finding. The script looks at the last 30 subjects.
If the convention clearly started at some point, say where and stop reporting before it.

## Output

```
## Git audit — <branch>, <n> local branches

BLOCKING
  1. `.env` is tracked and contains real values (src/.env) — remove from the index and
     rotate what it exposed

CLEANUP
  2. 4 branches merged into main and never deleted: feat/import-csv, fix/parser, …
  3. chore/old-deps has no commit since 2025-11 and is not merged — abandoned?

CONVENTION
  4. 3 of the last 30 subjects are off-convention (all from the same day, likely a rebase)

Which do you want done?
```

Nothing above `BLOCKING` that is not genuinely blocking. An audit that cries wolf gets
ignored, and then the tracked key stays tracked.

## Constraints

- **Read-only.** Never delete a branch, never stage, never commit, never rewrite history
- **Never report a secret's value** — name the file, say what kind of secret, stop
- Numbered output, so the user can answer with numbers
- Once they pick, hand execution to [git-intent](../git-intent/SKILL.md); do not run it here
