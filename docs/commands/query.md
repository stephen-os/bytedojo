# `dojo query`

> Browse / filter the bundled problem catalog.

## Synopsis

```
dojo query [PROBLEM_IDS ...] [--difficulty LEVEL] [--tag TAGS]
           [--search TEXT] [--page N] [--per-page N] [--list-tags]
```

## Description

Pages through the bundled catalog — the exact set of problems `fetch`
supports. Each row shows the problem id, your status for it
(`✓` passed, `✗` failed, `!` error, `~` skipped, `·` untouched), its
difficulty and title. Navigation after the listing:

```
n = next page    p = prev page    # = jump to page    q = quit
```

`--search` matches the problem title first and falls back to the full
description text.

## Arguments

- `PROBLEM_IDS` (optional) — restrict to ids/ranges: `1 2 3`, `1..50`,
  `1,5..10,15`.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--difficulty`, `-d` | `easy`/`1`, `medium`/`2`, `hard`/`3` | any |
| `--tag`, `-t` | Filter by tag; repeatable or comma-separated | any |
| `--search`, `-s` | Text search in titles + descriptions | unset |
| `--page`, `-p` | Starting page | `1` |
| `--per-page`, `-n` | Problems per page | `20` |
| `--list-tags` | Print every available tag and exit | `false` |

## Examples

```bash
dojo query                          # Browse everything
dojo query 1..50                    # Problems 1-50
dojo query -d easy -t array         # Easy array problems
dojo query -s "binary search"       # Text search
dojo query --list-tags              # All tags
```

## See also

- [`pick`](pick.md) — let dojo choose for you
- [`fetch`](fetch.md) — grab what you found
