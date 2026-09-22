---
description: Move the current work through its pull request — draft, ready for review, or merged — checking the gates this project declared.
---

Open [../skills/project-intent/references/composite.md](../skills/project-intent/references/composite.md)
of the `project-intent` skill and follow it.

`$ARGUMENTS` names the target: `draft`, `ready`, or `merge`. Empty: read the current state and
propose the next step.

Do not perform the git transition directly. Read `.agent-adoptions.json` (`ai-plugin-dev`), run the gated
conventions read-only, report what they found, then hand the transition to `git-intent`.
