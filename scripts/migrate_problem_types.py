"""
One-shot migration: derive canonical input/output types for every problem JSON.

Reads data/problems/*.json, infers a CanonicalType for each parameter and the
return type by majority vote across the per-language type strings, and writes
the result to a top-level `types_canonical` block alongside the existing
per-language entries.

We keep the per-language `types.*` entries in place for backwards compatibility
— consumers can opt into the canonical block at their own pace, and we can
drop the legacy entries once everything reads canonical types.

Run from the project root:
    python scripts/migrate_problem_types.py
or:
    python scripts/migrate_problem_types.py --dry-run    # report-only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# Make the package importable when run directly from project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from bytedojo.core.models.canonical_type import CanonicalType  # noqa: E402


PROBLEMS_DIR = _PROJECT_ROOT / "data" / "problems"


# ----------------------------------------------------------------------------
# Per-language forward mappings — language type string → CanonicalType.
#
# Keys are normalized (whitespace stripped, C++ `&` stripped) before lookup.
# Patterns we can't recognize fall through to UNKNOWN and get logged.
# ----------------------------------------------------------------------------

JAVA: Dict[str, CanonicalType] = {
    "int": CanonicalType.INT,
    "long": CanonicalType.LONG,
    "double": CanonicalType.DOUBLE,
    "boolean": CanonicalType.BOOL,
    "char": CanonicalType.CHAR,
    "String": CanonicalType.STRING,
    "void": CanonicalType.VOID,

    "int[]": CanonicalType.INT_ARRAY,
    "long[]": CanonicalType.LONG_ARRAY,
    "double[]": CanonicalType.DOUBLE_ARRAY,
    "boolean[]": CanonicalType.BOOL_ARRAY,
    "char[]": CanonicalType.CHAR_ARRAY,
    "String[]": CanonicalType.STRING_ARRAY,

    "int[][]": CanonicalType.INT_MATRIX,
    "char[][]": CanonicalType.CHAR_MATRIX,

    "TreeNode": CanonicalType.TREE_NODE,
    "ListNode": CanonicalType.LIST_NODE,
    "ListNode[]": CanonicalType.LIST_NODE_ARRAY,

    "List<Integer>": CanonicalType.INT_ARRAY,
    "List<Long>": CanonicalType.LONG_ARRAY,
    "List<Double>": CanonicalType.DOUBLE_ARRAY,
    "List<Boolean>": CanonicalType.BOOL_ARRAY,
    "List<String>": CanonicalType.STRING_ARRAY,
    "List<List<Integer>>": CanonicalType.INT_MATRIX,
    "List<List<Long>>": CanonicalType.LONG_MATRIX,
    "List<List<String>>": CanonicalType.STRING_MATRIX,
}

CPP: Dict[str, CanonicalType] = {
    "int": CanonicalType.INT,
    "long": CanonicalType.LONG,
    "long long": CanonicalType.LONG,
    "double": CanonicalType.DOUBLE,
    "bool": CanonicalType.BOOL,
    "char": CanonicalType.CHAR,
    "string": CanonicalType.STRING,
    "void": CanonicalType.VOID,

    "vector<int>": CanonicalType.INT_ARRAY,
    "vector<long long>": CanonicalType.LONG_ARRAY,
    "vector<double>": CanonicalType.DOUBLE_ARRAY,
    "vector<bool>": CanonicalType.BOOL_ARRAY,
    "vector<char>": CanonicalType.CHAR_ARRAY,
    "vector<string>": CanonicalType.STRING_ARRAY,

    "vector<vector<int>>": CanonicalType.INT_MATRIX,
    "vector<vector<long long>>": CanonicalType.LONG_MATRIX,
    "vector<vector<char>>": CanonicalType.CHAR_MATRIX,
    "vector<vector<string>>": CanonicalType.STRING_MATRIX,

    "TreeNode*": CanonicalType.TREE_NODE,
    "ListNode*": CanonicalType.LIST_NODE,
    "vector<ListNode*>": CanonicalType.LIST_NODE_ARRAY,
}

PYTHON: Dict[str, CanonicalType] = {
    "int": CanonicalType.INT,
    "float": CanonicalType.DOUBLE,
    "bool": CanonicalType.BOOL,
    "str": CanonicalType.STRING,
    "None": CanonicalType.VOID,

    "List[int]": CanonicalType.INT_ARRAY,
    "List[float]": CanonicalType.DOUBLE_ARRAY,
    "List[bool]": CanonicalType.BOOL_ARRAY,
    "List[str]": CanonicalType.STRING_ARRAY,

    "List[List[int]]": CanonicalType.INT_MATRIX,
    "List[List[str]]": CanonicalType.STRING_MATRIX,

    "TreeNode": CanonicalType.TREE_NODE,
    "Optional[TreeNode]": CanonicalType.TREE_NODE,
    "ListNode": CanonicalType.LIST_NODE,
    "Optional[ListNode]": CanonicalType.LIST_NODE,
    "List[Optional[ListNode]]": CanonicalType.LIST_NODE_ARRAY,
}

GO: Dict[str, CanonicalType] = {
    "int": CanonicalType.INT,
    "int64": CanonicalType.LONG,
    "float64": CanonicalType.DOUBLE,
    "bool": CanonicalType.BOOL,
    "byte": CanonicalType.CHAR,
    "string": CanonicalType.STRING,

    "[]int": CanonicalType.INT_ARRAY,
    "[]int64": CanonicalType.LONG_ARRAY,
    "[]float64": CanonicalType.DOUBLE_ARRAY,
    "[]bool": CanonicalType.BOOL_ARRAY,
    "[]byte": CanonicalType.CHAR_ARRAY,
    "[]string": CanonicalType.STRING_ARRAY,

    "[][]int": CanonicalType.INT_MATRIX,
    "[][]int64": CanonicalType.LONG_MATRIX,
    "[][]byte": CanonicalType.CHAR_MATRIX,
    "[][]string": CanonicalType.STRING_MATRIX,

    "*TreeNode": CanonicalType.TREE_NODE,
    "*ListNode": CanonicalType.LIST_NODE,
    "[]*ListNode": CanonicalType.LIST_NODE_ARRAY,
}

RUST: Dict[str, CanonicalType] = {
    "i32": CanonicalType.INT,
    "i64": CanonicalType.LONG,
    "f64": CanonicalType.DOUBLE,
    "bool": CanonicalType.BOOL,
    "char": CanonicalType.CHAR,
    "String": CanonicalType.STRING,
    "()": CanonicalType.VOID,

    "Vec<i32>": CanonicalType.INT_ARRAY,
    "Vec<i64>": CanonicalType.LONG_ARRAY,
    "Vec<f64>": CanonicalType.DOUBLE_ARRAY,
    "Vec<bool>": CanonicalType.BOOL_ARRAY,
    "Vec<char>": CanonicalType.CHAR_ARRAY,
    "Vec<String>": CanonicalType.STRING_ARRAY,

    "Vec<Vec<i32>>": CanonicalType.INT_MATRIX,
    "Vec<Vec<i64>>": CanonicalType.LONG_MATRIX,
    "Vec<Vec<char>>": CanonicalType.CHAR_MATRIX,
    "Vec<Vec<String>>": CanonicalType.STRING_MATRIX,

    "Option<Rc<RefCell<TreeNode>>>": CanonicalType.TREE_NODE,
    "Option<Box<ListNode>>": CanonicalType.LIST_NODE,
    "Vec<Option<Box<ListNode>>>": CanonicalType.LIST_NODE_ARRAY,
}

# JS/TS `number` is ambiguous between INT and DOUBLE — we map to INT by
# default and let Java/C++/Rust's stricter type override it during majority
# vote when they disagree.
JAVASCRIPT: Dict[str, CanonicalType] = {
    "number": CanonicalType.INT,
    "string": CanonicalType.STRING,
    "boolean": CanonicalType.BOOL,
    "void": CanonicalType.VOID,

    "number[]": CanonicalType.INT_ARRAY,
    "string[]": CanonicalType.STRING_ARRAY,
    "boolean[]": CanonicalType.BOOL_ARRAY,

    "number[][]": CanonicalType.INT_MATRIX,
    "string[][]": CanonicalType.STRING_MATRIX,

    "TreeNode": CanonicalType.TREE_NODE,
    "ListNode": CanonicalType.LIST_NODE,
    "ListNode[]": CanonicalType.LIST_NODE_ARRAY,
}

TYPESCRIPT: Dict[str, CanonicalType] = {
    **JAVASCRIPT,
    "TreeNode | null": CanonicalType.TREE_NODE,
    "ListNode | null": CanonicalType.LIST_NODE,
    "Array<ListNode | null>": CanonicalType.LIST_NODE_ARRAY,
}


LANGUAGE_MAPS = {
    "java":       JAVA,
    "cpp":        CPP,
    "python3":    PYTHON,
    "golang":     GO,
    "rust":       RUST,
    "javascript": JAVASCRIPT,
    "typescript": TYPESCRIPT,
}


# ----------------------------------------------------------------------------
# Inference
# ----------------------------------------------------------------------------

def _normalize(lang: str, raw: str) -> str:
    """Strip whitespace; for C++ also strip a trailing `&` (reference)."""
    s = (raw or "").strip()
    if lang == "cpp" and s.endswith("&"):
        s = s[:-1].rstrip()
    return s


def lookup(lang: str, raw: str) -> CanonicalType:
    """Map a single language type string to its canonical form."""
    table = LANGUAGE_MAPS.get(lang)
    if table is None:
        return CanonicalType.UNKNOWN
    return table.get(_normalize(lang, raw), CanonicalType.UNKNOWN)


def majority(votes: Iterable[CanonicalType]) -> CanonicalType:
    """
    Pick the most common non-UNKNOWN canonical type from a set of language
    votes. Ties go to the more specific type (more specific wins arbitrarily
    via Counter ordering, which is stable in insertion order).
    """
    counts = Counter(v for v in votes if v != CanonicalType.UNKNOWN)
    if not counts:
        return CanonicalType.UNKNOWN
    return counts.most_common(1)[0][0]


# ----------------------------------------------------------------------------
# Per-problem migration
# ----------------------------------------------------------------------------

def derive_canonical_types(types_block: dict) -> Optional[dict]:
    """
    Given a problem's `types` block (per-language input/output strings),
    return a canonical {"input": [{name: CANONICAL}, ...], "output": "CANONICAL"}.
    Returns None when there's no usable input data.
    """
    # Collect input params by position across all languages. Names should
    # match across langs but be defensive — use the position as the key
    # and capture the name from whichever language sees it first.
    input_votes: Dict[int, Dict[str, List[CanonicalType]]] = {}
    output_votes: List[CanonicalType] = []

    for lang, lang_types in (types_block or {}).items():
        if not isinstance(lang_types, dict):
            continue

        inputs = lang_types.get("input") or []
        for idx, param_dict in enumerate(inputs):
            if not isinstance(param_dict, dict):
                continue
            for name, raw_type in param_dict.items():
                slot = input_votes.setdefault(idx, {"name": name, "votes": []})
                slot["votes"].append(lookup(lang, raw_type))

        out = lang_types.get("output")
        if out:
            output_votes.append(lookup(lang, out))

    if not input_votes and not output_votes:
        return None

    canonical_input = []
    for idx in sorted(input_votes.keys()):
        slot = input_votes[idx]
        canonical = majority(slot["votes"])
        canonical_input.append({slot["name"]: canonical.value})

    canonical_output = majority(output_votes).value if output_votes else ""

    return {"input": canonical_input, "output": canonical_output}


def migrate_file(path: Path, *, dry_run: bool) -> dict:
    """
    Migrate a single problem file. Returns a small report dict for logging.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    types_block = data.get("types") or {}
    canonical = derive_canonical_types(types_block)

    if canonical is None:
        return {"path": path.name, "skipped": True}

    # Skip if already migrated and unchanged.
    if data.get("types_canonical") == canonical:
        return {"path": path.name, "unchanged": True, "canonical": canonical}

    data["types_canonical"] = canonical

    if not dry_run:
        # Preserve original key order by writing in place
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return {"path": path.name, "migrated": True, "canonical": canonical}


# ----------------------------------------------------------------------------
# Entry point + summary reporting
# ----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report what would change without writing the JSON files.",
    )
    parser.add_argument(
        "--problems-dir", type=Path, default=PROBLEMS_DIR,
        help=f"Directory of problem JSON files (default: {PROBLEMS_DIR})",
    )
    args = parser.parse_args()

    files = sorted(p for p in args.problems_dir.glob("*.json") if p.name != "index.json")
    if not files:
        print(f"No problem files found under {args.problems_dir}", file=sys.stderr)
        return 1

    print(f"Scanning {len(files)} problem files (dry_run={args.dry_run})...")

    migrated = 0
    unchanged = 0
    skipped = 0
    unknown_examples: Dict[str, List[str]] = {}

    for path in files:
        report = migrate_file(path, dry_run=args.dry_run)
        if report.get("migrated"):
            migrated += 1
        elif report.get("unchanged"):
            unchanged += 1
        elif report.get("skipped"):
            skipped += 1

        # Track which problems still have UNKNOWN canonicals so the user
        # can decide whether to extend the mappings.
        canonical = report.get("canonical")
        if canonical:
            for slot in canonical.get("input", []):
                for name, t in slot.items():
                    if t == CanonicalType.UNKNOWN.value:
                        unknown_examples.setdefault("input", []).append(
                            f"  {path.name}: {name}"
                        )
            if canonical.get("output") == CanonicalType.UNKNOWN.value:
                unknown_examples.setdefault("output", []).append(f"  {path.name}")

    print()
    print(f"Migrated:  {migrated}")
    print(f"Unchanged: {unchanged}")
    print(f"Skipped:   {skipped}")

    if unknown_examples:
        print()
        print("Problems with UNKNOWN canonical types (extend the mappings if needed):")
        for kind, lines in unknown_examples.items():
            head = lines[:5]
            print(f"  [{kind}] {len(lines)} occurrences, first {len(head)}:")
            for line in head:
                print(f"    {line}")
            if len(lines) > len(head):
                print(f"    ... and {len(lines) - len(head)} more")

    return 0


if __name__ == "__main__":
    sys.exit(main())
