# `dojo test`

> Run the bundled test cases; record the outcome and drive the review schedule.

## Synopsis

```
dojo test [IDENTIFIER] [--name TEXT] [--desc TEXT] [--last]
          [--version N] [--verbose] [--timeout SECONDS] [--python]
```

## Description

Stages the solution together with the universal Python runner into
`.dojo/build/`, executes every bundled test case, prints the results,
and records the outcome on **both** the attempt and the problem row (so
`query` and `stats` never disagree).

Testing is the primary loop — the outcome drives the spaced-repetition
schedule:

| Outcome | Status | Schedule effect |
| --- | --- | --- |
| Pass, no schedule yet | `PASSED` | Review created at the base interval |
| Pass, review due | `PASSED` | Review advanced (SM-2, quality *good*) |
| Pass, review not due | `PASSED` | No change (early practice) |
| Cases failed | `FAILED` | Scheduled review lapses — due tomorrow |
| Never evaluated (compile error / runner crash) | `ERROR` | Same lapse as a failure |

Fetch guarantees every registered problem has a test bundle; a missing
bundle is reported as a (defensive) corpus error.

## Arguments

- `IDENTIFIER` (optional) — numeric problem ID. Omit it when using
  `--name`, `--desc` or `--last`.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--name`, `-n` | Fuzzy match on title | unset |
| `--desc`, `-d` | Keyword search in description | unset |
| `--last` | Most recently fetched problem | `false` |
| `--version N` | Test a specific attempt version | latest |
| `--verbose`, `-v` | Show every case result (default shows first 5 failures) | `false` |
| `--timeout`, `-t` | Whole-run timeout in seconds | `60` |
| `--python`, `-py` | Language preference (warns on mismatch) | unset |

## Examples

```bash
dojo test 1                    # Test problem #1
dojo test 1 --verbose          # Show all case results
dojo test 1 --version 2        # Test attempt v2
dojo test --last -t 120        # Last fetched problem, longer timeout
```

## See also

- [`review`](review.md) — what the schedule does with your passes
- [`grade`](grade.md) — the manual override
