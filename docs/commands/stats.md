# `dojo stats`

> Repository statistics and per-problem attempt detail.

## Synopsis

```
dojo stats [--list] [--verbose] [--source TEXT] [--difficulty LEVEL]
```

## Description

Without flags: summary counts of registered problems grouped by
difficulty and source. With `--list`: one card per registered problem
(id, title, difficulty, language, fetch time, file path). Adding
`--verbose` appends attempt counts — total attempts, latest version,
pass/fail/skip tallies and how many times the solution was run.

Attempt counts are aggregated across the problem's whole (flat) version
history, whatever language each attempt was in.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--list` | List problems instead of the summary | `false` |
| `--verbose`, `-v` | Include attempt counts per problem | `false` |
| `--source` | Filter by source (e.g. `leetcode`) | any |
| `--difficulty`, `-d` | `easy` / `medium` / `hard` | any |

## Examples

```bash
dojo stats                     # Summary counts
dojo stats --list              # All registered problems
dojo stats --list -v           # ...with attempt counts and run tallies
dojo stats --list -d easy      # Easy problems only
```

## See also

- [`review`](review.md) — `review stats` for schedule counters
- [`query`](query.md) — the whole catalog, not just what you registered
