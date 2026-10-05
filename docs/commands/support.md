# `dojo support`

> Environment + toolchain diagnostic report.

## Synopsis

```
dojo support
```

## Description

Prints the ByteDojo version, the Python interpreter dojo is running
under (with a warning if it's older than the supported 3.10), the OS,
the repository it found (if any), and the detection status of every
registered language toolchain.

Purely diagnostic: it never fails, so you can always attach its output
to a bug report.

## Examples

```bash
dojo support
```

```
  ByteDojo Support
  ──────────────────────────────────────────────────────
  Environment
    ByteDojo    0.1.0
    Python      3.12.4
    Platform    Windows 11  win32
    Repository  C:\code\practice

  Toolchains
    [OK]  python3   3.12.4

  All 1 toolchains ready.
```

## See also

- [`init`](init.md) — create the repository `support` looks for
