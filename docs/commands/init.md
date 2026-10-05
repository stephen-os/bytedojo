# `dojo init`

> Create a `.dojo/` repository in the current (or chosen) directory.

## Synopsis

```
dojo init [--path DIR] [--force]
```

## Description

Creates the `.dojo/` directory that every other command discovers by
walking up from the working directory. It contains:

- `db.sqlite` — problems, versioned attempts, review schedule
- `settings.json` — user preferences (see [`settings`](settings.md))
- `.gitignore` — excludes build artifacts and logs
- `README.md` — a short orientation file
- `build/` — created on demand for test staging

Running `init` where a `.dojo/` already exists fails with a hint;
`--force` re-runs the bootstrap (existing rows are kept — the schema
setup is idempotent).

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--path`, `-p` | Directory to initialize | current directory |
| `--force` | Reinitialize even if `.dojo/` exists | `false` |

## Examples

```bash
dojo init                 # Here
dojo init -p ~/practice   # Somewhere else
dojo init --force         # Re-run the bootstrap
```

## See also

- [`fetch`](fetch.md) — the first thing to do afterwards
- [`support`](support.md) — confirm the environment is ready
