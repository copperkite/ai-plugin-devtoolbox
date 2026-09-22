---
title: <!-- Short imperative title — the decision, not the problem -->
summary: <!-- One line a reader can act on without opening the file -->
status: proposed
date: <!-- YYYY-MM-DD -->
deciders: <!-- who agreed -->
superseded_by: null
---

# ADR-NNNN — <!-- Title -->

## Context

What forced a decision. Constraints, deadlines, existing commitments, what breaks if
nothing changes. Write it so someone in two years understands the pressure — without it,
the decision reads as arbitrary.

## Decision

What was decided, in one or two sentences, in the active voice.

<!-- e.g. "We use PostgreSQL as the single primary datastore." -->

## Alternatives considered

The section that stops the same debate from restarting. One block per option that was
genuinely on the table.

### <!-- Option A -->

- **What it would have meant**: <!-- -->
- **Why not**: <!-- the specific disqualifier, not "it was worse" -->

### <!-- Option B -->

- **What it would have meant**: <!-- -->
- **Why not**: <!-- -->

## Consequences

Both directions — this is not a justification section.

**We accept**

- <!-- cost, lock-in, extra work this creates -->

**We gain**

- <!-- what becomes possible or cheaper -->

**We must now**

- <!-- follow-up work this decision obliges: migrations, docs, lint rules -->

## Revisit if

The condition that would make this decision wrong. If it has no such condition, say so —
but most decisions have one, and naming it is what makes supersession honest later.

- <!-- e.g. "Write throughput exceeds 5k/s sustained" -->
