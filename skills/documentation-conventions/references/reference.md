# Documentation conventions — reference

Rationale, flows, checklist, anti-patterns. The rules for *writing* a document live in
[SKILL.md](../SKILL.md) — open this file when you need why a placement exists, how a session
should read, or the audit checklist.

Machine-readable layer: [frontmatter.md](./frontmatter.md).

## Why these placements

| Choice                                                                       | Reason                                                                                                                                                                                                                                             |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, or root `SECURITY.md` | Legal terms and community process are not product or technical documentation. They have their own owners and lifecycles; a doc skill that also drafts them ends up stale on both fronts. Leave them alone when present, never flag them as missing |
| No roadmap, milestones, or idea backlog                                      | Documentation describes what *is*. Plans change faster than any document tracking them, and every project already has a tracker that owns them — a second copy in `docs/` is drift waiting to happen                                               |
| Internal security design is `THREAT-MODEL.md`, not `SECURITY.md`             | `SECURITY.md` is the name GitHub reads as the public disclosure policy — a different document for a different audience, and one this skill does not own. Keeping the names apart leaves that slot free for whoever does                            |
| `PRODUCT.md` holds the glossary                                              | Domain vocabulary and domain rules are the same knowledge; splitting them means neither gets maintained                                                                                                                                            |
| No numeric directory prefixes (`01-`, `02-`)                                 | They imply a reading order nobody follows, add noise to every path, and force renumbering when a category is inserted. Ordering is the index's job                                                                                                 |

Each piece of knowledge has one home. The writing table (tree / flat / single-file) is in
[SKILL.md](../SKILL.md#one-file-one-intention). Where two files need the same fact, one owns
it and the other links.

## On-demand files

Owed files for each shape are in [SKILL.md](../SKILL.md#owed-files). **On demand only** —
never created by default, because an empty one is worse than none:

| Shape | On-demand files                                                                                                                                                           |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tree  | `docs/operations/TESTING.md`, `docs/operations/RUNBOOKS.md`, `docs/architecture/DATA-MODEL.md`, `docs/architecture/THREAT-MODEL.md`, `docs/operations/TROUBLESHOOTING.md` |
| Flat  | `docs/TESTING.md`, `docs/RUNBOOKS.md`, `docs/DATA-MODEL.md`, `docs/THREAT-MODEL.md`, `docs/TROUBLESHOOTING.md`                                                            |

Create these when the trigger fires:

| File                 | Trigger                                                                                      |
| -------------------- | -------------------------------------------------------------------------------------------- |
| `TESTING.md`         | A test command already exists (Makefile `test`, `package.json` `scripts.test`, Cargo, Go, …) |
| `RUNBOOKS.md`        | The project is operated in production (a deploy command, or a runbook was already asked for) |
| `DATA-MODEL.md`      | The schema is large enough that a summary is faster than reading it                          |
| `THREAT-MODEL.md`    | The project has authentication, multi-tenancy, or sensitive data                             |
| `TROUBLESHOOTING.md` | The same question has been asked twice                                                       |

Infer `TESTING.md` from the repository at intake. Do **not** read `adopted.testing` — that
domain owns what a test must prove, not whether this document exists.

## Read flow (agent session)

Tree:

```
AGENTS.md
    └─► docs/INDEX.md
            ├─► decisions/README.md
            ├─► architecture/OVERVIEW.md
            ├─► operations/DEVELOPMENT.md
            └─► CHANGELOG.md [Unreleased]
```

Flat:

```
AGENTS.md
    └─► docs/INDEX.md
            ├─► DECISIONS.md
            ├─► ARCHITECTURE.md
            ├─► DEVELOPMENT.md
            └─► CHANGELOG.md [Unreleased]
```

The point of `INDEX.md` is that the agent opens **two** documents, not eight.

Read `context/` when planning or when domain vocabulary is unclear — not every session.

## Write flow (after work)

| What happened                                | Tree                                                       | Flat                        |
| -------------------------------------------- | ---------------------------------------------------------- | --------------------------- |
| User-visible behaviour shipped               | `CHANGELOG.md` → `[Unreleased]`                            | same                        |
| Structural or technology choice made         | New ADR + row in `decisions/README.md`                     | New entry in `DECISIONS.md` |
| Structure, entry point, or invariant changed | `architecture/OVERVIEW.md`                                 | `ARCHITECTURE.md`           |
| Domain term added or renamed                 | `context/PRODUCT.md` glossary (renaming also needs an ADR) | `PRODUCT.md` glossary       |
| Setup, command, or env variable changed      | `operations/DEVELOPMENT.md`                                | `DEVELOPMENT.md`            |
| Document verified against the code           | Its `last_verified` + `status: verified`                   | same                        |
| Document added, moved, or retired            | `docs/INDEX.md`                                            | same                        |

## ADR conventions

Format, statuses, immutability, numbering: [frontmatter.md](./frontmatter.md#adr-frontmatter)
and the shipped `assets/docs/decisions/README.md`.

Two points that matter most in practice:

- **Alternatives considered is not optional.** An ADR without rejected options does not
  stop the decision being re-litigated in six months, which is the only thing it is for.
- **Never edit an accepted ADR.** Supersede it. The wrong turns are the value.

## CHANGELOG

[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). `## [Unreleased]` always at the
top. Sections in order, using only those that apply: `Added`, `Changed`, `Deprecated`,
`Removed`, `Fixed`, `Security`.

Entries describe user-visible change, not commits. A new project has no releases — do not
ship a fabricated dated version.

## Audit checklist

### Presence

- [ ] Owed files for the declared shape exist
- [ ] No owed file is missing without a stated reason
- [ ] No on-demand file exists as an empty shell (worse than absent)

### Freshness — the checks that matter

- [ ] Every document under `docs/` has valid frontmatter
- [ ] For each document, code matching `covers` has not changed since `last_verified`
- [ ] Every `covers` glob still matches something
- [ ] Every top-level source directory is covered by some document
- [ ] No `verified` document older than the freshness budget (180 days)

Full list and severities: [frontmatter.md](./frontmatter.md#checks).

### Index

- [ ] `docs/INDEX.md` is generated, not hand-edited (`docs_index.py --write`)
- [ ] It matches a fresh render — no drift from the documents' frontmatter
- [ ] Every relative link resolves

### AGENTS.md

- [ ] Project context (goal, stack, type)
- [ ] Routes through `docs/INDEX.md` rather than listing every file
- [ ] Explains how to read `status` / `last_verified`
- [ ] Before-coding and after-coding rituals
- [ ] Working agreements
- [ ] Pointer to `.cursor/rules/` or `CLAUDE.md` when present

### Decisions

**Tree:**

- [ ] `decisions/README.md` index matches the files on disk
- [ ] Numbers unique, no reuse, no renumbering
- [ ] Every `superseded` ADR names its `superseded_by`
- [ ] Accepted ADRs include Alternatives considered
- [ ] No accepted ADR modified in recent history except its status

**Flat / single-file:**

- [ ] Each decision entry states why and what else was considered
- [ ] Supersessions add a new entry; old entries are not rewritten

### Separation of intent

- [ ] `README.md` holds no planning content, decision log, or troubleshooting
- [ ] `CHANGELOG.md` has `## [Unreleased]`
- [ ] Structural rationale is in an ADR (tree) or a `DECISIONS.md` entry (flat), not only in
  code comments or the architecture document
- [ ] No forward-looking plan has crept into `docs/` — that belongs in the tracker

## Anti-patterns

| Problem                                                          | Fix                                                                                                            |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Architecture doc contains a directory tree                       | Replace with the Areas glob table — trees go stale on every refactor                                           |
| Document says `verified` but the code it covers moved last month | Presume stale; verify or downgrade. This is check 1                                                            |
| Internal security design named `SECURITY.md`                     | Rename to `THREAT-MODEL.md` — that name belongs to the public disclosure policy, which this skill does not own |
| A roadmap or idea backlog appears under `docs/`                  | Move it to the issue tracker; documentation describes the present                                              |
| Accepted ADR edited to reflect the new plan                      | Revert; write a superseding ADR instead                                                                        |
| ADR with no rejected alternatives                                | Add them, or expect the debate to restart                                                                      |
| `INDEX.md` is a list of filenames                                | Add the `summary` column — `ls` already lists filenames                                                        |
| Empty on-demand file created "for later"                         | Delete; create on trigger                                                                                      |
| Placeholders left as HTML comments                               | They are invisible on GitHub: a half-filled README looks finished. Fill or remove                              |

## Edge cases

| Situation                                         | Behaviour                                                                                                         |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| A doc file already exists                         | Merge missing structural sections; never replace custom content wholesale                                         |
| `docs/` contains unrelated files                  | Leave them, but add them to `INDEX.md` — an unindexed document is invisible                                       |
| Monorepo                                          | One doc set at the repository root. Per-package docs only if the user asks, and the root `INDEX.md` links to them |
| Existing `AGENTS.md` with custom sections         | Append the index routing and rituals; ask before restructuring                                                    |
| Repository already uses a different doc structure | This skill does not migrate. Report the difference and ask                                                        |
| Root `CLAUDE.md` missing, team uses Claude Code   | Ask before adding a one-liner pointing at `AGENTS.md`; do not author a second agent guide                         |

## Out of scope

- Author `LICENSE` or any legal text
- Author `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, or a root `SECURITY.md` — community
  process and disclosure policy have their own owners
- Track future work: roadmaps, milestones, idea backlogs. That is the tracker's job
- Migrate an existing documentation tree into this structure
- Author `.cursor/rules/` or `CLAUDE.md` content
- Define stack folder layout (Next.js, Django, etc.)
- Decide whether a presumed-stale document is actually wrong — the checker flags it, a
  human or agent still has to read it
- Invent project facts. When something cannot be inferred, ask or leave the placeholder
