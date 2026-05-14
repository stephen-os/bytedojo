# `dojo fetch`

> Pull a LeetCode problem and place the starter solution on disk.

## Synopsis

```
dojo fetch IDS [--python | --java | --cpp]
              [--force | --version N | --path DIR]
```

## Description

Fetches one or more problems from the local LeetCode catalog and writes
a starter solution (and any sibling node-class files) onto disk. Three
mutually exclusive modes:

- **default** — register a new attempt and place under
  `problems/<id>-<slug>/<lang>/v{N}/solution.<ext>`. A new attempt
  bumps the version (`v001`, `v002`, ...).
- **`--version N`** — rewrite the existing v{N} of a tracked problem
  in place. Useful for refreshing the starter without losing version
  history.
- **`--path DIR`** — drop a one-off copy into a custom directory.
  Untracked: no database entry, no version bump.

The placed file includes:

- A header comment with problem ID + title + difficulty
- The HTML-stripped problem description
- Baseline imports for the language (typing / collections / etc.)
- The user's starter `class Solution` (or `Solution.java` /
  `solution.cpp`)
- A `main()` / `if __name__ == "__main__"` stub for quick local runs

If the problem references `TreeNode` / `ListNode` / `Node`, the relevant
sibling files (`tree_node.py`, `ListNode.java`, `tree_node.hpp`, etc.)
are placed alongside so the solution compiles / runs as-is.

## Arguments

- `IDS` (required, one or more) — problem identifiers in any combination of:
  - Single: `1`
  - Comma list: `1,2,3`
  - Range: `1..10`
  - Mixed: `1,5..10,15`

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--python`, `-py` | Fetch as Python | (default language from settings) |
| `--java` | Fetch as Java | |
| `--cpp` | Fetch as C++ | |
| `--force` | Create a new attempt even if the problem is already registered (bumps to v{N+1}) | `false` |
| `--version N` | Refetch an existing tracked version, rewriting it in place | unset |
| `--path DIR` | Place into a custom directory; do not register in the DB | unset |

`--force` is incompatible with `--version` and `--path`. `--version` is
incompatible with `--path`.

## Examples

```bash
# New attempt of problem #1 (uses configured default language).
dojo fetch 1

# Fetch as Java; force a new attempt even if registered.
dojo fetch 1 --java --force

# Refresh v3 of problem #1 in place (overwrites that version).
dojo fetch 1 --version 3

# Drop a one-off copy into ./scratch, untracked.
dojo fetch 1 --path ./scratch

# Batch fetch: 1, 2, and 5 through 10, in C++.
dojo fetch 1,2,5..10 --cpp
```

## Exit codes

- `0` — at least one problem was placed; per-problem results printed inline
- `1` — flag validation failed, unknown language, or repository missing

## See also

- [`init`](init.md) — required first
- [`run`](run.md) — execute the placed solution
- [`test`](test.md) — run the bundled test cases
