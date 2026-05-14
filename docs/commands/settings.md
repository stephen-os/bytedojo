# `dojo settings`

> View and modify dojo settings (group with subcommands).

## Synopsis

```
dojo settings                                # show all settings
dojo settings list                           # alias for the default view
dojo settings default-language LANG          # change default language
dojo settings review-frequency DAYS          # change review interval
dojo settings set KEY VALUE                  # set a leetcode.* key
dojo settings get KEY                        # read a leetcode.* key
```

## Description

Settings live in two places:

- **`.dojo/db.sqlite` `config` table** — runtime config (default
  language, default source, review frequency)
- **`.dojo/settings.json`** — per-source user preferences
  (currently only `leetcode.organization`)

The default view (`dojo settings`, no subcommand) prints both blocks
together so you can see every effective setting at once.

## Subcommands

### Default view / `list`

Renders every setting under a header. No flags.

### `default-language LANG`

Set the default language used by `fetch`, `run`, `test`, and `grade`
when no `--python` / `--java` / `--cpp` flag is given.

| Argument | Allowed values |
| --- | --- |
| `LANG` | `python`, `java`, `cpp` (case-insensitive) |

### `review-frequency DAYS`

Set the base interval (in days) used when a problem first enters the
review track via `grade --pass`. Subsequent SM-2 progression after
`review complete` is independent of this value.

| Argument | Constraint |
| --- | --- |
| `DAYS` | integer; `1 <= DAYS <= 365` |

### `set KEY VALUE`

Set a typed key/value pair under `.dojo/settings.json`. Currently
recognised:

| Key | Allowed values | Meaning |
| --- | --- | --- |
| `leetcode.organization` | `flat`, `difficulty` | How fetched problems are laid out under `problems/` |

Unknown keys and out-of-whitelist values are rejected with a clear
error listing the valid options.

### `get KEY`

Read the current value of a `set`-style key. Errors on unknown keys.

## Examples

```bash
# Show everything.
dojo settings

# Use Java for everything by default.
dojo settings default-language java

# Review weekly instead of the default.
dojo settings review-frequency 7

# Switch to difficulty-keyed folder layout.
dojo settings set leetcode.organization difficulty

# Read a setting back.
dojo settings get leetcode.organization
```

## Exit codes

- `0` — view rendered or setting applied
- `1` — repository missing, unknown subcommand argument, out-of-range
  numeric value, or unknown / invalid `set`/`get` key

## See also

- [`init`](init.md) — sets sensible defaults at repo creation
- [`review`](review.md) — `review-frequency` controls its seed interval
