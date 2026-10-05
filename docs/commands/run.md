# `dojo run`

> Execute a solution's `__main__` and capture its output.

## Synopsis

```
dojo run [IDENTIFIER] [--name TEXT] [--desc TEXT] [--last]
         [--version N] [--python]
```

## Description

Resolves the registered problem, executes its solution file with the
language's toolchain (Python: the same interpreter running dojo), and
prints stdout/stderr plus the exit status. Each run increments the
attempt's run counter (visible in `dojo stats --list -v`).

`--version N` runs a specific attempt; the default is the latest. The
resolved attempt's language decides the toolchain.

## Arguments

- `IDENTIFIER` (optional) — numeric problem ID. Omit it when using
  `--name`, `--desc` or `--last`.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--name`, `-n` | Fuzzy match on title | unset |
| `--desc`, `-d` | Keyword search in description | unset |
| `--last` | Most recently fetched problem | `false` |
| `--version N` | Run a specific attempt version | latest |
| `--python`, `-py` | Language preference (warns on mismatch) | unset |

## Examples

```bash
dojo run 1                    # Run problem #1 (latest attempt)
dojo run 1 --version 2        # Run v2 specifically
dojo run --name "Two Sum"     # Search by name
dojo run --last               # Run the last fetched problem
```

## See also

- [`test`](test.md) — run the bundled cases and record the outcome
- [`fetch`](fetch.md) — place the solution file in the first place
