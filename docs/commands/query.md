# `dojo query`

> Browse / filter the local problem catalog.

## Synopsis

```
dojo query [PROBLEM_IDS ...] [--difficulty LEVEL]
           [--tag TAG ...] [--search TEXT]
           [--page N] [--per-page N]
           [--list-tags]
```

## Description

Interactive paginated browser over the local LeetCode problem catalog.
Renders each problem with:

- ID + title
- Difficulty marker (`E`/`M`/`H`)
- Status marker — `[P]` passed, `[F]` failed, `[S]` skipped, `[ ]`
  ungraded / not fetched. The marker reflects the best status across
  every language you've attempted the problem in.

Pagination loop accepts:

- `n` / `next` / `>` — next page
- `p` / `prev` / `<` — previous page
- `<number>` — jump to that page
- `q` / `quit` / Enter — exit

Pass `--list-tags` to skip the browser entirely and just print every
tag that appears in the catalog.

## Arguments

- `PROBLEM_IDS` (optional, multiple) — restrict the browser to specific
  IDs. Accepts the same formats as [`fetch`](fetch.md): single,
  comma list, range, mixed.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--difficulty LEVEL`, `-d LEVEL` | Filter by difficulty: `easy`, `medium`, `hard` | any |
| `--tag TAG`, `-t TAG` | Filter by tag. Repeat or comma-separate for OR. | any |
| `--search TEXT`, `-s TEXT` | Substring search in problem descriptions | unset |
| `--page N`, `-p N` | Starting page | `1` |
| `--per-page N`, `-n N` | Problems per page | `20` |
| `--list-tags` | Print every available tag and exit | `false` |

## Examples

```bash
# Browse everything.
dojo query

# Browse a specific range.
dojo query 1..50

# Easy array problems.
dojo query -d easy -t array

# Multiple tags (OR semantics).
dojo query -t array,hash-table

# Search descriptions.
dojo query -s "binary search"

# 50 per page, starting on page 3.
dojo query -d medium -n 50 -p 3

# Show all available tag names.
dojo query --list-tags
```

## Exit codes

- `0` — browser exited normally (or `--list-tags` printed and exited)
- `1` — repository missing, unknown difficulty, or invalid ID format

## See also

- [`pick`](pick.md) — random selection from the same filters
