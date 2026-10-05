# `dojo pick`

> Pick a random problem matching difficulty / tag filters.

## Synopsis

```
dojo pick [--difficulty LEVEL] [--tag TAG ...]
          [--all | --solved] [--fetch]
```

## Description

Picks a random problem from the bundled catalog. By default the pool is
problems you haven't registered yet, and after showing the pick the CLI
asks what to do with it:

```
[f]etch / [r]epick / [q]uit
```

- `f` fetches the problem immediately (same as `dojo fetch <id>`)
- `r` rolls again with the same filters
- `q` quits, leaving a `dojo fetch <id>` hint

`--fetch` skips the prompt entirely: pick one and fetch it.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--difficulty`, `-d` | `easy`/`1`, `medium`/`2`, `hard`/`3` | any |
| `--tag`, `-t` | Filter by tag; repeatable (OR semantics) | any |
| `--all`, `-a` | Pick from all problems, registered or not | `false` |
| `--solved`, `-s` | Pick only from registered problems | `false` |
| `--fetch` | Non-interactive: fetch the pick immediately | `false` |

## Examples

```bash
dojo pick                        # Random unsolved problem, interactive
dojo pick -d easy                # Random easy problem
dojo pick -t array -t dp         # Array OR dynamic-programming
dojo pick --fetch                # Pick and fetch in one step
dojo pick --solved               # Something you've done before
```

## See also

- [`fetch`](fetch.md) — what `f`/`--fetch` runs under the hood
- [`query`](query.md) — browse instead of rolling dice
