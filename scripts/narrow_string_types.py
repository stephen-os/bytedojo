"""
One-time corpus correction: narrow STRING types to CHAR where the data allows.

Some bundles were typed STRING / STRING_ARRAY / STRING_MATRIX during the
initial migration even though every value is a single-character string —
LeetCode's actual signature for those problems uses `char[][]` / `vector<
vector<char>>`. The dataset stored '1' / '0' as 1-char strings rather
than chars, and the migration trusted the string shape.

Result: Java's user-side `char[][] grid` signature gets fed
`String[][]` by the runner and the `narrowTo` boundary fails;
C++'s `vector<vector<char>>&` won't even compile against the
runner's generated `vector<vector<string>>` argument.

Rule per slot (each param + return considered independently):

  - Collect every value in that slot across all cases.
  - If every value is either `null` or a single-character string,
    narrow STRING* → CHAR*.
  - Otherwise leave the slot alone.

No case drops, no value rewrites. The values themselves are already
in the right shape — CHAR is encoded as a 1-character string in
cases.json anyway. Only the type annotation changes.

Usage:
    python scripts/narrow_string_types.py --dry-run    # report only
    python scripts/narrow_string_types.py              # write
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

#: Map of wide type -> narrow type for the STRING → CHAR family.
WIDEN_MAP = {
    "STRING":        "CHAR",
    "STRING_ARRAY":  "CHAR_ARRAY",
    "STRING_MATRIX": "CHAR_MATRIX",
}


def is_char_compatible(value: Any) -> bool:
    """Recursive check: is every leaf null or a single-character string?"""
    if value is None:
        return True
    if isinstance(value, str):
        return len(value) == 1
    if isinstance(value, list):
        return all(is_char_compatible(v) for v in value)
    return False


def slot_values(bundle: dict, slot_name: str, is_return: bool) -> List[Any]:
    """Collect every value for a named slot across all cases."""
    if is_return:
        return [c.get("expected") for c in bundle["cases"]]
    return [c["input"].get(slot_name) for c in bundle["cases"]]


def narrow_bundle(bundle: dict) -> Optional[dict]:
    """Apply narrowing in place. Returns a stat dict, or None if nothing changed."""
    sig = bundle["signature"]
    narrowed_slots: List[Tuple[str, str, str]] = []  # (slot, before, after)

    for p in sig["params"]:
        if p["type"] not in WIDEN_MAP:
            continue
        if all(is_char_compatible(v) for v in slot_values(bundle, p["name"], False)):
            before = p["type"]
            p["type"] = WIDEN_MAP[before]
            narrowed_slots.append((p["name"], before, p["type"]))

    if sig["returns"] in WIDEN_MAP:
        if all(is_char_compatible(v) for v in slot_values(bundle, "expected", True)):
            before = sig["returns"]
            sig["returns"] = WIDEN_MAP[before]
            narrowed_slots.append(("expected", before, sig["returns"]))

    if not narrowed_slots:
        return None
    return {"narrowed_slots": narrowed_slots}


# ---------------------------------------------------------------------------
# Compact JSON output (mirrors the migration so diffs stay clean)
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

    total = 0
    narrowed = 0
    per_kind: Dict[str, int] = {}
    notable: List[Tuple[int, dict]] = []

    for path in paths:
        if not path.exists():
            print(f"  skip: {path.name} not found", file=sys.stderr)
            continue
        total += 1
        bundle = json.loads(path.read_text(encoding="utf-8"))
        result = narrow_bundle(bundle)
        if result is None:
            continue

        narrowed += 1
        for _, before, _after in result["narrowed_slots"]:
            per_kind[before] = per_kind.get(before, 0) + 1
        notable.append((int(path.stem), result))

        if not args.dry_run:
            path.write_text(dump_compact(bundle), encoding="utf-8")

    print(f"Total bundles scanned: {total}")
    print(f"Narrowed (STRING* -> CHAR*): {narrowed}")
    for kind, n in sorted(per_kind.items()):
        print(f"  {kind:<15s} {n}")
    print()
    print("Narrowed problems:")
    for pid, r in sorted(notable):
        slots_desc = ", ".join(
            f"{name}: {before} -> {after}"
            for name, before, after in r["narrowed_slots"]
        )
        print(f"  #{pid:>5d}  {slots_desc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
