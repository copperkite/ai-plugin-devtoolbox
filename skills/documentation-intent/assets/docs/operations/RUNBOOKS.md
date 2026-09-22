---
title: Runbooks
summary: Deployment, rollback, and incident procedures — step by step, no prior context needed.
status: draft
last_verified: <!-- PROJECT: today -->
covers:
  - <!-- PROJECT: ci-globs — e.g. ".github/workflows/**", "infra/**" -->
---

# Runbooks

Written for someone tired, alone, and under pressure. Exact commands, no "simply", no
assumed context. Every runbook states how to know it worked and how to undo it.

## Environments

| Environment | URL | Deployed from | Who can deploy |
| ----------- | --- | ------------- | -------------- |
| <!-- staging --> | <!-- --> | <!-- branch --> | <!-- --> |
| <!-- production --> | <!-- --> | <!-- tag/branch --> | <!-- --> |

## Deploy

1. **Preconditions** — <!-- green CI, changelog updated, migrations reviewed -->
2. **Steps**
   ```bash
   <!-- exact commands -->
   ```
3. **Verify** — <!-- health endpoint, dashboard, the one metric that proves it works -->
4. **If it failed** — go to *Rollback* below. Do not attempt a fix-forward under pressure
   unless a rollback is impossible; say here which one applies.

## Rollback

1. **Steps**
   ```bash
   <!-- exact commands -->
   ```
2. **Verify** — <!-- -->
3. **Database migrations**: <!-- are they reversible? if not, say so loudly and explain
   what a rollback does NOT undo — this is where rollbacks go wrong -->

## Incident response

1. **Assess** — <!-- what is broken, for whom, since when -->
2. **Communicate** — <!-- channel, who to notify, status page -->
3. **Stabilise** — rollback, feature flag, scale, or degrade. Which levers exist:
   | Lever | How | Effect |
   | ----- | --- | ------ |
   | <!-- --> | <!-- --> | <!-- --> |
4. **Record** — write the timeline while it is fresh; a decision made during the incident
   that outlives it becomes an ADR.

## Rotate a leaked secret

1. Revoke the old credential **first** — rewriting git history does not un-leak it.
2. Issue a replacement: <!-- where -->
3. Update: <!-- secret store, CI, running services -->
4. Verify the old credential is dead: <!-- how -->
5. Assess exposure: <!-- what could have been reached with it -->

## Restore from backup

- Backups run: <!-- schedule, retention, location -->
- **Last successful restore test**: <!-- date — an untested backup is not a backup -->
- Steps:
  ```bash
  <!-- -->
  ```

## On call

- Rotation: <!-- where it is published -->
- Escalation: <!-- who, after how long -->
