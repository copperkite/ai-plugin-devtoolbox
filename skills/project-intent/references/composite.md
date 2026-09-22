# Composite actions

Some requests are not about one domain. **"Ship this", "make this reviewable", "is anything
blocking this PR"** span every convention the project adopted, which is why they arrive here
and not at `git-intent`.

1. **Read the config.** No config, or no gate for the target state: nothing to coordinate —
   hand straight to [git-intent](../../git-intent/SKILL.md) and stop.
2. **Run each gated convention's own workflow skill, read-only.** For `documentation`, that
   is [documentation-intent](../../documentation-intent/SKILL.md) step 1 — read, report,
   change nothing. For `testing`, that is [testing-intent](../../testing-intent/SKILL.md)
   step 1 — the state script, change nothing.
3. **A blocking finding stops the plan and asks.** It does not veto: the user overrides in
   one word, and the override is reported, not argued with. A gate nobody can pass gets
   deleted within a month, and then nothing is checked at all.
4. **Then hand the git transition to `git-intent`**, naming the target state.

**Never repair what a gate found, mid-action.** The user is in the middle of shipping and did
not ask for their documentation to be rewritten. Report what is stale and let them decide
whether it belongs in this change.

Two gate keys exist today: **`pr-ready`**, checked before a pull request is marked ready for
review, and **`release-ready`**, checked before a version is cut. Add another when a real case
needs it.

**Gating the same convention on both is usually redundant.** Where every change reaches the
default branch through a gated pull request, the release commit — a version and a changelog
heading — is the least likely change in the project to have broken anything. A gate that never
fires gets overridden by reflex, and then neither gate is read.

A release is a composite with an extra leg — [release.md](./release.md).
