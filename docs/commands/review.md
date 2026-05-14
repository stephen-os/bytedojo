# `dojo review`

> Spaced-repetition review system (group with subcommands).

## Synopsis

```
dojo review [--all]                                  # show due reviews
dojo review pick                                     # pick a random due
dojo review complete IDENTIFIER (--easy|--good|--hard) [SELECTORS] [LANG]
dojo review add      IDENTIFIER [--days N]           [SELECTORS] [LANG]
dojo review snooze   IDENTIFIER [--days N]           [SELECTORS] [LANG]
dojo review remove   IDENTIFIER                      [SELECTORS] [LANG]
dojo review stats                                    # counts summary
```

## Description

ByteDojo uses an SM-2-style spaced-repetition system:

- Grading a problem as **passed** ([`grade --pass`](grade.md)) seeds a
  review at the configured base interval ([`review-frequency`](settings.md)).
- When the review comes due, work the problem again and report back
  with `dojo review complete <id> --easy|--good|--hard`:
  - `--good` — recalled with effort. Next interval = current × ease.
  - `--easy` — recalled effortlessly. Adds a 1.3× bonus; ease grows.
  - `--hard` — struggled. Interval resets to 1 day; ease shrinks.
- `add` / `snooze` / `remove` are escape hatches for managing the
  queue manually.

All selectors and language flags work the same way as
[`run`](run.md) / [`test`](test.md) / [`grade`](grade.md).

## Subcommands

### Default — show due reviews

Listed table view of problems due today (or all scheduled with `--all`).
Shows ID, source, due-date label (`Today` / `Tomorrow` / `In N days` /
`N days overdue` / ISO date), review count, and title.

| Flag | Description | Default |
| --- | --- | --- |
| `--all`, `-a` | Include future-scheduled reviews, not just due | `false` |

### `pick` — pick a random due review

Picks one due review at random and renders the problem details plus
the SM-2 state (`current interval`, `ease`) and the next-step commands
(`dojo test` / `dojo review complete`).

### `complete IDENTIFIER` — apply SM-2 update

| Flag | Description | Default |
| --- | --- | --- |
| `--easy` | Quality: effortless recall | |
| `--good` | Quality: standard recall (one required) | |
| `--hard` | Quality: struggled | |
| `--name TEXT`, `-n TEXT` | Selector | |
| `--desc TEXT`, `-d TEXT` | Selector | |
| `--last` | Selector | |
| `--python`/`--java`/`--cpp` | Language | configured default |

Errors if no quality flag is passed, or if the problem has no active
review track (use `dojo grade --pass` or `dojo review add` first).

### `add IDENTIFIER` — manually queue for review

Adds a problem to the review queue without grading it as passed.
Errors if a review is already scheduled — use `snooze` to delay an
existing review or `remove` then `add` to reset.

| Flag | Description | Default |
| --- | --- | --- |
| `--days N` | Initial interval | configured `review-frequency` |
| selector + language flags | (as above) | |

### `snooze IDENTIFIER` — push out a scheduled review

Moves `next_review_date` to `today + N` days. Does NOT touch SRS state
(interval / ease / repetitions stay the same).

| Flag | Description | Default |
| --- | --- | --- |
| `--days N` | Snooze duration | `1` |
| selector + language flags | (as above) | |

### `remove IDENTIFIER` — drop from queue

Deletes the review track for a problem entirely. After this, the
problem is no longer in the review pool and won't surface in
`dojo review` until you `add` or `grade --pass` it again.

### `stats` — summary counts

Reports `Due Today`, `Due This Week`, `Total in Review`, and the
configured review frequency. No flags.

## Examples

```bash
# Today's review session.
dojo review

# Random due problem.
dojo review pick

# Solve it, then mark complete.
dojo test 1 --python                  # verify
dojo review complete 1 --python --good

# Manually queue a problem (3 days out).
dojo review add 1 --python --days 3

# Push tomorrow's review out a week.
dojo review snooze 1 --python --days 7

# Drop a problem from review entirely.
dojo review remove 1 --python

# Statistics.
dojo review stats
```

## Exit codes

- `0` — success (including caught-up / empty cases)
- `1` — pre-flight failure, missing required flag, problem not in
  review queue, or already-queued conflict on `add`

## See also

- [`grade`](grade.md) — passing a problem seeds the review track
- [`settings`](settings.md) — `review-frequency` controls the base
  interval
