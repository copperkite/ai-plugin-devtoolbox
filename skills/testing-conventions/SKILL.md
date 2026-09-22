---
name: testing-conventions
description: >-
  How tests are written and when a change is unfinished. Use when adding or
  changing behaviour, writing a test, or deciding whether tests are enough. Not
  for CI config or the TESTING.md document layout.
metadata:
  domain: testing
  role: norm
---

# Testing conventions

The policy: **what a test must prove, and when a change is unfinished.**
[testing-intent](../testing-intent/SKILL.md) is what executes it — this file runs nothing.

Two neighbours own the rest, and saying where they start is part of the job.
**[documentation-conventions](../documentation-conventions/SKILL.md) owns `TESTING.md`** —
that the file exists when its on-demand trigger has fired, and which sections it contains.
How *this* project runs its suite is recorded there.
**[code-wording](../code-wording/SKILL.md) owns how test names and assertion messages read.**
This skill owns the portable rule for writing a test.

## Precedence

The project repository wins when it already tests its own way. Check, in order:

1. `docs/operations/TESTING.md`, `docs/TESTING.md` (flat), or a Testing heading in
   `DOCUMENTATION.md`
2. `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/`
3. The tests that already exist — match a clear local convention, including one this guide
   would not have chosen

A repository that colocates `*.test.ts` does not want a new `tests/` folder invented next to
them. Follow it, and say so once.

## The one rule

**A behaviour change is unfinished until a test exists that would have failed without that
change.** A test that re-implements the code to compute the expected value proves nothing.

```
bad:   expect(add(2, 3)).toBe(add(2, 3))
bad:   expect(result).toEqual(fn(input))   // fn is the unit under test
good:  expect(add(2, 3)).toBe(5)
```

The expected value is a fact about the world, written by someone who knows it, not derived
from the same function that is meant to be under test.

## Where tests live

Look at the repository first. Two layouts are both correct; mixing them in one project is
not.

- **Colocated** — `invoice-parser.ts` next to `invoice-parser.test.ts` (or `_test.py`,
  `_test.go`, …). Default when the repo has not already chosen.
- **A top-level `test/` or `tests/` directory** — reserved for genuinely cross-cutting
  coverage (an end-to-end pass, a fixture shared by many files), not a dumping ground for
  every unit test.

New tests follow the layout already in use. Never introduce the other one.

## What to test

Observable behaviour: return values, files written, exit codes, errors raised, the shape of
what a caller sees.

Not: private helpers, framework wiring, types the compiler already checks, implementation
structure that can change without anyone outside noticing.

A change that only restructures, and that no test could observe, does not need a new test.
Say so; do not invent one for coverage.

## What not to mock

**The unit under test.** Mock only a boundary this project does not own — a network, a
clock, another process. Mocking everything tests the mocks.

When the surrounding tests already run the real thing against a temp directory, follow
them. Do not introduce a mock that the file next door does not use.

## How to run

The project's own command, in this order of discovery: a Makefile `test` target,
`package.json` `scripts.test`, `cargo test`, `go test ./...`, then a Python test runner
already configured in the repo.

**Never invent a runner.** A project with `make test` does not want `npx vitest` because
the agent prefers it. CI and the local command must be the same command; if they differ,
the project's `TESTING.md` (or CI) wins and the local docs are wrong.

## Out of scope

| Not here                               | There                                                              |
| -------------------------------------- | ------------------------------------------------------------------ |
| `TESTING.md` layout and its sections   | [documentation-conventions](../documentation-conventions/SKILL.md) |
| Identifier spelling, assertion wording | [code-wording](../code-wording/SKILL.md)                           |
| CI pipelines, required GitHub checks   | the project's own CI                                               |
| Coverage percentages as a goal         | — not a number this convention tracks                              |

Publishing or merging with a red suite is a project gate, not a testing rule. Adopting this
convention does not by itself hold up a pull request — that is a `gates.pr-ready` entry
someone asks for.
