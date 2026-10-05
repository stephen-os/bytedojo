# ByteDojo CLI Reference

Every command available under `dojo`. Each page has the same shape:
**Synopsis → Description → Arguments → Options → Examples → See also**.

## Quick reference

| Command | One-liner |
| --- | --- |
| [`init`](init.md) | Create a `.dojo/` repository in the current (or chosen) directory |
| [`fetch`](fetch.md) | Place bundled problems on disk with a synthesised starter stub |
| [`run`](run.md) | Execute a solution's `__main__` and capture its output |
| [`test`](test.md) | Run the bundled test cases; record the outcome and drive the review schedule |
| [`grade`](grade.md) | Manually apply pass/fail/skip to a problem |
| [`pick`](pick.md) | Pick a random problem matching difficulty / tag filters |
| [`query`](query.md) | Browse / filter the bundled problem catalog |
| [`review`](review.md) | Spaced-repetition review system (group with subcommands) |
| [`stats`](stats.md) | Repository statistics and per-problem attempt detail |
| [`settings`](settings.md) | View and modify dojo settings (group with subcommands) |
| [`support`](support.md) | Environment + toolchain diagnostic report |

## Common patterns

**Selectors.** `run`, `test`, `grade` and the `review` subcommands accept
the same selectors to identify which registered problem to act on:

- Positional `IDENTIFIER` — a numeric problem ID
- `--name TEXT` / `-n TEXT` — fuzzy match against the problem title
- `--desc TEXT` / `-d TEXT` — keyword search in the description
- `--last` — the most recently fetched problem

If the lookup is ambiguous the CLI prompts; pass `--name`/`--desc` with
something specific enough to disambiguate.

**Language flag.** `--python` (`-py`) states a language *preference*.
Language is attempt metadata, not identity: a problem's attempts share one
version history regardless of language, and commands act on the resolved
attempt. If you pass a language flag and the latest attempt is in a
different language, the CLI warns instead of silently picking another file.

**Repository discovery.** Every command (except `init` and `support`)
walks up from the current directory looking for `.dojo/`. Not finding one
is error exit code 1 with a pointer at `dojo init`.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 1 | A ByteDojo error — repository/problem/solution/bundle not found, unsupported problem id, missing toolchain, malformed data |
| 2 | Click usage error (bad flags or arguments) |
| 130 | Interrupted (Ctrl-C) |

Error messages are actionable and never include a stack trace unless
`--debug` is passed.
