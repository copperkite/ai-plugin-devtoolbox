---
name: documentation-intent
description: >-
  Scaffold, fill, or correct agent-first documentation. Use when setting up docs
  or checking drift.
disable-model-invocation: true
metadata:
  domain: documentation
  role: workflow
---

# Documentation intent

One intent: **bring this project's documentation to a state that is true and complete.**

Read where the documentation actually stands, name that state, then converge on it.
Scaffolding an empty repository and correcting a drifted set are the same job from different
starting points, and they share every operation below.

**What "correct" means is not defined here** — structure, shapes, frontmatter, scope all live
in **[documentation-conventions](../documentation-conventions/SKILL.md)**. Open that skill
for the rules that apply to the files you are writing. Open
[references/frontmatter.md](../documentation-conventions/references/frontmatter.md) only when
the checker reports a frontmatter, index, or ADR-contract finding. Do not load the
references up front.

Applies to any code project — app, library, monorepo. No prerequisites.

## Step 1: Read the state

Never assume it, not even on a repository that looks obviously empty. Two reads, both every
time.

**The shape** — a project uses one, never both docs shapes with single-file:

| Found at the root                                                        | Shape                                                              |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `DOCUMENTATION.md`                                                       | `single-file`                                                      |
| `docs/` with `context/`, `architecture/`, `decisions/`, or `operations/` | `tree`                                                             |
| `docs/` with markdown only at the top level (no those folders)           | `flat`                                                             |
| neither                                                                  | undecided — operation B picks it                                   |
| **`DOCUMENTATION.md` and `docs/`**                                       | **stop.** Report it and ask; never merge or delete one on your own |

**Inventory** — which files of that shape exist, and which of them are placeholder-only.

**The checker** — all shapes. `tree` and `flat` read `docs/**`; `single-file` reads root
`DOCUMENTATION.md` (frontmatter, `covers` staleness, body placeholders). No index is
required in `single-file`. The deterministic findings no reader would catch:

The script is `scripts/docs_index.py` beside this SKILL.md; `--project` is the
repository being worked on (the session cwd):

```bash
python3 scripts/docs_index.py \
  --project . --check --json
```

It covers staleness (`last_verified` versus git history on `covers`), dead `covers` globs,
uncovered top-level directories, index drift, frontmatter validity, unfilled placeholders
(YAML and `<!-- PROJECT:` in the body), broken relative links, ADR numbering and index
consistency, `superseded` without `superseded_by`, missing *Alternatives considered*, a
missing `## [Unreleased]` heading, and the freshness budget.

On a repository with no documentation it reports almost everything missing. That is a valid
reading of the state, not a failure.

If the script cannot be located, check staleness by hand — compare `last_verified` against
`git log -1 --format=%cI -- <covers globs>`.

## Step 2: Name the state

| State     | Reads as                                                         | Converge with     |
| --------- | ---------------------------------------------------------------- | ----------------- |
| `absent`  | No `AGENTS.md`, no `docs/` — nothing to build on                 | A → B → C → D → F |
| `partial` | Structure started; files missing, or placeholders still unfilled | A → B → C → D → F |
| `drifted` | Structure complete; documents contradict or lag the code         | E → F             |
| `current` | Checker clean, spot checks hold                                  | F only, report    |

**A repository is often `partial` and `drifted` at once.** Run both, gaps first: a document
you are about to create cannot be stale, and judging content before the set is complete
wastes the expensive read.

## Step 3: Show the plan

Print it before writing anything:

```
documentation state
  now:    partial + drifted · 5 of 7 owed files · 4 unfilled placeholders
          · 2 presumed stale (OVERVIEW.md 94d, DEVELOPMENT.md 31d)
  target: current · shape tree
  steps:  1. intake — confirm project name and one-line goal
          2. create context/PRODUCT.md (owed; TESTING.md skipped — no test command yet)
          3. personalize and fill frontmatter on the new file
          4. read OVERVIEW.md and DEVELOPMENT.md against the code they cover
          5. regenerate docs/INDEX.md
```

Ask **once**, for the whole plan. Then run the operations in order, stopping at the first
one that cannot proceed without an answer.

---

## Operations

### A. Intake

Only what personalization actually needs.

1. **Auto-infer** from `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml`, the existing
   `README.md`, and the source layout: name, goal, stack, type, commands, prerequisites
2. **Ask only what cannot be inferred** — one line each, no elaboration:
   - "What is this project called?"
   - "One sentence: what does this project do?"
3. **Record the answers** in a scratch note and use them for every file

### B. Pick the shape

Shapes and owed files:
[documentation-conventions](../documentation-conventions/SKILL.md). Default is **`flat`**.

- `single-file` → `DOCUMENTATION.md` at the root
- `flat` → `docs/` with files at the top level (`ARCHITECTURE.md`, `DECISIONS.md`, …)
- `tree` → `docs/` with `context/`, `architecture/`, `decisions/`, `operations/`

Propose `single-file` for a script or spike; propose `flat` for a normal project that
wants separate documents; propose `tree` when numbered ADRs or several architecture
documents are likely.

Also read `.agent-adoptions.json` → `ai-plugin-dev.adopted.documentation.shape` when present
— if it is `single-file`, `flat`, or `tree`, that is the target unless the user asks to change it.
Any other value (or missing key) means documentation is not adopted: propose adoption,
do not invent a shape from a bad record.

On a `partial` repository, infer the shape already in use from what exists rather than
imposing the default — then propose the gap.

### C. Create missing files

Copy from this skill's `assets/`. **Only what is missing.** If `project-intent` install
already copied owed files, skip them. Never replace an existing file wholesale; when a
file exists but lacks structural sections, merge the missing sections in.

- `single-file` — `assets/DOCUMENTATION.md` to the repository root
- `flat` — owed files from `assets/flat/docs/` → `docs/`; `assets/flat/AGENTS.md`,
  `README.md`, and `CHANGELOG.md` when those root files are missing
- `tree` — owed files from `assets/docs/`, preserving layout; `assets/AGENTS.md`,
  `assets/README.md`, and `assets/CHANGELOG.md` when missing

Do not copy on-demand files (`TESTING.md`, `RUNBOOKS.md`, `DATA-MODEL.md`,
`THREAT-MODEL.md`, `TROUBLESHOOTING.md`) unless the trigger in the conventions reference
has fired.
### D. Personalize and fill the frontmatter

Replace every `<!-- PROJECT: ... -->` marker from the intake data: `name`, `goal`, `type`,
`stack`, `prerequisites`, `start-commands`, `setup-commands`, `today`, `doc-owner`,
`source-globs`, `tracker-link`, and the per-document `*-globs`. An unfilled one stays
unfilled and goes in the report.

Then fill the frontmatter per the contract in
[documentation-conventions](../documentation-conventions/SKILL.md) — one block per file under
`docs/` in `tree` and `flat`, a single block at the top of `DOCUMENTATION.md` in
`single-file`. Freshly scaffolded means `status: draft` and today's date.

### E. Judge the existing documents

**Presence is the cheap part. A doc set can be complete and entirely wrong** — a confidently
wrong `OVERVIEW.md` is worse than a missing one, because agents believe it. This operation
is where the value is; weight the effort accordingly.

1. **Are the presumed-stale documents actually wrong?** The checker lists them in
   `presumed_stale`. **Hand only those documents to the `doc-auditor` agent** — give each
   the path, the globs, and the `last_verified` date; it returns a verdict and the
   discrepancies, one document per delegation. They are independent, so they do not need to
   be done in sequence. Do not audit documents the checker did not flag, unless the user
   asked for a full audit.
   Then act on the verdicts: `current` ⇒ bump `last_verified`. `stale` or `wrong` ⇒ fix it,
   or mark `stale` and say so. Never bump a date on a document nobody read.
   If delegation is unavailable, do the same reading inline — it is the same work, in this
   skill's own context.
2. **Critical content** — `README.md` and `AGENTS.md` not placeholder-only. If they are, name
   what is missing and **ask**; do not invent.
3. **Separation of intent** — planning or troubleshooting content in `README.md`; structural
   rationale living only in code comments; missing `## [Unreleased]`; forward-looking plans
   that have crept into `docs/` instead of the issue tracker.
4. **Decision quality** — tree: *Alternatives considered* present; no accepted ADR rewritten
   in recent history except its `status` / `superseded_by`. Flat / single-file: each entry
   states why and alternatives; entries are not rewritten.
5. **AGENTS.md** — routes via `docs/INDEX.md` (or via headings in single-file) rather than
   listing every file, explains the `status` / `last_verified` convention, has both rituals.
6. **Optional Claude companion** — if root `CLAUDE.md` is missing and the team uses Claude
   Code, **ask** before adding `Read @./AGENTS.md and treat its contents as if they were in CLAUDE.md`.

Fix gaps and frontmatter directly. **Ask before rewriting content.** Never edit an accepted
ADR — supersede it.

### F. Regenerate the index and report

**`single-file` has no index** — the headings are the index. Skip straight to the report.

`tree` and `flat`:

```bash
python3 scripts/docs_index.py \
  --project . --write
```

Then verify the whole set:

```bash
python3 scripts/docs_index.py \
  --project . --check
```

The script is stdlib-only, so it runs in a repository of any language with nothing but
Python 3. See [scripts/docs_index.py](scripts/docs_index.py).

**Report, in this order:**

1. **Presumed-stale documents first**, with day counts — the finding that matters and the
   one no human would have caught
2. Structural findings
3. Created / merged / skipped (already present) / left unfilled, and why
4. The next useful step — usually `ARCHITECTURE.md` (flat) or `architecture/OVERVIEW.md`
   (tree) Areas and Entry points, since it unblocks every later session

Do not commit unless the user asks.

---

## Offer the CI check

Once the set is `current`, offer to keep it that way. **Ask before writing** — this adds
files to the user's repository.

CI runs without this plugin, so it needs its own copy of the checker. Propose **two** files
together; one is useless without the other:

1. [scripts/docs_index.py](scripts/docs_index.py) → the repository's `scripts/docs-index.py`
2. [assets/ci/docs-check.yml](assets/ci/docs-check.yml) → `.github/workflows/docs-check.yml`

The workflow needs `fetch-depth: 0`: staleness compares `last_verified` against git history,
and a shallow clone reports nothing while appearing to pass.

Not on GitHub Actions, or CI declined? Offer the same command as a pre-commit hook or a
`make docs-check` target. The mechanism matters, the runner does not.

## Constraints

- **Idempotent** — safe to re-run; minimal diff every time
- **No migration** — this scaffolds one structure. If the repository already uses a different
  documentation structure, report the difference and **ask** — do not move files. That
  includes moving between shapes: a `single-file` or `flat` project that has outgrown the
  shape is told so, not converted
- **Never modify** `.cursor/rules/`, existing `CLAUDE.md` content, application code, or
  existing custom doc content beyond merging missing structural sections
- Everything else that governs *what* gets written is in
  [documentation-conventions](../documentation-conventions/SKILL.md), and applies here too

## Sample prompts

```
Set up agent-first documentation on this repo.
```

```
Where does the documentation stand? What is stale relative to the code?
```

```
Bring the docs back up to date — we shipped a lot last month.
```

```
Fill the gaps in our docs, flat shape, we track work in Linear.
```
