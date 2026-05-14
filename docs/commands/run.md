# `dojo run`

> Execute a problem's solution and capture its output.

## Synopsis

```
dojo run [IDENTIFIER] [--name TEXT | --desc TEXT | --last]
                     [--python | --java | --cpp]
                     [--version N]
```

## Description

Resolves a registered problem, locates its solution file, runs it
through the right language toolchain, and prints the captured stdout
(and stderr / compile errors) back to the terminal.

This is the quick-feedback path: it just runs your `main()` /
`if __name__ == "__main__":` block. For the full bundled test suite,
use [`test`](test.md).

The header above the output shows what was *actually* run — including
the version-specific file path, so when `--version N` is passed you see
the v{N} path, not the latest-attempt path baked into the registered
record.

## Arguments

- `IDENTIFIER` (optional) — a problem ID. Omit when using
  `--name` / `--desc` / `--last`.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--name TEXT`, `-n TEXT` | Fuzzy match against the problem title | unset |
| `--desc TEXT`, `-d TEXT` | Keyword search in the description | unset |
| `--last` | Run the most-recently-fetched problem in this language | `false` |
| `--version N` | Run a specific attempt version | latest |
| `--python`, `-py` | Run the Python version | (default language) |
| `--java` | Run the Java version | |
| `--cpp` | Run the C++ version | |

## Examples

```bash
# Run problem #1 (default language).
dojo run 1

# Run the Java version explicitly.
dojo run 1 --java

# Search by name (prompts to disambiguate if multiple match).
dojo run --name "Two Sum"

# Run the most recently fetched problem.
dojo run --last

# Run a specific older attempt (v2 of problem 1).
dojo run 1 --version 2
```

## Exit codes

- `0` — solution executed (regardless of the solution's own exit code)
- `1` — pre-flight failure (missing repo / missing file / missing
  toolchain / unsupported language)

The solution's own exit code is shown in the output footer but does
not propagate up to the shell — `dojo run` succeeds as long as the
runner managed to invoke the program.

## See also

- [`test`](test.md) — run against the bundled test cases instead
- [`fetch`](fetch.md) — place a solution first
- [`support`](support.md) — diagnose missing toolchains
