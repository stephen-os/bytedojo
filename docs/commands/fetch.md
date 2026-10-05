# `dojo fetch`

> Place bundled problems on disk with a synthesised starter stub.

## Synopsis

```
dojo fetch IDS [--python]
              [--new-attempt | --version N | --path DIR]
```

## Description

Fully offline: problems come from the catalog bundled inside the
package, never the network. Fetch is restricted to that catalog — every
id is validated up front, and an unsupported id aborts the whole batch
with a pointer at `dojo query` before anything is placed.

Modes (mutually exclusive):

- **default** — register the problem and place v1 at
  `problems/<id>-<slug>/v001/solution.py`. If the problem is already
  registered the fetch is refused with a hint at the other modes.
- **`--new-attempt` / `-na`** — add the next attempt version
  (`v002`, `v003`, ...). Older versions keep their recorded outcome.
- **`--version N`** — rewrite tracked version N in place (also restores
  the file if it was deleted).
- **`--path DIR`** — drop an untracked scratch copy into a custom
  directory. No database entry, no version bump.

The placed file is synthesised from the problem's bundled data:

- A header comment with problem ID + title + difficulty + tags
- The problem description, worked examples and constraints
- Baseline imports (`typing`, `collections`, `heapq`, ...)
- A typed `class Solution` stub built from the test bundle's method
  signature (e.g. `def twoSum(self, nums: List[int], target: int) -> List[int]:`)
- An `if __name__ == "__main__":` stub for quick local runs

If the signature uses `BINARY_TREE` / `LINKED_LIST` types, the matching
sibling modules (`tree_node.py`, `list_node.py`) are placed alongside so
the solution runs as-is.

## Arguments

- `IDS` (required, one or more) — problem identifiers in any combination of:
  - Single: `1`
  - Comma list: `1,2,3`
  - Range: `1..10`
  - Mixed: `1,5..10,15`

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--python`, `-py` | Fetch as Python | configured `default-language` |
| `--new-attempt`, `-na` | Add the next attempt version even if already registered | `false` |
| `--version N` | Rewrite tracked version N in place | unset |
| `--path DIR` | Place into a custom directory; do not register in the DB | unset |

## Examples

```bash
# Register and place v1 of problem #1.
dojo fetch 1

# Add a fresh attempt (v2) of a problem you already have.
dojo fetch 1 --new-attempt

# Rewrite v3 of #1 in place (overwrites that version's file).
dojo fetch 1 --version 3

# Untracked scratch copy.
dojo fetch 1 --path ./scratch

# Batch fetch with ranges.
dojo fetch 1,5..10,15
```

## See also

- [`pick`](pick.md) — choose a random problem (with `--fetch` to grab it)
- [`query`](query.md) — browse the supported catalog
- [`test`](test.md) — run the bundled cases against your solution
