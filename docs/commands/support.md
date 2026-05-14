# `dojo support`

> Environment + toolchain diagnostic report.

## Synopsis

```
dojo support
```

## Description

Prints a snapshot of the local environment and which language
toolchains are detected. Use it to:

- Confirm your setup before `dojo run` / `dojo test`
- Gather diagnostic info when reporting issues
- Quickly spot which language toolchains are missing

Output sections:

- **Environment** — ByteDojo version, Python version + interpreter
  path, OS / platform, current repository path (or "not in a .dojo
  repository" if you're outside one)
- **Toolchains** — one row per registered language, each marked
  `[OK]` or `[NO]`. For ready toolchains the detected binary paths and
  version string are shown. For missing toolchains a platform-specific
  install hint is printed.
- **Summary** — `All N toolchains ready` or `K of N toolchains ready`

`dojo support` can be run from anywhere — it doesn't require a `.dojo/`
repository (and notes its absence in the Environment block).

## Options

(none)

## Examples

```bash
# Quick environment check.
dojo support
```

Typical output:

```
======================================================================
  BYTEDOJO SUPPORT
======================================================================

  Environment:
    ByteDojo:    0.1.0
    Python:      3.12.0
                 /usr/bin/python3
    Platform:    Linux 6.6  (linux)
    Repository:  /home/you/leet

  Toolchains:
    [OK]  python3     Python 3.12.0
              python: /usr/bin/python3
    [OK]  java        OpenJDK Runtime Environment (build 21+35)
              javac: /usr/bin/javac
              java: /usr/bin/java
    [NO]  cpp         Missing: g++, clang++, or cl.exe
              Install: apt install g++  # or: dnf install gcc-c++

----------------------------------------------------------------------
  2 of 3 toolchains ready.
```

## Exit codes

- `0` — always (`support` is a diagnostic, not a validator)

## See also

- [`run`](run.md) / [`test`](test.md) — consumers of the toolchains
  diagnosed here
