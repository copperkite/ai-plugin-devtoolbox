# Check

Fast, mechanical, safe to run in a loop. **Deterministic findings only** — nothing here
requires reading a document and forming an opinion.

1. **The record against reality** — is every adopted convention actually in place; does the
   repository contradict its own record (a `release-branch` model with no `release/*` branch
   and a live `develop` is worth surfacing)
2. **Each adopted convention's own deterministic pass** — for `documentation`, that is
   [documentation-intent](../../documentation-intent/SKILL.md) step 1: the checker, which
   covers dead links, invalid frontmatter, index drift and presumed-stale documents. For
   `git`, `git_state.py --mode state` from [git-intent](../../git-intent/SKILL.md) (and
   `--mode audit` when the request is hygiene, not a transition). For `release`,
   `release_state.py` from [release-intent](../../release-intent/SKILL.md): whether the
   version of record and the newest dated version in the `CHANGELOG` each have a matching
   tag — a version announced with no tag behind it is a release that never finished. For
   `testing`, `testing_state.py` from [testing-intent](../../testing-intent/SKILL.md):
   whether a runner was found, and which changed source files have no paired test. The
   suite itself is not run here — that is the workflow's converge step, not a loop-safe
   check
3. **Report, and fix only the trivial and unambiguous** — a regenerated index, a broken
   relative link with one obvious target. Anything requiring a judgement call is named and
   left alone

Report `presumed stale` counts, never verdicts: deciding whether a stale document is actually
wrong is the audit's job, and it is expensive.
