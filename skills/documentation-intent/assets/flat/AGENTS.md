# Agent guide — <!-- PROJECT: name -->

Read this first when starting a session on this project.

## 1. Project context

- **Goal**: <!-- PROJECT: goal -->
- **Type**: <!-- PROJECT: type — e.g. web application, library, monorepo -->
- **Stack**: <!-- PROJECT: stack -->

## 2. Where to look

**[docs/INDEX.md](./docs/INDEX.md) is the routing table.** It lists every document with a
one-line summary and a freshness status. Read it, pick the one or two documents that
answer your question, and open only those. Do not load the whole `docs/` set.

| You need                                      | Go to                           |
| --------------------------------------------- | ------------------------------- |
| Domain vocabulary, user roles, business rules | `docs/PRODUCT.md`               |
| Structure, entry points, where to add code    | `docs/ARCHITECTURE.md`          |
| Why something is the way it is                | `docs/DECISIONS.md`             |
| How to run and change it                      | `docs/DEVELOPMENT.md`           |
| What shipped recently                         | `CHANGELOG.md` → `[Unreleased]` |

Project-specific conventions (design, domain rules): `.cursor/rules/` and `CLAUDE.md`
when present — they override generic defaults.

## 3. Trusting the docs

Each document declares `status` and `last_verified` in its frontmatter.

- `verified` — checked against the code on that date; trust it
- `draft` — never verified; treat as intent, not fact
- `stale` — known to be behind the code

**A document whose `covers` globs changed after `last_verified` is presumed stale**, even
if it still says `verified`. When you find one, check it against the code: if it is right,
update `last_verified`; if it is wrong, fix it or mark it `stale` — do not silently rely
on it.

## 4. Before coding

1. `docs/INDEX.md` — which documents cover this area?
2. `docs/DECISIONS.md` — is there an accepted decision constraining this work?
3. `docs/ARCHITECTURE.md` — invariants and extension points for the area you touch
4. `CHANGELOG.md` → `[Unreleased]` — what changed recently

## 5. After coding

| Change                                       | Update                             |
| -------------------------------------------- | ---------------------------------- |
| User-visible behaviour shipped               | `CHANGELOG.md` → `## [Unreleased]` |
| Structural or technology choice made         | New entry in `docs/DECISIONS.md`   |
| Structure, entry point, or invariant changed | `docs/ARCHITECTURE.md`             |
| Domain term added or renamed                 | `docs/PRODUCT.md` glossary         |
| Setup, command, or env variable changed      | `docs/DEVELOPMENT.md`              |
| A document added, moved, or retired          | `docs/INDEX.md`                    |

When you verify a document against the code, bump its `last_verified` and set
`status: verified`. This is the only thing keeping the doc set honest.

## 6. Working agreements

- Code, comments, and documentation in English
- Minimal diff — only change what the task requires
- Never rewrite an accepted decision entry; supersede it with a new one
- Ask before overwriting custom work or deviating from an accepted decision
- Do not commit unless the user explicitly asks
