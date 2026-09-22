---
name: testing-intent
description: >-
  Bring this change's tests up to date: find gaps, write the missing tests, run
  the project's test command. Use when asked to add tests, when a change has no
  tests, or when tests are red. Not for whole-project "ship this" — that belongs
  to project-intent.
disable-model-invocation: true
metadata:
  domain: testing
  role: workflow
---

# Testing intent

One intent: **bring this change's tests to a state that would catch a regression.**

Read what actually changed, name the gaps, write the missing tests, run the project's
command.

**What a test must prove is not defined here** — the one rule, layout, mocking, and how to
find the runner all live in **[testing-conventions](../testing-conventions/SKILL.md)**. Open
that skill for the rules that apply to the tests you are writing.

## Step 1: Read the state

Always. Even when the user points at a file. One command — do not re-run the git queries
behind it. The script is `scripts/testing_state.py` beside this SKILL.md; `--project` is
the repository being worked on (the session cwd):

```bash
python3 scripts/testing_state.py \
  --project . --json
```

Act on the JSON. `runner` is how this project runs tests (`null` if none was found).
`unpaired` is changed source with no test file on disk. `pairedUnchanged` is changed source
whose test file exists but is not part of this change. `changedTests` is test files in the
change. Do not re-walk the tree to recompute them.

Then read `.agent-adoptions.json` → `ai-plugin-dev.adopted` when present — **read only the
`testing` key**. Absent, or no `testing` key: apply
[testing-conventions](../testing-conventions/SKILL.md) as written. What other domains have
adopted is none of this skill's business.

If the script cannot be located, list the changed source files against the pairing rules in
the norm, by hand.

## Step 2: Name the state

| State      | Reads as                                                                              | Converge with    |
| ---------- | ------------------------------------------------------------------------------------- | ---------------- |
| `no-runner`  | `runner` is `null`                                                                  | Stop, ask        |
| `uncovered`  | `unpaired` is non-empty                                                             | A → C            |
| `unjudged`   | `pairedUnchanged` is non-empty, `unpaired` is empty                                 | B → C            |
| `unrun`      | Gaps closed (or none); the suite has not been run this pass                         | C                |
| `red`        | The project's command exited non-zero                                               | D                |
| `current`    | Paired tests exist for the change, or none were needed; the command is green        | Report           |

A change is often `uncovered` and `unjudged` at once. Write the missing tests first, then
read the ones that already exist.

**`runner` present is not `current`.** Finding `make test` does not mean it has been run.

## Step 3: Show the plan, then act

Print it before writing anything:

```
testing state
  now:    uncovered · 2 unpaired (src/parse.ts, src/format.ts)
          · runner: make test
  target: current
  steps:  1. add src/parse.test.ts (observable return values)
          2. add src/format.test.ts
          3. run make test
```

Ask **once** for the whole plan. Then run the operations in order, stopping at the first
one that cannot proceed without an answer.

**No intent given** — "are the tests ok?", "did I miss tests?" — do not print a menu.
Report the state in two lines and propose the single next step.

**"Ship it", "make this reviewable"** and similar whole-project requests are not testing
intents — they may require conventions this skill knows nothing about. They belong to
[project-intent](../project-intent/SKILL.md), which calls this skill as one of its steps.

---

## Operations

### A. Write the missing tests

For each path in `unpaired`. Follow [testing-conventions](../testing-conventions/SKILL.md):
the one rule, the layout already in the repository, no mock of the unit under test.

Match the surrounding tests — runner, assertion style, fixture layout. A new helper,
factory, or folder is a last resort.

A path in `unpaired` that only restructures, with nothing a test could observe, is not a
gap. Drop it from the plan and say why.

### B. Judge the tests that already exist

For each path in `pairedUnchanged`. Open the paired test file. Would it have failed
without this change?

- **Yes** — leave it. The gap is already closed.
- **No** — extend it so the new behaviour is an expected value, not a tautology. Same
  file; do not start a second suite next to it.

This is judgement the script cannot do. Do not skip it because the file exists.

### C. Run the project's command

Exactly `runner.command`. No extra flags, no different package manager, no "just this
file" unless the user asked for a filter.

If `runner` is `null`, stop. Report what was looked for (Makefile `test`, `package.json`
`scripts.test`, Cargo, Go, Python) and ask which command to record. Do not invent one.

### D. A red suite

Fix the code or the test. **Never delete or weaken a test to get to green.** A test that
failed for a real reason is the convention working.

If the failure is unrelated to this change (already red on the base branch), say so and
stop — do not expand the change to include it unless the user asks.

## What this never does

- **Never invents a runner.** The script names one or it names none
- **Never writes `TESTING.md`.** That document belongs to documentation; this skill writes
  tests
- **Never holds up a pull request on its own.** A gate is a project rule, read by
  project-intent
- **Never "skips tests because it's obvious."** The one rule has no exception for size
- **Never runs a different command than `runner.command`** to save time

## Sample prompts

```
Add tests for this change.
```

```
Did I miss any tests?
```

```
The suite is red — fix it without weakening the tests.
```

```
Where do tests stand on what I just wrote?
```
