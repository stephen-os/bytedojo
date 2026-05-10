# Contributing to ByteDojo

Thanks for your interest in contributing! This document covers the conventions
we follow so your changes can be reviewed and merged smoothly.

## Commit Messages

We use [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).
Every commit on `main` should follow this format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type       | When to use                                                          |
|------------|----------------------------------------------------------------------|
| `feat`     | A new user-facing feature                                            |
| `fix`      | A bug fix                                                            |
| `refactor` | A code change that neither fixes a bug nor adds a feature            |
| `perf`     | A performance improvement                                            |
| `docs`     | Documentation only                                                   |
| `test`     | Adding or fixing tests                                               |
| `build`    | Build system, dependencies, packaging                                |
| `ci`       | CI configuration and scripts                                         |
| `chore`    | Maintenance that doesn't fit elsewhere (cleanup, renames, etc.)      |
| `style`    | Formatting, whitespace — no code behavior change                     |

### Scope (optional)

Scope is the area of the codebase you're touching. Common scopes in this repo:

- `repo` — `Repository` and DB-facing code
- `fetch`, `run`, `grade`, etc. — individual subcommands
- `tui` — terminal UI
- `cli` — top-level click command wiring

### Breaking changes

Append `!` after the type/scope **and** include a `BREAKING CHANGE:` footer
explaining what broke and how to migrate:

```
refactor(repo)!: split place_problem into atomic operations

BREAKING CHANGE: Repository.place_problem signature changed from
(problem, language, force, source) -> bool to (problem, language, path)
-> None. PlaceResult is removed.
```

### Examples

```
feat(fetch): add --version flag to refetch existing attempts
fix(run): handle missing solution file without crashing
refactor(repo): make open/find/create classmethods
docs: document scratch-mode placement in fetch
test(repo): cover Repository.find walking upward
chore: bump pytest to 8.x
```

### Subject line rules

- Lowercase first letter
- No trailing period
- Imperative mood (`add`, `fix`, `remove` — not `added`/`adds`)
- Keep it under ~72 characters

### Body (optional)

Use the body to explain *why* the change is needed, not what the diff already
shows. Wrap at ~72 characters per line.

## Pull Requests

- Branch off `main`.
- Keep PRs focused — one logical change per PR is easier to review.
- Make sure tests pass before requesting review.
- Reference any related issues in the PR description.

## Questions

Open an issue if you're unsure about scope, approach, or whether something is
in-scope for the project.
