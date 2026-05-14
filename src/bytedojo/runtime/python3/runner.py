"""
Universal Python test runner for ByteDojo.

Standalone — no bytedojo dependencies. TestService copies this file
plus converters.py into a per-problem build directory, drops the test
bundle as cases.json, and the user's solution as solution.py, then
invokes:

    python runner.py

Output is a single JSON results envelope wrapped in sentinels so any
stray `print()` from the user's solution can be discarded by the
caller. Sentinels are emitted on their own lines:

    <<<BYTEDOJO_RESULTS_BEGIN>>>
    [...JSON array of case-result objects...]
    <<<BYTEDOJO_RESULTS_END>>>

Each case-result has: case, passed, input, expected, actual, error.
"""

import json
import sys
import traceback
from pathlib import Path

from converters import compare, display, format_input, parse_value


BEGIN = "<<<BYTEDOJO_RESULTS_BEGIN>>>"
END = "<<<BYTEDOJO_RESULTS_END>>>"


def _emit(results):
    """Print the JSON results envelope wrapped in begin/end sentinels."""
    print(BEGIN)
    print(json.dumps(results))
    print(END)


def run():
    """Load cases.json, dispatch every case against Solution, emit results."""
    here = Path(__file__).resolve().parent
    bundle_path = here / "cases.json"
    if not bundle_path.exists():
        _emit([{
            "case": 0, "passed": False, "input": "", "expected": "",
            "actual": "", "error": f"cases.json not found at {bundle_path}",
        }])
        return

    with open(bundle_path, encoding="utf-8") as f:
        bundle = json.load(f)

    method_name = bundle["method"]
    params = bundle["signature"]["params"]
    return_type = bundle["signature"]["returns"]
    comparison = bundle.get("comparison", "exact")

    # Import the user's solution lazily so SyntaxError / ImportError on the
    # user side gets caught by the top-level except below and reported
    # through the results envelope (instead of crashing the module load).
    from solution import Solution
    solution = Solution()
    if not hasattr(solution, method_name):
        _emit([{
            "case": 0, "passed": False, "input": "", "expected": "",
            "actual": "",
            "error": f"Solution class has no method `{method_name}`",
        }])
        return
    method = getattr(solution, method_name)

    results = []
    for case in bundle["cases"]:
        case_id = case["case_id"]
        input_str = format_input(case["input"])
        expected_raw = case["expected"]
        try:
            # Positional args in signature order — matches both Python's
            # natural keyword binding and Java/C++ positional dispatch.
            args = [parse_value(case["input"].get(p["name"]), p["type"]) for p in params]
            expected = parse_value(expected_raw, return_type)

            actual = method(*args)

            passed = compare(actual, expected, return_type, comparison)
            results.append({
                "case": case_id,
                "passed": passed,
                "input": input_str,
                "expected": display(expected, return_type),
                "actual": display(actual, return_type),
                "error": None,
            })
        except Exception as e:
            results.append({
                "case": case_id,
                "passed": False,
                "input": input_str,
                "expected": display(expected_raw, return_type),
                "actual": "",
                "error": f"{type(e).__name__}: {e}",
            })

    _emit(results)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        # Catastrophic failure — surface it as a single case-0 error so
        # the caller's parser still sees a valid envelope.
        _emit([{
            "case": 0, "passed": False, "input": "", "expected": "",
            "actual": "",
            "error": f"runner crash: {type(e).__name__}: {e}\n{traceback.format_exc()}",
        }])
        sys.exit(1)
