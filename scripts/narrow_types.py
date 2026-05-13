"""
One-time corpus correction: narrow INT64 types where the data allows.

Background: the initial migration bumped some bundles to INT64 because a
handful of outlier cases exceeded int32, even though LeetCode's stated
signature for those problems is `int` / `int[]` and the bulk of the
cases fit int32. This pass narrows the type to INT32 and drops the
outlier cases (which violated LeetCode's stated constraints anyway).

Decision rule per bundle:

  - For each INT64 / INT64_ARRAY / INT64_MATRIX slot (params + return),
    compute the set of cases where any value in that slot doesn't fit
    int32.
  - If the union of those bad cases is empty -> narrow losslessly.
  - Else if dropping them keeps >50% of the bundle's cases -> drop
    them and narrow.
  - Else keep the wide type (the problem genuinely needs int64).

Usage:
    python scripts/narrow_types.py --dry-run    # report only
    python scripts/narrow_types.py              # write
"""
from __future__ import annotations

import sys
sys.set_int_max_str_digits(10000)

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = ROOT / "data" / "tests"

INT32_MAX = 2**31 - 1
INT32_MIN = -2**31

#: Map of wide type -> narrow type. Restricted to int widening so we
#: don't accidentally narrow FLOAT64 or other families.
WIDEN_MAP = {
    "INT64": "INT32",
    "INT64_ARRAY": "INT32_ARRAY",
    "INT64_MATRIX": "INT32_MATRIX",
}

#: Threshold: keep the wide type if narrowing would drop >50% of cases.
#: That's the rough heuristic for "this problem genuinely needs int64."
KEEP_WIDE_THRESHOLD = 0.5


def fits_int32(value: Any) -> bool:
    """Recursive check: does this JSON value fit in int32 at every leaf?"""
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, int):
        return INT32_MIN <= value <= INT32_MAX
    if isinstance(value, list):
        return all(fits_int32(v) for v in value)
    # str / float / dict — not in the int family, doesn't apply
    return True


def slots_to_check(bundle: dict) -> List[Tuple[str, str, bool]]:
    """Return [(name, wide_type, is_return)] for every INT64-family slot."""
    sig = bundle["signature"]
    out: List[Tuple[str, str, bool]] = []
    for p in sig["params"]:
        if p["type"] in WIDEN_MAP:
            out.append((p["name"], p["type"], False))
    if sig["returns"] in WIDEN_MAP:
        out.append(("expected", sig["returns"], True))
    return out


def value_for(case: dict, name: str, is_return: bool) -> Any:
    if is_return:
        return case.get("expected")
    return case.get("input", {}).get(name)


def narrow_bundle(bundle: dict) -> Optional[dict]:
    """
    Apply narrowing rules in place. Returns a stat dict or None if the
    bundle has no INT64 slots to consider.
    """
    slots = slots_to_check(bundle)
    if not slots:
        return None

    cases: List[dict] = bundle["cases"]
    drop_indices: List[int] = []
    for i, case in enumerate(cases):
        for name, _, is_return in slots:
            if not fits_int32(value_for(case, name, is_return)):
                drop_indices.append(i)
                break

    dropped = len(drop_indices)
    total = len(cases)
    kept = total - dropped

    if dropped == 0:
        # Lossless narrow — every value already fits int32.
        _apply_narrow(bundle)
        return {
            "action": "narrowed_lossless",
            "kept": kept,
            "dropped": 0,
            "total": total,
        }

    if kept == 0 or (kept / total) < KEEP_WIDE_THRESHOLD:
        # Too many bad cases — the problem really wants the wider type.
        return {
            "action": "kept_wide",
            "kept": total,
            "dropped": 0,
            "total": total,
            "would_drop": dropped,
        }

    # Narrow + drop the outliers.
    drop_set = set(drop_indices)
    bundle["cases"] = [c for i, c in enumerate(cases) if i not in drop_set]
    _apply_narrow(bundle)
    return {
        "action": "narrowed_with_drops",
        "kept": kept,
        "dropped": dropped,
        "total": total,
    }


def _apply_narrow(bundle: dict) -> None:
    """Rewrite the bundle's signature types using WIDEN_MAP."""
    sig = bundle["signature"]
    for p in sig["params"]:
        if p["type"] in WIDEN_MAP:
            p["type"] = WIDEN_MAP[p["type"]]
    if sig["returns"] in WIDEN_MAP:
        sig["returns"] = WIDEN_MAP[sig["returns"]]


# ---------------------------------------------------------------------------
# Compact JSON output (scalar arrays inline, dicts multi-line)
# Mirrors the format used by the original migration so diffs stay clean.
# ---------------------------------------------------------------------------

def _is_scalar(v: Any) -> bool:
    return v is None or isinstance(v, (str, int, float, bool))


def _dump(v: Any, indent: int = 0, step: str = "  ") -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return json.dumps(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        if not v:
            return "[]"
        if all(_is_scalar(x) for x in v):
            return "[" + ", ".join(_dump(x, indent, step) for x in v) + "]"
        pad = step * (indent + 1)
        close = step * indent
        parts = [_dump(x, indent + 1, step) for x in v]
        return "[\n" + ",\n".join(pad + p for p in parts) + "\n" + close + "]"
    if isinstance(v, dict):
        if not v:
            return "{}"
        pad = step * (indent + 1)
        close = step * indent
        parts = []
        for k, val in v.items():
            parts.append(f"{pad}{json.dumps(k, ensure_ascii=False)}: "
                         f"{_dump(val, indent + 1, step)}")
        return "{\n" + ",\n".join(parts) + "\n" + close + "}"
    return json.dumps(v, ensure_ascii=False)


def dump_compact(obj: Any) -> str:
    return _dump(obj) + "\n"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true",
                   help="Report what would change without writing files.")
    p.add_argument("--problem", type=int, default=None,
                   help="Process one problem only (by id).")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    if args.problem is not None:
        paths = [TESTS_DIR / f"{args.problem}.json"]
    else:
        paths = sorted(TESTS_DIR.glob("*.json"))

    stats = {
        "total": 0,
        "no_int64": 0,
        "narrowed_lossless": 0,
        "narrowed_with_drops": 0,
        "kept_wide": 0,
        "total_dropped_cases": 0,
    }
    notable: List[Tuple[int, dict]] = []

    for path in paths:
        if not path.exists():
            print(f"  skip: {path.name} not found", file=sys.stderr)
            continue
        stats["total"] += 1
        bundle = json.loads(path.read_text(encoding="utf-8"))
        result = narrow_bundle(bundle)

        if result is None:
            stats["no_int64"] += 1
            continue

        action = result["action"]
        if action == "narrowed_lossless":
            stats["narrowed_lossless"] += 1
        elif action == "narrowed_with_drops":
            stats["narrowed_with_drops"] += 1
            stats["total_dropped_cases"] += result["dropped"]
        elif action == "kept_wide":
            stats["kept_wide"] += 1

        if action in ("narrowed_with_drops", "kept_wide"):
            notable.append((int(path.stem), result))

        if not args.dry_run and action in (
            "narrowed_lossless", "narrowed_with_drops"
        ):
            path.write_text(dump_compact(bundle), encoding="utf-8")

    print(f"Total bundles scanned:       {stats['total']}")
    print(f"No INT64 in signature:       {stats['no_int64']}")
    print(f"Narrowed (lossless):         {stats['narrowed_lossless']}")
    print(f"Narrowed (with case drops):  {stats['narrowed_with_drops']}")
    print(f"Kept wide (would lose >50%): {stats['kept_wide']}")
    print(f"Total cases dropped:         {stats['total_dropped_cases']}")
    print()
    print(f"Notable problems (drops or kept-wide):")
    for pid, r in sorted(notable, key=lambda x: -(x[1].get("dropped", x[1].get("would_drop", 0)))):
        dropped = r.get("dropped", r.get("would_drop", 0))
        print(f"  #{pid:>5d}  action={r['action']:<22s} "
              f"kept={r['kept']:>4d} dropped={dropped:>3d} total={r['total']:>4d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
