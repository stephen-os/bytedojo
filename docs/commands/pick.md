# `dojo pick`

> Pick a random problem matching difficulty / tag filters.

## Synopsis

```
dojo pick [--difficulty LEVEL] [--tag TAG ...]
          [--all | --solved]
```

## Description

Selects one random problem from the local catalog matching your
filters. By default the pool is **unsolved** — problems you haven't
fetched / registered yet — which is the right default when you're
looking for the next thing to work on.

Pass `--all` to ignore registration status, or `--solved` to pick from
problems already registered (handy when revisiting).

The output names the picked problem and includes the exact `dojo
fetch` command to grab it.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--difficulty LEVEL`, `-d LEVEL` | Filter by difficulty: `easy`, `medium`, or `hard` | any |
| `--tag TAG`, `-t TAG` | Filter by algorithm tag. Pass multiple times for OR semantics. | any |
| `--all`, `-a` | Pick from all problems (ignore registration status) | `false` |
| `--solved`, `-s` | Pick from registered problems only | `false` |

Unknown tags are silently dropped (with a warning logged) — if every
tag you passed is unknown the command errors out so you can correct
the typo.

`--all` and `--solved` are mutually exclusive scope flags.

## Examples

```bash
# Random unsolved problem.
dojo pick

# Random easy problem.
dojo pick -d easy

# Random array problem.
dojo pick -t array

# Random medium tree-or-graph problem.
dojo pick -d medium -t tree -t graph

# Pick from problems I've already registered.
dojo pick --solved

# Pick from the whole catalog, regardless of registration.
dojo pick --all
```

## Exit codes

- `0` — a problem was picked, or the pool was empty
- `1` — repository missing, unknown difficulty, or every supplied tag
  was unknown

## See also

- [`query`](query.md) — browse problems by filter without picking one
- [`fetch`](fetch.md) — grab the picked problem
