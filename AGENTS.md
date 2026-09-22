# AGENTS.md — ai-plugin-devtoolbox

Public Claude Code + Cursor plugin. This directory **is** the plugin root.

## Do

- Edit skills, commands, agents, and scripts here directly.
- Keep markdown links file-relative. Shell commands use paths from the plugin
  root (`node scripts/install.mjs`), never a leading `/` and never
  `${CLAUDE_PLUGIN_ROOT}` / `${CURSOR_PLUGIN_ROOT}`.
- Keep `plugin.json` schema-clean (Agent Plugins). Put Claude-only
  `extensions.bluewombat.install` only in `.claude-plugin/plugin.json`.
- Keep the catalog table in `skills/project-intent/SKILL.md` in sync when you
  add or remove a domain skill.

## Do not

- Add a `src/` wrapper or a Nola build.
- Point hosts at a sibling `nola-plugins/ai-plugin-dev` checkout for this tree.

## Verify

```bash
python3 -m unittest discover -s tests -p '*_test.py'
node --test scripts/*.test.mjs
```
