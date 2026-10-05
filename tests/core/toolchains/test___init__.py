"""Tests for the toolchain registry (core/toolchains/__init__.py)."""

from bytedojo.core.models.code_language import CodeLanguage
from bytedojo.core.toolchains import (
    PythonToolchain,
    Toolchain,
    all_toolchains,
    get_toolchain,
)


# --------------------------------------------------------------------------- #
# get_toolchain                                                               #
# --------------------------------------------------------------------------- #

def test_get_toolchain_returns_python_toolchain():
    tc = get_toolchain(CodeLanguage.PYTHON)
    assert isinstance(tc, PythonToolchain)
    assert tc.language is CodeLanguage.PYTHON


def test_get_toolchain_unsupported_language_returns_none():
    """Only Python is wired; every other language has no registered toolchain."""
    assert get_toolchain(CodeLanguage.JAVA) is None
    assert get_toolchain(CodeLanguage.CPP) is None
    assert get_toolchain(CodeLanguage.RUST) is None
    assert get_toolchain(CodeLanguage.GO) is None
    assert get_toolchain(CodeLanguage.JAVASCRIPT) is None
    assert get_toolchain(CodeLanguage.UNKNOWN) is None


def test_get_toolchain_returns_fresh_instances():
    """Each call constructs a new instance — toolchains are stateless."""
    a = get_toolchain(CodeLanguage.PYTHON)
    b = get_toolchain(CodeLanguage.PYTHON)
    assert a is not b


# --------------------------------------------------------------------------- #
# all_toolchains                                                              #
# --------------------------------------------------------------------------- #

def test_all_toolchains_returns_one_per_registered_language():
    instances = all_toolchains()
    assert len(instances) == 1
    languages = {tc.language for tc in instances}
    assert languages == {CodeLanguage.PYTHON}


def test_all_toolchains_returns_concrete_subclasses_of_toolchain():
    for tc in all_toolchains():
        assert isinstance(tc, Toolchain)
