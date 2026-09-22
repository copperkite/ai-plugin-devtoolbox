---
title: Testing
summary: What is tested at which level, what must pass before merge, and what is deliberately untested.
status: draft
last_verified: <!-- PROJECT: today -->
covers:
  - <!-- PROJECT: test-globs — e.g. "tests/**", "**/*.test.ts" -->
---

# Testing

## Levels

| Level | Covers | Location | Runtime | Run with |
| ----- | ------ | -------- | ------- | -------- |
| Unit | <!-- pure logic --> | <!-- glob --> | <!-- seconds --> | `<!-- -->` |
| Integration | <!-- with real database/services --> | <!-- glob --> | <!-- --> | `<!-- -->` |
| End-to-end | <!-- user journeys --> | <!-- glob --> | <!-- --> | `<!-- -->` |

## What must pass before merge

```bash
<!-- PROJECT: pre-merge-commands — the exact gate, same as CI -->
```

If this differs from what CI runs, CI wins and this document is wrong — fix it here.

## Writing tests

- Naming: <!-- convention -->
- Fixtures and factories: <!-- where they live, how to add one -->
- What gets mocked: <!-- policy — mocking everything tests nothing -->
- Determinism: <!-- how time, randomness, and network are controlled -->

## Deliberately not tested

Being explicit here prevents both false confidence and pointless coverage debates.

| Area | Why not | Compensating control |
| ---- | ------- | -------------------- |
| <!-- --> | <!-- --> | <!-- manual check, monitoring, type system --> |

## Flaky tests

- Policy: <!-- quarantine? fix within N days? --> 
- Currently quarantined: <!-- list with issue links, or "none" -->

An undocumented flaky test trains the team to ignore red builds.
