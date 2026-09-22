---
title: Decision index
summary: Every architectural decision record, its status, and what superseded it.
status: verified
last_verified: <!-- PROJECT: today -->
covers:
  - "docs/decisions/**"
---

# Decisions

Architectural Decision Records. One decision per file, immutable once accepted.

**Read this index before any structural change.** Open only the ADRs that touch your area.

## Index

Newest first.

| ID | Title | Status | Date | Superseded by |
| -- | ----- | ------ | ---- | ------------- |
| [ADR-0001](./ADR-0001-example.md) | <!-- title --> | proposed | <!-- YYYY-MM-DD --> | — |

## Statuses

| Status | Meaning |
| ------ | ------- |
| `proposed` | Written, under discussion, not binding yet |
| `accepted` | In force — code must comply |
| `rejected` | Considered and turned down; kept so it is not re-proposed blindly |
| `superseded` | Replaced by a later ADR, named in `superseded_by` |
| `deprecated` | No longer applies, and nothing replaced it (the need disappeared) |

## Rules

1. **Immutable once accepted.** Never rewrite the Context, Decision, or Alternatives of
   an accepted ADR. To change course, write a new ADR and set the old one to
   `superseded` with `superseded_by`. The wrong turns are the value of this directory.
2. **One decision per file.** If the title needs "and", it is two ADRs.
3. **Numbering is permanent.** `ADR-0004` always means the same thing, even if rejected.
   Never reuse a number, never renumber.
4. **Record the alternatives.** An ADR without rejected options does not prevent the
   decision from being re-litigated in six months — which is the whole point.
5. **Write it when the decision is made**, not at release time. A retroactive ADR is a
   rationalisation.

## Writing a new one

Copy [ADR-TEMPLATE.md](./ADR-TEMPLATE.md) to `ADR-<next-number>-<short-slug>.md`,
fill it in, and add a row to the index above.

Filenames: four-digit number, lowercase kebab-case slug, English —
`ADR-0007-postgres-over-mysql.md`.

## What deserves an ADR

- Choosing between technologies, libraries, or hosting
- Changing a boundary, a contract, or the shape of the data
- Adopting or dropping a convention the whole team must follow
- Accepting a known risk or a piece of technical debt on purpose
- Renaming a domain term

Not an ADR: implementation details reversible in an afternoon, personal style preferences,
or anything an existing team convention already settles.
