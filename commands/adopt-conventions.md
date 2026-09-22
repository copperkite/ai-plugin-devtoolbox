---
description: Propose conventions this project can adopt, record the choice, and scaffold what is missing.
---

Open [../skills/project-intent/references/install.md](../skills/project-intent/references/install.md)
and follow it.

Run `node scripts/install.mjs --project-dir . --propose --json`,
ask once from `questions[]`, then `--apply --answers`.
Never adopt anything the user did not pick.

`$ARGUMENTS`, when present, names a convention to focus on.
