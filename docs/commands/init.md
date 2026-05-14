# `dojo init`

> Create a `.dojo/` repository in the current (or chosen) directory.

## Synopsis

```
dojo init [--path PATH] [--force]
```

## Description

Initialises a ByteDojo repository — a sibling `.dojo/` directory next to
your problems, holding the sqlite progress database, your settings, and
the build cache.

Created on first run:

```
.dojo/
├── db.sqlite      # problem + attempt + review tracking
├── settings.json  # local preferences
├── .gitignore     # excludes build artefacts + logs
└── README.md      # describes the layout
```

You'll typically run `init` once per workspace and never again. Use
`--force` to wipe the existing `.dojo/` and start over.

## Options

| Flag | Description | Default |
| --- | --- | --- |
| `--path PATH`, `-p PATH` | Directory to initialise. The `.dojo/` lands underneath it. | Current directory |
| `--force` | Reinitialise even if `.dojo/` already exists | `false` |

## Examples

```bash
# Default: initialise in cwd.
dojo init

# Initialise in a specific directory.
dojo init --path ./my-leetcode

# Wipe and re-initialise.
dojo init --force
```

## Exit codes

- `0` — repository created successfully
- `1` — `.dojo/` already exists and `--force` was not passed

## See also

- [`settings`](settings.md) — configure defaults after init
- [`fetch`](fetch.md) — pull your first problem
