# Frontmatter and index contract

The machine-readable layer of the doc set. It exists so that documentation drift can be
**detected automatically** instead of noticed by accident.

This file is the specification. It is implemented by `docs_index.py`, shipped with
[documentation-intent](../../documentation-intent/SKILL.md) — see [Tooling](#tooling) at the end.

## Why

Presence checks are cheap and near-worthless: a doc set can be complete, well separated,
and entirely wrong. A confidently wrong `OVERVIEW.md` is worse than no `OVERVIEW.md`,
because an agent reads it and codes against a system that no longer exists.

The contract below gives every document two things it normally lacks: a **claim about what
code it describes** (`covers`) and a **date that claim was last checked** (`last_verified`).
With both, staleness becomes computable from git history.

## Document frontmatter

Every file under `docs/` carries YAML frontmatter:

```yaml
---
title: Architecture overview
summary: How the system is organized, where execution starts, and where to add new code.
status: verified
last_verified: 2026-08-07
covers:
  - "src/**"
  - "!src/generated/**"
---
```

| Field           | Required | Type                             | Purpose                                                                                        |
| --------------- | -------- | -------------------------------- | ---------------------------------------------------------------------------------------------- |
| `title`         | yes      | string                           | Human title; the index displays it                                                             |
| `summary`       | yes      | string, one line                 | **The routing signal.** Must let a reader decide whether to open the file without opening it   |
| `status`        | yes      | `draft` \| `verified` \| `stale` | Trust level                                                                                    |
| `last_verified` | yes      | `YYYY-MM-DD`                     | Date the content was checked against the code                                                  |
| `covers`        | yes      | list of globs                    | Code this document claims to describe. `[]` means "describes no code" (valid for `PRODUCT.md`) |

ADR files use a variant — see [ADR frontmatter](#adr-frontmatter).

### Writing `summary`

It is the only thing most readers see. One sentence, no marketing, phrased as what the
document answers. `"Postgres schema, ownership rules, and API contracts"` routes correctly;
`"Documentation about the data"` does not.

### Writing `covers`

Globs, never directory trees — a tree goes stale on every refactor, a glob survives one.
Negations with `!` are allowed. Point at the code the document *describes*, not the code
that happens to be nearby: an over-broad `covers` makes every commit look like drift and
trains people to ignore the signal.

### `status` semantics

| Status     | Meaning                                                       | Set by                                    |
| ---------- | ------------------------------------------------------------- | ----------------------------------------- |
| `draft`    | Written but never checked against the code — intent, not fact | Author at creation                        |
| `verified` | Checked on `last_verified`; trust it                          | Whoever verified it                       |
| `stale`    | Known to be behind the code                                   | Anyone who spots it and cannot fix it now |

**Derived staleness overrides the declared status.** If any file matching `covers` has a
commit newer than `last_verified`, the document is *presumed stale* regardless of what the
field says. This is the whole point of the contract: nobody has to remember to downgrade
a document, git does it for them.

## docs/INDEX.md

A routing table so an agent reads one 30-line file, picks two documents, and opens those
— instead of loading the whole tree.

**Generated, never hand-written.** `docs_index.py --write` builds it from frontmatter;
editing it by hand is pointless because the next run overwrites it. Fix the frontmatter.

Requirements:

- **Committed to the repository.** Agents read the repo, not CI artifacts. A generated
  index that only exists in a build is useless.
- Grouped by category, in this order: Context, Architecture, Decisions, Operations.
- One row per document: link, `summary`, `status`, `last_verified`.
- Mirrors frontmatter exactly — it is derived data.
- ADR files are not listed individually; `decisions/README.md` is their index.

A listing of filenames is not an index — `ls` already does that. The `summary` column is
what earns the file.

## ADR frontmatter

```yaml
---
title: Use PostgreSQL as the single primary datastore
summary: One line stating the decision, actionable without opening the file.
status: accepted
date: 2026-08-07
deciders: "@alice, @bob"
superseded_by: null
---
```

| Field           | Values                                                                          |
| --------------- | ------------------------------------------------------------------------------- |
| `status`        | `proposed` \| `accepted` \| `rejected` \| `superseded` \| `deprecated`          |
| `superseded_by` | `null`, or the ADR id that replaced it — **required when `status: superseded`** |

ADRs have no `covers` / `last_verified`: they are historical records, not descriptions of
current code. They never go stale — they get superseded.

Conventions:

- Filename `ADR-NNNN-short-slug.md`, four digits, lowercase kebab-case slug, English
- Numbers are permanent: never reused, never renumbered, assigned even to rejected ADRs
- **Immutable once accepted.** Changing course means a new ADR plus `superseded_by` on the
  old one. Editing an accepted ADR destroys the record of what was actually believed at
  the time, which is the only reason the directory exists.

## Checks

Ordered by value. The first is the one that justifies the whole contract.

| #   | Check                                                                                 | Catches                                                                        | Severity               |
| --- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------------- |
| 1   | For each doc, any file matching `covers` with a commit newer than `last_verified`     | **Documentation silently behind the code** — automatic, no human review needed | warn                   |
| 2   | Every `covers` glob matches at least one existing path                                | Document describes deleted code                                                | error                  |
| 3   | Every top-level source directory is matched by some `covers`                          | Undocumented area of the codebase                                              | warn                   |
| 4   | `INDEX.md` byte-identical to a fresh render                                           | Orphaned or misdescribed document                                              | error                  |
| 5   | Every relative link resolves                                                          | Broken links                                                                   | error                  |
| 6   | Required frontmatter fields present and well-typed                                    | Documents that escape every other check                                        | error                  |
| 7   | Unfilled `<!-- PROJECT: … -->` placeholders in frontmatter **or body**                | Scaffolding never finished — invisible on GitHub                               | warn                   |
| 8   | `status: superseded` implies non-null `superseded_by`                                 | Dead-end supersession chains                                                   | error                  |
| 9   | ADR numbers unique; every ADR listed in `decisions/README.md`                         | Numbering collisions, orphaned ADRs                                            | error                  |
| 10  | `last_verified` older than the freshness budget                                       | Documents nobody has looked at in a year                                       | warn                   |
| 11  | `CHANGELOG.md` has a `## [Unreleased]` heading when the file exists                   | Changelog that cannot record what just shipped                                 | warn                   |
| 12  | Each ADR (not the template) has an *Alternatives considered* heading                  | Outcome recorded as if it were a decision                                      | warn                   |
| 13  | Root `DOCUMENTATION.md` when there is no `docs/` — frontmatter and `covers` staleness | Single-file shape with no checker                                              | warn/error as for tree |

Check 1 needs git, not just the filesystem:

```
git log -1 --format=%cI -- <covers globs>   # newest commit touching the covered code
```

compared against `last_verified`.

**Staleness warns, it never blocks.** A documentation gate that fails merges gets disabled
within a month, and then nothing is checked at all. Structural errors do fail — they are
always the author's to fix and take seconds. `--strict` promotes warnings to failures for
teams that want it.

Freshness budget: 180 days for `verified`, 365 for documents with `covers: []`.

Not automated, left to the agent's audit: whether a presumed-stale document is *actually*
wrong, and whether an accepted ADR was rewritten rather than superseded.

## Tooling

`docs_index.py` implements everything above, for all shapes: `docs/` (tree and flat) and
root `DOCUMENTATION.md` (single-file). Single-file has no index; `--write` still requires
`docs/`. Flat filenames map to the same index categories as the tree folders.

```bash
# regenerate the index from frontmatter
python3 "$SCRIPT" --project . --write

# run every check (exit 1 on errors, 0 on warnings)
python3 "$SCRIPT" --project . --check

# machine-readable: {ok, errors, warnings, documents, presumed_stale, summary}
python3 … --project . --check --json
```

`$SCRIPT` is `scripts/docs_index.py` in the `documentation-intent` skill when the agent
runs it. For CI or a git hook — anything running without the plugin — the
script is copied into the repository at `scripts/docs-index.py` and committed, so a fresh
clone and any runner have it with no agent tooling installed.

The script is stdlib-only Python (3.8+), so it runs in
a Go, Rust, or PHP repository just as well. A checker requiring Node in a Go repository
would not be adopted, which is the whole reason for that constraint.

CI template: `assets/ci/docs-check.yml`, shipped with
[documentation-intent](../../documentation-intent/SKILL.md). It needs
`fetch-depth: 0` — check 1 reads git history, and a shallow clone finds nothing while
appearing to pass.
