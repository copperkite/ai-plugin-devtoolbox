---
title: Development
summary: Run, debug, and change this project locally — setup, environment, common tasks.
status: draft
last_verified: <!-- PROJECT: today -->
covers:
  - <!-- PROJECT: config-globs — e.g. "package.json", "docker-compose.yml", ".env.example" -->
---

# Development

Daily working guide: how to get this project running locally, and how to make the changes
it asks for most often.

## Setup

**Prerequisites**: <!-- PROJECT: prerequisites — exact versions, not "recent Node" -->

```bash
<!-- PROJECT: setup-commands — clone to running, copy-pasteable, in order -->
```

Expected result: <!-- what you should see when it worked, e.g. "server on http://localhost:3000" -->

## Environment

| Variable | Required | Default | What it does | Where to get it |
| -------- | -------- | ------- | ------------ | --------------- |
| <!-- NAME --> | yes/no | <!-- --> | <!-- --> | <!-- secret manager, teammate, self-signup --> |

Keep this table in sync with `.env.example`. A variable in code but absent from both
is the most common cause of a broken first day.

## Everyday commands

| Task | Command |
| ---- | ------- |
| Start the app | `<!-- -->` |
| Run tests | `<!-- -->` |
| Lint and format | `<!-- -->` |
| Type check | `<!-- -->` |
| Reset local data | `<!-- -->` |
| Load sample data | `<!-- -->` |

## Common changes

Recipes for the tasks this project actually asks of people. Add a row every time someone
has to ask how — that question is the signal.

| To… | Do |
| --- | -- |
| Add a database migration | <!-- exact command, where the file lands, how to apply and roll back --> |
| Add a dependency | <!-- lockfile policy, approval needed? --> |
| Regenerate generated code | <!-- --> |
| Run against a real external service | <!-- credentials, safety rules --> |

## Debugging

| Symptom | Look at |
| ------- | ------- |
| <!-- --> | <!-- logs location, debug flag, dashboard --> |

- Log level: <!-- how to raise it -->
- Attaching a debugger: <!-- -->

## Known traps

Things that have cost someone an afternoon. Cheapest documentation in the repository.

| Trap | Sign | Fix |
| ---- | ---- | --- |
| <!-- e.g. Stale generated client after a schema change --> | <!-- type errors in unrelated files --> | <!-- regenerate --> |
