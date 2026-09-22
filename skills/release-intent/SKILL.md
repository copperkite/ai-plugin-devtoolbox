---
name: release-intent
description: >-
  Cut a release — version, changelog, tag. Use when asked to release or bump a
  version. Not for pull requests or publishing.
disable-model-invocation: true
metadata:
  domain: release
  role: workflow
---

# Release intent

One intent: **cut a release of this project.**

Read what has shipped since the last tag, name the version that follows from it, and take the
project to that version.

**What the number means is not decided here** — semver, tag format, the CHANGELOG transition
all live in [release-conventions](../release-conventions/SKILL.md). Read it first.

**This skill stops at the repository.** It does not open a pull request, does not merge, and
does not publish. Moving a commit onto the default branch is a git transition and belongs to
the git workflow; publishing belongs to the project's CI.

## Step 1: Read the state

Always — even when the user names the version themselves. One command. The script is
`scripts/release_state.py` beside this SKILL.md; `--project` is the repository being
worked on (the session cwd):

```bash
python3 scripts/release_state.py \
  --project . --json
```

Act on the JSON. It names `lastTag`, `commitsSinceTag` (subjects as committed), `dirty`,
whether `## [Unreleased]` is present and empty, and `versionOfRecord` when
`.agent-adoptions.json` → `ai-plugin-dev.adopted.release` named a `version-file`. It does **not** choose the next version.

Then read [release-conventions](../release-conventions/SKILL.md) for what the number means.
When `versionOfRecord` is `null`, locate the file from that norm. Read the Unreleased
entries themselves — the script counts them; the wording is still yours to judge.

## Step 2: Name the state

Report it before proposing anything. Each of these changes what happens next:

| Found                                                | What it means                                                                                                 |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| No tag at all                                        | First release. Propose `0.1.0`, never `1.0.0`                                                                 |
| Last tag equals the version of record, nothing since | Already released. Say so and stop                                                                             |
| Working tree dirty                                   | **Stop.** A release must describe committed history, not a desk mid-edit                                      |
| `[Unreleased]` empty, but commits since the tag      | The changelog was not kept up. Report it and stop — writing it now is a separate decision                     |
| Version of record ahead of the last tag              | A bump was committed and never tagged. Finish it **by tagging**; never re-bump a version that already shipped |
| Not on the default branch                            | Report where the work is. Only the tag needs the default branch                                               |
| Tags exist but do not look like `v<semver>`          | The project has its own scheme. Follow it — see Precedence in the norm                                        |

## Step 3: Propose the version

Derive it from the commits, then **show the derivation, not just the number**:

```
Last tag: v0.3.1 (2026-07-02)
14 commits since:
  1 × feat!    plugin renamed — consumers must update their config key
  3 × feat
  6 × fix
  4 × chore, docs

Breaking change present, and the project is below 1.0.0 → 0.4.0

CHANGELOG [Unreleased] holds 5 entries, under Changed and Fixed.

Proceed?
```

**Never bump without showing why.** A version number nobody can trace back to a commit is a
number nobody trusts.

The user may name a different version. Record their choice and act on it — say once if it
disagrees with the derivation, then drop it.

## Step 4: Converge

In order. Stop at the first step whose precondition does not hold.

1. **Version of record** → the new version. That one file, nothing else
2. **`CHANGELOG.md`** → `[Unreleased]` becomes the dated heading, and a fresh empty
   `[Unreleased]` goes back on top
3. **Commit** → `chore(release): v0.4.0`, those two files only. Nothing else rides along
4. **Tag** → annotated, on the release commit — **only once that commit is on the default
   branch.** When it is not, stop here and say exactly what remains: the release commit has to
   reach the default branch first, and the tag is the last step after it does

**Steps 1 to 3 without step 4 is not a release**, it is a changelog that announces one. Until
the tag exists, say so in those words every time the state is reported — a dated version with
nothing pinned to it is worse than an undated one, because it reads as shipped.

Then report what a consumer would now see: the version, the tag, and where each lives.

## What this never does

- **Never publishes.** No `npm publish`, no push to a registry, no release upload. Irreversible
  and credentialed — it is the project's CI or a human, never this skill
- **Never writes a changelog entry from a commit subject.** An entry describes user-visible
  change; a commit subject describes an edit. They are not the same sentence
- **Never edits a version a tool owns** — a lockfile, a generated manifest, a scaffolder's
  stamp. Update the version of record and let each tool regenerate its own
- **Never moves or deletes an existing tag**, and never releases from a dirty tree
- **Never invents a release date.** It is the day the tag is made

## Sample prompts

```
Release this.
```

```
What would the next version be?
```

```
Cut 1.0.0.
```

```
We tagged 0.3.1 but the version file still says 0.3.0.
```
