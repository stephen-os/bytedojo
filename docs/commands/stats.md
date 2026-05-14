# `dojo stats`

> Repository statistics.

## Synopsis

```
dojo stats [--list] [--verbose] [--source TEXT] [--difficulty LEVEL]
```

## Description

Two modes:

- **Summary mode (default)** — high-level numbers: total problems
  registered, grouped by difficulty, grouped by source.
- **List mode (`--list`)** — per-problem detail: one entry per
  registered problem with source, difficulty, language, fetched
  timestamp, and file path. Pass `--verbose` for an attempt-stats
  placeholder (per-language detail rebuild is pending).

The two filter flags (`--source`, `--difficulty`) work in both modes
but are most useful in `--list` mode.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--list` | Switch to per-problem listing | `false` |
| `--verbose`, `-v` | Show detailed attempt info in `--list` mode | `false` |
| `--source TEXT` | Filter by source (e.g. `leetcode`) | any |
| `--difficulty LEVEL`, `-d LEVEL` | Filter by difficulty: `easy`, `medium`, or `hard` | any |

## Examples

```bash
# Summary view.
dojo stats

# All registered problems.
dojo stats --list

# Easy problems with attempt details.
dojo stats --list -d easy --verbose

# Problems from leetcode only.
dojo stats --list --source leetcode
```

## Exit codes

- `0` — stats rendered
- `1` — repository missing or invalid `--difficulty` value (click
  rejects unknown choices before the command runs)

## See also

- [`query`](query.md) — browse the local catalog (not just registered)
- [`review`](review.md) — review-specific counts
- [`support`](support.md) — environment status (not problem stats)
