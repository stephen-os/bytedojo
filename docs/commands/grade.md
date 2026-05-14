# `dojo grade`

> View test results and manually apply pass/fail/skip.

## Synopsis

```
dojo grade [IDENTIFIER] [--name TEXT | --desc TEXT | --last]
                       [--pass | --fail | --skip] [--manual]
                       [--notes TEXT]
                       [--python | --java | --cpp]
                       [--per-page N]
```

## Description

This command has two flavours:

1. **View mode** — without a status flag and without `--manual`, it
   simply renders the current test status for a problem (`PASSED` /
   `FAILED` / `SKIPPED` / `NOT TESTED`) along with its last test run
   timestamp and recorded output.

2. **Grade mode** — apply a grade. Either:
   - Pass a status flag directly: `--pass` / `--fail` / `--skip`
   - Use `--manual` for an interactive `[P]ass / [F]ail / [S]kip /
     [Q]uit` prompt that also asks for optional notes

Grading a problem as **passed** schedules it for spaced-repetition
review using the configured `review-frequency`. Subsequent review
events (via [`review complete`](review.md)) progress the SM-2 state.

Without an `IDENTIFIER` / selector flag, `dojo grade` enters an
interactive batch view: a paginated list of every registered problem
with its current status, where you can pick one to view or grade.

## Arguments

- `IDENTIFIER` (optional) — a problem ID. Omit for batch mode or when
  using `--name` / `--desc` / `--last`.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--name TEXT`, `-n TEXT` | Fuzzy match against the problem title | unset |
| `--desc TEXT`, `-d TEXT` | Keyword search in the description | unset |
| `--last` | Most-recently-fetched problem in this language | `false` |
| `--pass`, `-p` | Mark as passed | `false` |
| `--fail`, `-f` | Mark as failed | `false` |
| `--skip`, `-s` | Mark as skipped | `false` |
| `--manual`, `-m` | Show the interactive pass/fail/skip prompt | `false` |
| `--notes TEXT` | Attach notes to the grade record | unset |
| `--python`, `-py` | Operate on the Python version | (default language) |
| `--java` | Operate on the Java version | |
| `--cpp` | Operate on the C++ version | |
| `--per-page N` | Problems per page in batch view mode | `10` |

`--pass`, `--fail`, and `--skip` are mutually exclusive.

## Examples

```bash
# Interactive batch view of every registered problem.
dojo grade

# View status of problem #1 (no grade applied).
dojo grade 1

# Mark problem #1 as passed (schedules a review).
dojo grade 1 --pass

# Mark as failed with a note.
dojo grade 1 -f --notes "TLE on case 7"

# Search by title, then manually grade.
dojo grade --name "Two Sum" --manual

# Skip the last fetched problem.
dojo grade --last --skip
```

## Exit codes

- `0` — view rendered or grade applied
- `1` — pre-flight failure or invalid combination of status flags

## See also

- [`test`](test.md) — record test results automatically
- [`review`](review.md) — track scheduled reviews after passing
- [`stats`](stats.md) — see overall pass/fail counts
