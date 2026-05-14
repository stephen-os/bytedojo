# ByteDojo CLI Reference

Every command available under `dojo`. Each page has the same shape:
**Synopsis → Description → Arguments → Options → Examples → See also**.

The TUI (`dojo enter`) is intentionally not documented here; launch it
and the UI is self-describing.

## Quick reference

| Command | One-liner |
| --- | --- |
| [`init`](init.md) | Create a `.dojo/` repository in the current (or chosen) directory |
| [`fetch`](fetch.md) | Pull a LeetCode problem and place the starter solution on disk |
| [`run`](run.md) | Execute a problem's solution and capture its output |
| [`test`](test.md) | Run the bundled test cases against a solution |
| [`grade`](grade.md) | View test results and manually apply pass/fail/skip |
| [`pick`](pick.md) | Pick a random problem matching difficulty / tag filters |
| [`query`](query.md) | Browse / filter the local problem catalog |
| [`review`](review.md) | Spaced-repetition review system (group with subcommands) |
| [`settings`](settings.md) | View and modify dojo settings (group with subcommands) |
| [`stats`](stats.md) | Repository statistics |
| [`support`](support.md) | Environment + toolchain diagnostic report |

## Common patterns

**Selectors.** `run`, `test`, and `grade` accept the same set of selectors
to identify which registered problem to act on:

- Positional `IDENTIFIER` — a numeric problem ID
- `--name TEXT` / `-n TEXT` — fuzzy match against the problem title
- `--desc TEXT` / `-d TEXT` — keyword search in the description
- `--last` — most-recently-fetched problem in the configured language

If the lookup is ambiguous the CLI prompts; pass `--name`/`--desc` with
something specific enough to disambiguate.

**Language flags.** `--python` (`-py`), `--java`, `--cpp` are accepted by
every command that operates on a language-specific solution. They are
mutually exclusive. When none is passed, the configured default
language is used (see [`settings default-language`](settings.md)).

**Repository discovery.** Every command walks up from the current
directory looking for a `.dojo/` folder, so you can run them from any
subdir of your dojo repo. If no `.dojo/` is found anywhere up the tree
the command exits with `Not inside a .dojo repository. Please run 'dojo
init' first.`

## Global flags

These work on the top-level `dojo` group, before any subcommand:

| Flag | Behaviour |
| --- | --- |
| `--version` | Print the ByteDojo version and exit |
| `--author` | Print the author and exit |
| `--desc` | Print the project description and exit |
| `--debug` | Enable debug-level logging for the remainder of the invocation |
| `--help` | Show the top-level command listing |
