---
name: project-intent
description: >-
  Whole-project setup, ship, make-reviewable, or "what has this project adopted".
  Use when the request spans more than one convention. Single-domain actions
  belong to their own skill.
metadata:
  domain: project
  role: orchestrator
---

# Project intent

The entry point. Domain work after install is delegated. **Install itself** is
`scripts/install.mjs` (see [references/install.md](references/install.md)).

**Direction of dependency: this skill calls domain skills; a domain skill never calls
another domain's skill.** Anything spanning two domains happens here or nowhere.

Open **one** flow file for the request. Do not load the others.

| The request is…                            | Open                                               |
| ------------------------------------------ | -------------------------------------------------- |
| Setup, adopt, `/adopt-conventions`         | [references/install.md](references/install.md)     |
| `/check-project`, mechanical health        | [references/check.md](references/check.md)         |
| `/audit-project`, judgement                | [references/audit.md](references/audit.md)         |
| "Ship this", "make this reviewable", `/pr` | [references/composite.md](references/composite.md) |
| `/release`                                 | [references/release.md](references/release.md)     |

## The config file is the memory

`.agent-adoptions.json` at the repository root. Committed — a team decision, not a
local preference. One file for every plugin; this plugin owns only the `ai-plugin-dev`
object. Other top-level keys belong to other plugins — leave them untouched.

```json
{
  "ai-plugin-dev": {
    "adopted": {
      "documentation": { "shape": "flat" },
      "git": { "model": "release-branch" },
      "release": { "scheme": "semver" },
      "code-wording": true
    }
  }
}
```

An absent key under `adopted` means not adopted: do not apply it, do not nag about it.

**There is no `gates` key above, and that is the default state of a project.** A gate is an
extra rule someone asked for on top of a convention, never a consequence of adopting one.
A project that asked for one carries it inside this plugin's object, alongside `adopted`:

```json
{ "ai-plugin-dev": { "gates": { "pr-ready": ["documentation"] } } }
```

**Only this skill reads `gates`** — a domain skill reads its own key under `adopted` and
nothing else.

**No config file → install. Config file → the project already decided; act on the record.**

## Catalog

What is available to adopt:

| Domain | Norm | Workflow |
| --- | --- | --- |
| `code-wording` | [code-wording](../code-wording/SKILL.md) *(universal)* | — |
| `documentation` | [documentation-conventions](../documentation-conventions/SKILL.md) | [documentation-intent](../documentation-intent/SKILL.md) |
| `git` | [git-conventions](../git-conventions/SKILL.md) | [git-intent](../git-intent/SKILL.md) |
| `release` | [release-conventions](../release-conventions/SKILL.md) | [release-intent](../release-intent/SKILL.md) |
| `testing` | [testing-conventions](../testing-conventions/SKILL.md) | [testing-intent](../testing-intent/SKILL.md) |

To describe a convention in a proposal, the install script puts a project-specific
`help` line on each question. Do not paste canned marketing.

## Constraints

- **Install executes in `scripts/install.mjs`.** Recording the `ai-plugin-dev` slice of
  `.agent-adoptions.json` and copying owed doc assets is that script, not this markdown.
  Other flows still orchestrate: no branch is created here, no commit message is drafted
- **Never let one domain delegate to another.** A domain skill handing control to another
  domain's skill is a bug, not a shortcut — if a rule needs two domains, it lives in this
  skill. Two norms *naming* each other's territory is not delegation and is welcome
- **A universal convention is exempt** — one that applies everywhere may be referenced by
  anything, because it delegates to nothing and cannot create a cycle. The catalog marks
  them; [code-wording](../code-wording/SKILL.md) is one
- **Never adopt without an explicit pick** — not even an obviously good default
- **The repository's own written policy wins** over the config. Report the conflict; never
  resolve it silently
- **Idempotent** — re-running install proposes the gap, never rewrites the record
- **One config file, at the root, committed** — never a per-user or per-machine variant

## Sample prompts

```
Set this project up.
```

```
Ship this.
```

```
I want this reviewable.
```

```
Is anything blocking this PR from going up for review?
```

```
What has this project adopted?
```
