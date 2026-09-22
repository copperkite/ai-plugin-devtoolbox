---
name: documentation-conventions
description: >-
  Where each project document belongs and what it must contain. Use when writing
  or editing README, AGENTS, CHANGELOG, docs/, or DOCUMENTATION.md. Not for code
  comments.
metadata:
  domain: documentation
  role: norm
---

# Documentation conventions

The norm. **[documentation-intent](../documentation-intent/SKILL.md)** scaffolds and
converges a project onto it — this file says what *correct* looks like whenever a
documentation file is written or edited.

**[code-wording](../code-wording/SKILL.md) owns how the text reads.** This skill owns which
documents exist and what each one must contain.

**[testing-conventions](../testing-conventions/SKILL.md) owns what a test must prove.** This
skill owns `TESTING.md` as a document — that it exists when its on-demand trigger has
fired, and which sections it contains. How *this* project runs its suite is recorded
there; the portable rule for writing a test is not.

Open [references/frontmatter.md](references/frontmatter.md) only when filling frontmatter or
when the checker reported a frontmatter, index, or ADR-contract finding. Open
[references/reference.md](references/reference.md) for placement rationale, read/write
flows, the audit checklist, or anti-patterns. Do not load either up front.

## Precedence

A repository that already documents itself differently wins. Report the divergence once and
follow it — never move files to match this structure without being asked.

## Shapes

A project records one shape in `.agent-adoptions.json` as
`ai-plugin-dev.adopted.documentation.shape`: `single-file`, `flat`, or `tree`.
A project never mixes them.

**Single file** — `README.md`, `AGENTS.md`, `CHANGELOG.md`, `DOCUMENTATION.md` at the root.
`DOCUMENTATION.md` holds, in this order: `## Purpose`, `## Architecture`, `## Development`,
`## Decisions`, and `## Glossary` when the project has domain vocabulary. The headings are
the index.

**Flat** — one file per intention, all directly under `docs/` (no subdirectories):

```
README.md  AGENTS.md  CHANGELOG.md
docs/
  INDEX.md
  PRODUCT.md          (purpose, roles, domain rules, glossary)
  ARCHITECTURE.md
  DECISIONS.md        (one file — entries, not numbered ADRs)
  DEVELOPMENT.md
  [TESTING.md], [RUNBOOKS.md]
  [DATA-MODEL.md], [THREAT-MODEL.md], [TROUBLESHOOTING.md]
```

**Tree** — one file per intention, grouped in subdirectories:

```
README.md  AGENTS.md  CHANGELOG.md
docs/
  INDEX.md
  context/       PRODUCT.md (purpose, roles, domain rules, glossary)
  architecture/  OVERVIEW.md, [DATA-MODEL.md], [THREAT-MODEL.md]
  decisions/     README.md (index), ADR-TEMPLATE.md, ADR-NNNN-*.md
  operations/    DEVELOPMENT.md, [TESTING.md], [RUNBOOKS.md], [TROUBLESHOOTING.md]
```

`[bracketed]` files exist **on demand only** — an empty one is worse than none. Triggers:
[reference](references/reference.md#on-demand-files).

### Owed files

| Shape         | Always owed                                                                                                              |
| ------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `single-file` | `README.md`, `AGENTS.md`, `CHANGELOG.md`, `DOCUMENTATION.md`                                                             |
| `flat`        | Root trio + `docs/INDEX.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `DEVELOPMENT.md`                           |
| `tree`        | Root trio + `docs/INDEX.md`, `context/PRODUCT.md`, `architecture/OVERVIEW.md`, `decisions/`, `operations/DEVELOPMENT.md` |

Default for an empty repository: **`flat`**. Infer from disk when something already exists:
`DOCUMENTATION.md` without `docs/` → `single-file`; `docs/` with `context/`, `architecture/`,
`decisions/`, or `operations/` → `tree`.

## One file, one intention

| The question                        | Tree                             | Flat                   | Single file       |
| ----------------------------------- | -------------------------------- | ---------------------- | ----------------- |
| What is this product, for whom      | `docs/context/PRODUCT.md`        | `docs/PRODUCT.md`      | `## Purpose`      |
| How is it built, what talks to what | `docs/architecture/OVERVIEW.md`  | `docs/ARCHITECTURE.md` | `## Architecture` |
| How do I run and change it          | `docs/operations/DEVELOPMENT.md` | `docs/DEVELOPMENT.md`  | `## Development`  |
| Why was it built that way           | `docs/decisions/ADR-NNNN-*.md`   | `docs/DECISIONS.md`    | `## Decisions`    |
| The domain vocabulary               | `docs/context/PRODUCT.md`        | `docs/PRODUCT.md`      | `## Glossary`     |
| How do I operate it in production   | `docs/operations/RUNBOOKS.md`    | `docs/RUNBOOKS.md`     | — outgrow first   |
| How does *this* repo run its suite  | `docs/operations/TESTING.md`     | `docs/TESTING.md`      | — in Development  |
| What shipped, when                  | `CHANGELOG.md`                   | `CHANGELOG.md`         | `CHANGELOG.md`    |
| How does an agent work in this repo | `AGENTS.md`                      | `AGENTS.md`            | `AGENTS.md`       |

A single-file project that needs a runbook, a data model, or a threat model has outgrown the
shape. A flat project that needs numbered ADRs or several architecture documents has
outgrown flat — migrate to tree. Say so; do not bolt the missing shape on.

The glossary in `PRODUCT.md` is the vocabulary [code-wording](../code-wording/SKILL.md)
requires the code to follow.

## What this covers, and what it does not

**Subject: product and technical documentation only.** Never `LICENSE`, `CONTRIBUTING.md`,
`CODE_OF_CONDUCT.md`, or a root `SECURITY.md`. Leave them untouched; never create them;
never report them as missing. Internal security design is `THREAT-MODEL.md` (under
`docs/architecture/` in tree, or `docs/` in flat), not `SECURITY.md`.

**Surface: the project's own files.** Never treat as this project's documentation:

- vendored agent tooling (`.claude/`, `.cursor/`, …)
- `skills/**`, `commands/**`, `agents/**` (what a plugin ships)
- any `<skill>/assets/` tree (unfilled `<!-- PROJECT: … -->` markers are the point)

**Time: the present, plus decided history.** Roadmaps belong in the issue tracker.

**Document the project, not the tool that documented it.** Ask "would this sentence be true
if a human had written it?"

## Frontmatter

**Flat and tree**: every file under `docs/` carries `title`, `summary`, `status`,
`last_verified`, `covers`. **Single file**: the same block once, at the top of
`DOCUMENTATION.md`.

- `summary` — one line stating what the document answers
- `covers` — globs of the code it describes; `[]` when it describes none
- `last_verified` — date it was actually read against that code. **Never advance without reading**
- `status: draft` on anything freshly scaffolded

Field-by-field contract: [references/frontmatter.md](references/frontmatter.md).

`docs/INDEX.md` is generated from frontmatter, never hand-written.

## ADRs

**Single file and flat**: one entry per decision (`## Decisions` or `docs/DECISIONS.md`),
newest last. Each states what was decided, why, and what else was considered. Superseding
means a new entry plus a note on the old one, never a rewrite.

**Tree**: numbered `ADR-NNNN-kebab-title.md`, sequential, never reused. An accepted ADR is
immutable. Accepted ADRs state *Alternatives considered*. `docs/decisions/README.md` indexes
them.

Statuses and template: [references/frontmatter.md](references/frontmatter.md#adr-frontmatter).

## CHANGELOG

Keep a Changelog format, with a `## [Unreleased]` section that actually gets used. What
shipped — not what is planned.

## Writing rules

- **Never invent a project fact.** Ask, or leave the placeholder visible.
- **Merge, never overwrite.**
- Placeholders are HTML comments (`<!-- PROJECT: … -->`). An unfilled one must be called out
  in prose.
