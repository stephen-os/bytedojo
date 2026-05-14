# `dojo test`

> Run the bundled test cases against a solution.

## Synopsis

```
dojo test [IDENTIFIER] [--name TEXT | --desc TEXT | --last]
                      [--python | --java | --cpp]
                      [--version N] [--verbose] [--timeout SECS]
```

## Description

Executes the typed test bundle for a problem against the user's
`Solution` and records the result. For each test case the bundle's
input is converted to the language's native types (including
`TreeNode` / `ListNode` from the user's own sibling files), the
solution method is invoked, and the result is compared per the case's
declared `comparison` mode (`exact` / `unordered_all` /
`unordered_outer`).

The recorded outcome lands in the database on both the per-problem row
*and* the specific versioned attempt — testing v2 doesn't overwrite
v1's recorded outcome.

Output shape:

- A header with problem details, version, and file path
- A status banner — `PASSED`, `FAILED`, `ERROR`, or `UNGRADED`
- Failing case details (input / expected / actual) inline
- With `--verbose`, every passing case is listed too

The `UNGRADED` state covers "no failures, but no cases ran" (e.g. the
bundle exists with zero cases, or every case was filtered).

## Arguments

- `IDENTIFIER` (optional) — a problem ID. Omit when using
  `--name` / `--desc` / `--last`.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--name TEXT`, `-n TEXT` | Fuzzy match against the problem title | unset |
| `--desc TEXT`, `-d TEXT` | Keyword search in the description | unset |
| `--last` | Test the most-recently-fetched problem in this language | `false` |
| `--version N` | Test a specific attempt version | latest |
| `--python`, `-py` | Test the Python version | (default language) |
| `--java` | Test the Java version | |
| `--cpp` | Test the C++ version | |
| `--verbose`, `-v` | Show all test case results (including passing) | `false` |
| `--timeout SECS`, `-t SECS` | Per-run timeout in seconds | `60` |

## Examples

```bash
# Test problem #1 (default language).
dojo test 1

# Show every case, not just failures.
dojo test 1 --verbose

# Test the last fetched problem in C++.
dojo test --last --cpp

# Bump the timeout for a slow solution.
dojo test 200 --timeout 120

# Test an older version, leaving v3's recorded outcome alone.
dojo test 1 --version 2
```

## Exit codes

- `0` — tests ran (regardless of pass / fail)
- `0` — soft skip (no bundle / zero cases): the case is reported and
  nothing is recorded to the DB
- `1` — pre-flight failure (missing repo / file / toolchain / bundle,
  unsupported language)

## See also

- [`run`](run.md) — quick local execution without the test bundle
- [`grade`](grade.md) — view recorded results or override manually
- [`support`](support.md) — diagnose missing toolchains
