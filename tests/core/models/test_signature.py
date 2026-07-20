"""Tests for Signature — the composed type used in method signatures."""

import pytest

from bytedojo.core.models.data_structure import DataStructure
from bytedojo.core.models.primitive import Primitive
from bytedojo.core.models.signature import Signature


# --------------------------------------------------------------------------- #
# String coercion                                                             #
# --------------------------------------------------------------------------- #

def test_string_base_resolving_to_a_primitive():
    assert Signature(base="INT32").base is Primitive.INT32


def test_string_base_resolving_to_a_data_structure():
    assert Signature(base="ARRAY").base is DataStructure.ARRAY


def test_primitive_and_data_structure_vocabularies_are_disjoint():
    """
    _parse_base tries DataStructure first and falls back to Primitive. That
    order is only unambiguous while the two vocabularies share no names — add
    a name to both and a signature silently resolves to a different type.
    """
    overlap = {p.value for p in Primitive} & {d.value for d in DataStructure}
    assert overlap == set(), f"ambiguous type names: {sorted(overlap)}"


def test_base_coercion_is_case_insensitive():
    assert Signature(base="array").base is DataStructure.ARRAY
    assert Signature(base="int32").base is Primitive.INT32


def test_element_is_coerced_too():
    sig = Signature(base="ARRAY", element="INT32")
    assert sig.base is DataStructure.ARRAY
    assert sig.element is Primitive.INT32


def test_enum_members_pass_through_untouched():
    sig = Signature(base=DataStructure.MATRIX, element=Primitive.CHAR)
    assert sig.base is DataStructure.MATRIX
    assert sig.element is Primitive.CHAR


def test_element_defaults_to_none():
    assert Signature(base="INT32").element is None


def test_unparseable_base_degrades_to_unknown_without_raising():
    """
    A type string matching neither enum becomes Primitive.UNKNOWN silently.

    This is the failure mode to watch: a stale spelling like the pre-Signature
    "INT32_ARRAY" yields a valid-looking Signature that generates a wrong stub
    rather than an error.
    """
    assert Signature(base="INT32_ARRAY").base is Primitive.UNKNOWN
    assert Signature(base="nonsense").base is Primitive.UNKNOWN


def test_nested_data_structures():
    """ARRAY of LINKED_LIST — both halves resolve as structures."""
    sig = Signature(base="ARRAY", element="LINKED_LIST")
    assert sig.base is DataStructure.ARRAY
    assert sig.element is DataStructure.LINKED_LIST


# --------------------------------------------------------------------------- #
# from_dict                                                                   #
# --------------------------------------------------------------------------- #

def test_from_dict_base_only():
    """The on-disk form for a scalar param: {"base": "INT32"}."""
    sig = Signature.from_dict({"base": "INT32"})
    assert sig == Signature(base=Primitive.INT32)


def test_from_dict_with_element():
    """The on-disk form for a container: {"base": ..., "element": ...}."""
    sig = Signature.from_dict({"base": "MATRIX", "element": "CHAR"})
    assert sig == Signature(base=DataStructure.MATRIX, element=Primitive.CHAR)


def test_from_dict_ignores_unknown_keys():
    sig = Signature.from_dict({"base": "INT32", "nullable": True})
    assert sig == Signature(base=Primitive.INT32)


def test_from_dict_requires_a_base():
    with pytest.raises(KeyError):
        Signature.from_dict({"element": "INT32"})


# --------------------------------------------------------------------------- #
# __str__ / __repr__ / equality                                               #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("sig, text", [
    (Signature(base="INT32"),                    "INT32"),
    (Signature(base="LINKED_LIST"),              "LINKED_LIST"),
    (Signature(base="ARRAY", element="INT32"),   "ARRAY<INT32>"),
    (Signature(base="MATRIX", element="CHAR"),   "MATRIX<CHAR>"),
])
def test_str_renders_the_parameterized_form(sig, text):
    assert str(sig) == text


def test_repr_omits_element_when_absent():
    assert repr(Signature(base="INT32")) == "Signature(base=Primitive.INT32)"


def test_repr_includes_element_when_present():
    assert repr(Signature(base="ARRAY", element="INT32")) == (
        "Signature(base=DataStructure.ARRAY, element=Primitive.INT32)"
    )


def test_equality_is_by_value_not_identity():
    """Signature is a dataclass — compare with ==, never `is`."""
    assert Signature(base="INT32") == Signature(base=Primitive.INT32)
    assert Signature(base="ARRAY", element="INT32") != Signature(base="ARRAY")
