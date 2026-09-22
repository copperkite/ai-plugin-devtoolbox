# AGENTS.md

## Project context

**ai-plugin-dev** is an agent plugin (Claude Code + Cursor) for daily development
conventions: git, documentation, testing, release, and code wording.

Stack: markdown skills/commands/agents, Node scripts under `scripts/` (install
propose/apply), Python helpers under some skills. This directory **is** the
plugin root — no build step.

## Documentation map

There is no `docs/INDEX.md` yet. Start with:

| Need | Where |
| --- | --- |
| What this plugin is and how to load it | [README.md](./README.md) |
| What changed | [CHANGELOG.md](./CHANGELOG.md) |
| Domain norms and workflows | `skills/*/SKILL.md` (and their `references/`) |
| Doc templates the install scaffolds into projects | `skills/documentation-intent/assets/` |

## Frontmatter on shipped assets

Some markdown under `skills/documentation-intent/assets/` uses `status` and
`last_verified` (and optional `covers`). When you edit those files:

- Treat `status: verified` as a claim against the code or layout it describes
- If the covered paths changed since `last_verified`, presume stale and re-verify
  or downgrade the status — do not leave a confident wrong date

Plugin skill/command bodies themselves are not required to carry that frontmatter.

## Before coding

1. Confirm the change belongs in this plugin (portable conventions), not in a
   consumer project’s `.claude/` / `.cursor/` vendor copy.
2. Read the skill or script you will touch.
3. Run nothing destructive on a real project without `--project-dir` pointed at a
   throwaway folder.

## After coding

```bash
python3 -m unittest discover -s tests -p '*_test.py'
node --test scripts/*.test.mjs
```

Both must pass before the change is finished.

## Working agreements

- Markdown links are file-relative. Shell commands use paths from the plugin root
  (`node scripts/install.mjs`), never a leading `/`, never
  `${CLAUDE_PLUGIN_ROOT}` / `${CURSOR_PLUGIN_ROOT}`.
- **`extensions` (including `bluewombat.install`) lives only on the root
  `plugin.json`** (Agent Plugins 1.0). Do not put them on
  `.cursor-plugin/plugin.json` or `.claude-plugin/plugin.json`.
- Keep the catalog table in `skills/project-intent/SKILL.md` in sync when you
  add or remove a domain skill.
- Do not add a `src/` wrapper or a Nola build.
- Do not author a second agent guide (`CLAUDE.md` duplicate). This file is the
  agent entry point.
