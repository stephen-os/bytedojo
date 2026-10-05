# `dojo grade`

> Manually apply pass/fail/skip to a problem.

## Synopsis

```
dojo grade [IDENTIFIER] [--name TEXT] [--desc TEXT] [--last]
           [--manual | --pass | --fail | --skip] [--notes TEXT]
           [--per-page N] [--python]
```

## Description

`dojo test` is the normal grading path; `grade` is the manual override
for when you solved something away from the runner (whiteboard, another
machine) or want to set a problem aside. Grades land on both the latest
attempt and the problem row, with the same schedule effects a test
outcome would have:

- `--pass` — creates the review track, or advances it if a review is due
- `--fail` — lapses a scheduled review (due again tomorrow)
- `--skip` — sets the problem aside and removes its review track

With no selector at all, `grade` opens an interactive batch browser:
page through every registered problem, select one by number to view and
grade it manually.

## Arguments

- `IDENTIFIER` (optional) — numeric problem ID. Omit it (and all other
  selectors) for the batch browser.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--name`, `-n` | Fuzzy match on title | unset |
| `--desc`, `-d` | Keyword search in description | unset |
| `--last` | Most recently fetched problem | `false` |
| `--manual`, `-m` | Prompt for a grade interactively | `false` |
| `--pass`, `-p` | Mark as passed | `false` |
| `--fail`, `-f` | Mark as failed | `false` |
| `--skip`, `-s` | Mark as skipped (drops the review track) | `false` |
| `--notes TEXT` | Attach a note to the grade | unset |
| `--per-page N` | Problems per page in the batch browser | `10` |
| `--python`, `-py` | Language preference (warns on mismatch) | unset |

`--pass`, `--fail` and `--skip` are mutually exclusive.

## Examples

```bash
dojo grade                      # Browse all problems interactively
dojo grade 1                    # View status of problem #1
dojo grade 1 --pass             # Quick pass (schedules the review)
dojo grade 1 -f --notes "TLE"   # Fail with a note
dojo grade 1 --skip             # Set aside; drops the review track
dojo grade 1 --manual           # Prompt for p/f/s interactively
```

## See also

- [`test`](test.md) — the automatic grading loop
- [`review`](review.md) — the schedule those grades drive
