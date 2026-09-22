# Release

`/release` is the same shape as a composite action, with one more leg: the release has
content of its own to prepare before anything git happens.

1. **Read the config.** No `release` under `ai-plugin-dev.adopted`: say the project has not adopted a
   release convention, offer to adopt it, and stop. Never cut a version off the record.
   Adopting is its own change — it never travels inside the release commit
2. **Run the `release-ready` gates read-only.** Same rule as [composite.md](./composite.md) —
   a finding reports and asks, it does not veto
3. **Hand the version and the changelog to [release-intent](../../release-intent/SKILL.md)**,
   through its step 4, up to and including the release commit. It stops before the tag when
   that commit is not yet on the default branch
4. **Hand the branch and the pull request to [git-intent](../../git-intent/SKILL.md)**, naming
   the release commit as what has to reach the default branch
5. **Once it is there, hand back to `release-intent` for the tag.** The tag is the last thing
   that happens, on the default branch, never before the merge

Steps 3 and 5 are the same skill twice on purpose: the git transition sits between the release
commit and the tag, and neither domain may reach across it.
