---
description: "Cut a release: check the gates this project declared, prepare the version and the changelog, take it to main, and tag."
---

Open [../skills/project-intent/references/release.md](../skills/project-intent/references/release.md)
of the `project-intent` skill and follow it.

`$ARGUMENTS`, when present, names either the version to cut (`1.4.0`) or the level (`major`,
`minor`, `patch`). Empty: read the state and propose the version the commits imply.

Do not bump the version, write the changelog, or tag directly. Read `.agent-adoptions.json`
(`ai-plugin-dev`), run the conventions gated on `release-ready` read-only, report what they
found, then hand the release itself to `release-intent` and the branch and pull request to
`git-intent`.
