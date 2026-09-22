# Install

This plugin's **install** (adopt conventions, scaffold owed docs). Usage after
that is check / audit / domain skills.

It records the `ai-plugin-dev` slice of `.agent-adoptions.json` and scaffolds owed
docs. The script is the source of truth. Do not copy `assets/` by hand. Do not
call another plugin.

```
node scripts/install.mjs --project-dir . --propose --json
```

If `named` is `foreign`, stop. If `named` is `ready` and `questions` is empty,
`--apply --answers '{}'` still scaffolds any owed files that are missing.

`plan.files[]` is what apply would write with the defaults (`created`,
`regenerated`, `kept-foreign`). Show it before asking. A `docs/INDEX.md` the
plugin did not generate is never replaced: apply reports `kept-foreign` and
leaves it; `docs_index.py --write --force` is a human's call.

Ask **once** from `questions[]`. Then:

```
node scripts/install.mjs --project-dir . --apply --answers '{…}' --json
```

CLI: `-i` or `--yes`. Run from the **plugin root** (the folder that holds
`scripts/` and `skills/`).

Never adopt a domain they did not pick. Never write a `gates` key. Leave
`<!-- PROJECT: -->` markers that cannot be inferred. Skip files that already
exist. Do not run documentation operation E (judging content against code).

`$ARGUMENTS`, when present, may name a convention to focus on — still pass it
only if it appears in `questions[]`.
