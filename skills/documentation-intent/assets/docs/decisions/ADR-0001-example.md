---
title: Keep a versioned documentation set in the repository
summary: Documentation lives in docs/ next to the code, indexed for agent and human navigation.
status: proposed
date: <!-- PROJECT: today -->
deciders: <!-- PROJECT: doc-owner -->
superseded_by: null
---

# ADR-0001 — Keep a versioned documentation set in the repository

> **Delete this file once the project records its first real decision.**
> It exists to show the shape of an ADR, and to make the index non-empty.
> Renumber nothing when you delete it — start the first real ADR at 0002.

## Context

Knowledge about this project was going to live in conversation threads, tickets, and
people's heads. Both humans joining the project and AI agents starting a session need the
same context, and neither can get it from a chat history they were not part of.

## Decision

Keep documentation in `docs/`, versioned with the code, split by intention
(context, architecture, decisions, operations), with `docs/INDEX.md` as the routing table
and `AGENTS.md` as the agent entry point.

## Alternatives considered

### A wiki or shared document space

- **What it would have meant**: Documentation edited outside the repository.
- **Why not**: It cannot be reviewed in a pull request alongside the change it describes,
  so it drifts silently and no reviewer ever notices.

### No structured documentation, rely on code and tests

- **What it would have meant**: The code is the documentation.
- **Why not**: Code records what the system does, never what was rejected or why. That
  loss is permanent and is exactly what gets re-litigated.

## Consequences

**We accept**

- Changing behaviour now means changing a document in the same pull request.
- The doc set needs periodic verification or it becomes confidently wrong.

**We gain**

- A newcomer or agent can reach the relevant context in two file reads.
- Decisions and their rejected alternatives survive team turnover.

**We must now**

- Keep `docs/INDEX.md` in sync when documents are added or moved.
- Update `last_verified` when a document is checked against the code.

## Revisit if

- The team moves to a documentation system that supports review alongside code changes.
