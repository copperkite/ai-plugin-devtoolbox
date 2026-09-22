---
name: code-wording
description: >-
  English naming, comments, and error wording. Use when writing or naming code.
  Not for formatting, lint, or architecture.
metadata:
  domain: code-wording
  role: norm
  scope: universal
---

# Code wording

How text reads in a codebase — the identifiers, the comments, the messages, the docs.
Applies to code the agent writes *and* to prose the agent produces about it.

**This is a universal convention.** Unlike a norm tied to one domain, it applies to every
piece of text produced anywhere, and any other skill may point at it.

## Precedence

An existing codebase wins. Before applying anything here, look at how the surrounding code
already names things and comments. Match it, and mention the divergence once rather than
converting the file.

## English, everywhere

Code, identifiers, comments, documentation, commit messages, PR bodies, error messages,
log lines. US spelling.

The single exception: **text an end user reads**. That never lives in the source — it goes
through i18n, keyed in English. A user-facing string hardcoded in a component is a bug,
whatever language it is in.

## Comments

- A comment explains **why**. The code already says what.
- Delete any comment that paraphrases the line under it.
- One line when one line does it. Multi-line only for genuine reasoning.
- No ASCII banners, no `// ---- section ----` separators. Structure comes from the code.
- No history: no `// old version`, no `// changed 2024-03`, no commented-out code. That is
  what git is for.
- `TODO` has a scope and a subject: `// TODO(auth): refresh token before expiry`.
  A bare `// TODO` is not a TODO, it is litter.

```js
// bad — restates the code
// increment the counter
counter += 1;

// good — states what the code cannot
// The API rejects bursts above 10/s, so we pace even on retries.
await sleep(RETRY_INTERVAL_MS);
```

## Naming

| Kind          | Rule                                    | Example                     |
| ------------- | --------------------------------------- | --------------------------- |
| Boolean       | `is` / `has` / `should` / `can` prefix  | `isPublished`, `canRetry`   |
| Function      | Verb first                              | `parseInvoice`, `fetchUser` |
| Collection    | Plural                                  | `invoices`, `activeUsers`   |
| Constant      | `SCREAMING_SNAKE_CASE`                  | `MAX_RETRY_COUNT`           |
| Event handler | `handleX` implements, `onX` is received | `onSubmit={handleSubmit}`   |

**No abbreviations** outside this list: `id`, `url`, `uri`, `api`, `db`, `env`, `config`,
`ref`, `src`, `idx`, `ms`. Everything else is spelled out — `usr`, `cfgMgr`, `tmpVal` are
not names.

## File names

`kebab-case` by default: `invoice-parser.ts`, `use-auth.ts`.

**Exception — React components.** Some projects here name component files `PascalCase.tsx`,
matching the component they export. Both are correct; what is not correct is mixing them in
one project. Look at the existing files and follow them.

## Error messages

A complete sentence. It says what failed, in what context, and what to do about it.

```
bad:   Error occurred
bad:   Invalid input
good:  Cannot parse invoice 4821: the "total" field is missing. Check the export format.
```

## Logs

- Structured, with an explicit level.
- Never a secret, a token, a password, or personal data — not even at debug level.
- The message is a constant; the variable part goes in the fields, not in the string.

## One concept, one word

Pick a word per domain concept and never drift. `user` / `account` / `member` describing the
same thing across three files is a bug in the codebase's vocabulary.

The glossary lives in `docs/context/PRODUCT.md` — see
[documentation-conventions](../documentation-conventions/SKILL.md). When introducing a term
that is not there, add it.

That skill and this one split cleanly: it owns **which documents exist and what they must
contain**, this one owns **how their text reads**. Both apply to every document.

## No emoji

Not in code, not in logs, not in comments, not in commit messages, not in PR bodies.

## This applies to what the agent writes about the code too

PR titles and bodies, changelog entries, documentation, ADRs. Same English, same
vocabulary, same absence of emoji.

## Reviewing

When checking existing code against this guide, report the concrete rewrite, not the rule:

```
src/api/client.ts:42  `usrCfg` → `userConfig`
src/api/client.ts:57  comment restates the code — delete
src/api/client.ts:88  "Error occurred" → say which request failed and why
```
