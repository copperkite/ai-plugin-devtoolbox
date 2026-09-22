# Changelog

## [Unreleased]

- Put `extensions.bluewombat.install` on the root Agent Plugins `plugin.json`
  (single source of truth); remove the duplicate from `.claude-plugin/plugin.json`.

## 0.1.0

- Public dual-host layout: Claude and Cursor load this directory as-is (no Nola
  build). Catalog table baked into `project-intent`. Plugin-root `/` paths
  replaced with relative links and `scripts/` commands.
