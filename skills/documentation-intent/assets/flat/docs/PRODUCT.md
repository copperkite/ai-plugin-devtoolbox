---
title: Product and domain
summary: What this product does, who uses it, and what the domain words mean.
status: draft
last_verified: <!-- PROJECT: today -->
covers: []
---

# Product and domain

> Scope: what the code cannot tell you. Roles, rules, and vocabulary.
> Detailed feature specifications live in the tracker — link them, do not copy them here.

## What it does

<!-- PROJECT: goal — one paragraph. What problem, for whom, replacing what. -->

## Who uses it

| Role                | Needs                       | Can do              | Cannot do         |
| ------------------- | --------------------------- | ------------------- | ----------------- |
| <!-- e.g. Admin --> | <!-- what they came for --> | <!-- capability --> | <!-- boundary --> |

Keep this table aligned with the permission model in `./THREAT-MODEL.md`
when that document exists.

## Domain rules

Business invariants that must hold regardless of implementation. Each one should be
falsifiable — if code violates it, that is a bug, not a design choice.

- <!-- e.g. An order can never leave `draft` without at least one line item -->
- <!-- e.g. A user belongs to exactly one organisation for their whole lifetime -->

## Glossary

The words used in code, database columns, UI, and conversation. One row per concept.
If two words mean the same thing, pick one and mark the other as an alias to retire.

| Term          | Means               | Does **not** mean         | Where it lives in code     |
| ------------- | ------------------- | ------------------------- | -------------------------- |
| <!-- Term --> | <!-- definition --> | <!-- common confusion --> | <!-- glob or type name --> |

Rules:

- A term used in code but absent here is a documentation gap.
- A term here with no code location is either dead or not built yet — say which.
- Renaming a domain term is a decision: record it in [DECISIONS.md](./DECISIONS.md) before
  the rename, not after.

## Out of scope

What this product deliberately does not do, so the question stops coming back.

- <!-- e.g. No offline mode — the client assumes connectivity -->

## Detailed specifications

<!-- PROJECT: tracker-link — link to the issue tracker, product board, or spec space.
     Do not mirror specification content here; it will drift within weeks. -->
