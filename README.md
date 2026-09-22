# ai-plugin-dev

Daily development conventions (git, docs, testing, code wording) for Claude Code
and Cursor. Public dual-host layout: one tree, no build step.

## Load the plugin

Point a host at **this directory** (the folder that holds `plugin.json`,
`skills/`, and `scripts/`).

```bash
# Claude Code — one session
claude --plugin-dir /path/to/ai-plugin-devtoolbox

# Cursor CLI — one session
agent --plugin-dir /path/to/ai-plugin-devtoolbox

# Cursor IDE — persistent local install (real copy, not a symlink outside the folder)
cp -R /path/to/ai-plugin-devtoolbox ~/.cursor/plugins/local/ai-plugin-dev
# then Developer: Reload Window
```

When this folder is the root of its own GitHub repository, Claude and Cursor
marketplaces can use `source: "./"` from `.claude-plugin/marketplace.json` and
`.cursor-plugin/marketplace.json`. While it still lives inside another checkout,
prefer `--plugin-dir` or the local copy above (or a marketplace `git-subdir`
with `path: "ai-plugin-devtoolbox"`).

## Use on a project

With the plugin loaded:

```
/adopt-conventions
```

Or without an agent, from this directory:

```bash
node scripts/install.mjs --project-dir /path/to/project -i
```

Same engine: `--propose`, `-i`, `--yes`, `--apply --answers`.

## Tests

```bash
python3 -m unittest discover -s tests -p '*_test.py'
node --test scripts/*.test.mjs
```

## Layout

| Path              | Role                          |
| ----------------- | ----------------------------- |
| `plugin.json`     | Agent Plugins 1.0 (skills)    |
| `.claude-plugin/` | Claude manifest + marketplace |
| `.cursor-plugin/` | Cursor manifest + marketplace |
| `skills/`         | Shared skills                 |
| `commands/`       | Slash commands (flat `.md`)   |
| `agents/`         | Subagents (flat `.md`)        |
| `scripts/`        | Install propose/apply CLI     |
