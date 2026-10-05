# `dojo settings`

> View and modify dojo settings (group with subcommands).

## Synopsis

```
dojo settings [list]
dojo settings default-language LANGUAGE
dojo settings review-frequency DAYS
dojo settings set KEY VALUE
dojo settings get KEY
```

## Description

User preferences live in `.dojo/settings.json` — one home, three keys:

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `default-language` | choice (`python`) | `python` | Language used when no `--python`-style flag is given |
| `review-frequency` | int, 1–365 | `7` | Base SM-2 interval: the gap scheduled when a problem first passes |
| `organize-by-language` | bool | `false` | Place future attempts under `problems/<id>-<slug>/<language>/v{N}/` instead of the flat layout |

`default-language` and `review-frequency` have dedicated subcommands;
`set`/`get` work for every key. Values are validated before saving
(unknown keys and out-of-range values are rejected with the valid
options listed).

## Examples

```bash
dojo settings                              # Show all settings
dojo settings default-language python      # Set default language
dojo settings review-frequency 3           # First review after 3 days
dojo settings set organize-by-language true
dojo settings get review-frequency
```

## See also

- [`review`](review.md) — what `review-frequency` feeds into
- [`fetch`](fetch.md) — where `organize-by-language` changes paths
