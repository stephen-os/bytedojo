"""
Whole-corpus validation for the bundled problem data.

Checks EVERY bundled item — deliberately not part of the pytest suite
(it takes a while and validates data, not code). Run it manually after
touching anything under src/bytedojo/data/:

    python scripts/validate_data.py

Checks:
  - index.json parses and its id set exactly matches both problems/ and
    tests/ (id-set consistency, §6.4)
  - every problems/<id>.json parses, carries the required fields, and
    its signature types are in the type vocabulary
  - every tests/<id>.json parses, has the supported schema_version, a
    known comparison mode, a method name that is a valid identifier,
    and a signature whose params are uniquely named
  - every param/return type flattens through the runtime's _canonical()
    and every case value is accepted by parse_value() — i.e. the whole
    corpus is actually convertible by the Python runner

Exits non-zero on any failure and prints a summary either way.
"""

import json
import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from bytedojo.runtime.python3.converters import _canonical, parse_value  # noqa: E402

DATA_DIR = REPO_ROOT / "src" / "bytedojo" / "data"

#: Flat canonical scalars parse_value understands (containers are derived).
_SCALARS = {
    "INT32",
    "INT64",
    "FLOAT64",
    "BOOL",
    "CHAR",
    "STRING",
    "VOID",
    "TREE_NODE",
    "LIST_NODE",
}
_COMPARISONS = {"exact", "unordered_all", "unordered_outer"}
_DIFFICULTIES = {"Easy", "Medium", "Hard"}
_PROBLEM_REQUIRED_FIELDS = (
    "id",
    "title",
    "slug",
    "difficulty",
    "description",
    "signature",
)
_SCHEMA_VERSION = 1


def _install_node_stubs() -> None:
    """Provide tree_node/list_node modules so parse_value can build nodes.

    In real runs `dojo fetch` places these next to the solution; here we
    only need structurally-equivalent stand-ins.
    """

    class TreeNode:
        def __init__(self, val=0, left=None, right=None):
            self.val, self.left, self.right = val, left, right

    class ListNode:
        def __init__(self, val=0, next=None):
            self.val, self.next = val, next

    tree_mod = types.ModuleType("tree_node")
    tree_mod.TreeNode = TreeNode
    list_mod = types.ModuleType("list_node")
    list_mod.ListNode = ListNode
    sys.modules["tree_node"] = tree_mod
    sys.modules["list_node"] = list_mod


def _canonical_ok(type_spec) -> bool:
    """Whether a raw bundle type flattens into the supported vocabulary."""
    try:
        canonical = _canonical(type_spec)
    except (KeyError, TypeError):
        return False
    base = canonical
    while base.endswith(("_ARRAY", "_MATRIX")):
        base = base.rsplit("_", 1)[0]
    return base in _SCALARS


def _check_problem(path: Path, errors: list[str]) -> None:
    rel = path.relative_to(DATA_DIR)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        errors.append(f"{rel}: unparseable ({err})")
        return

    for field in _PROBLEM_REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"{rel}: missing field '{field}'")
    if "id" in data and str(data["id"]) != path.stem:
        errors.append(f"{rel}: id {data['id']} != filename")
    if data.get("difficulty") not in _DIFFICULTIES:
        errors.append(f"{rel}: unknown difficulty {data.get('difficulty')!r}")

    signature = data.get("signature")
    if isinstance(signature, dict):
        for param in signature.get("params", []):
            if not _canonical_ok(param.get("type")):
                errors.append(
                    f"{rel}: param type {param.get('type')!r} not in vocabulary"
                )
        if not _canonical_ok(signature.get("returns")):
            errors.append(
                f"{rel}: return type {signature.get('returns')!r} not in vocabulary"
            )
    elif signature is not None:
        errors.append(f"{rel}: signature is not an object")


def _check_bundle(path: Path, errors: list[str]) -> None:
    rel = path.relative_to(DATA_DIR)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        errors.append(f"{rel}: unparseable ({err})")
        return

    if data.get("schema_version") != _SCHEMA_VERSION:
        errors.append(
            f"{rel}: schema_version {data.get('schema_version')!r} != {_SCHEMA_VERSION}"
        )
    if str(data.get("problem_id")) != path.stem:
        errors.append(f"{rel}: problem_id {data.get('problem_id')!r} != filename")
    if data.get("comparison", "exact") not in _COMPARISONS:
        errors.append(f"{rel}: unknown comparison {data.get('comparison')!r}")

    method = data.get("method", "")
    if not isinstance(method, str) or not method.isidentifier():
        errors.append(f"{rel}: method {method!r} is not a valid identifier")

    signature = data.get("signature")
    if not isinstance(signature, dict):
        errors.append(f"{rel}: missing/invalid signature")
        return

    params = signature.get("params", [])
    names = [p.get("name") for p in params]
    if len(names) != len(set(names)) or not all(
        isinstance(n, str) and n.isidentifier() for n in names
    ):
        errors.append(f"{rel}: param names {names!r} not unique valid identifiers")

    for param in params:
        if not _canonical_ok(param.get("type")):
            errors.append(f"{rel}: param type {param.get('type')!r} not in vocabulary")
    returns = signature.get("returns")
    if not _canonical_ok(returns):
        errors.append(f"{rel}: return type {returns!r} not in vocabulary")
        return

    cases = data.get("cases", [])
    if not cases:
        errors.append(f"{rel}: bundle has zero cases")
    for case in cases:
        case_id = case.get("case_id", "?")
        for param in params:
            value = case.get("input", {}).get(param.get("name"))
            try:
                parse_value(value, param.get("type"))
            except Exception as err:  # noqa: BLE001 — report, don't crash the sweep
                errors.append(
                    f"{rel}: case {case_id} input {param.get('name')!r} "
                    f"rejected by parse_value ({err})"
                )
        try:
            parse_value(case.get("expected"), returns)
        except Exception as err:  # noqa: BLE001
            errors.append(
                f"{rel}: case {case_id} expected rejected by parse_value ({err})"
            )


def main() -> int:
    _install_node_stubs()
    errors: list[str] = []

    try:
        raw_index = json.loads((DATA_DIR / "index.json").read_text(encoding="utf-8"))
        index_ids = {int(k) for k in raw_index}
    except (OSError, ValueError) as err:
        print(f"FATAL: index.json unusable: {err}")
        return 1

    problem_files = sorted(DATA_DIR.glob("problems/*.json"))
    bundle_files = sorted(DATA_DIR.glob("tests/*.json"))
    problem_ids = {int(p.stem) for p in problem_files}
    bundle_ids = {int(p.stem) for p in bundle_files}

    for label, missing in (
        ("index ids with no problem file", index_ids - problem_ids),
        ("index ids with no test bundle", index_ids - bundle_ids),
        ("problem files not in index", problem_ids - index_ids),
        ("test bundles not in index", bundle_ids - index_ids),
    ):
        if missing:
            errors.append(
                f"id-set: {label}: {sorted(missing)[:10]}"
                + (" ..." if len(missing) > 10 else "")
            )

    for path in problem_files:
        _check_problem(path, errors)
    for path in bundle_files:
        _check_bundle(path, errors)

    print(
        f"Checked: {len(raw_index)} index entries, "
        f"{len(problem_files)} problem definitions, "
        f"{len(bundle_files)} test bundles."
    )
    if errors:
        print(f"\nFAILED — {len(errors)} problem(s):")
        for line in errors:
            print(f"  {line}")
        return 1
    print("OK — corpus is well-formed and convertible.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
