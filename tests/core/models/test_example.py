"""Tests for the Example dataclass."""

from bytedojo.core.models.example import Example


# --------------------------------------------------------------------------- #
# Construction                                                                #
# --------------------------------------------------------------------------- #

def test_construct_minimal_defaults_images_to_empty_list():
    ex = Example(example_num=1, example_text="nums = [1,2], target = 3")
    assert ex.example_num == 1
    assert ex.example_text == "nums = [1,2], target = 3"
    assert ex.images == []


def test_construct_with_images():
    ex = Example(example_num=2, example_text="see figure", images=["a.png", "b.png"])
    assert ex.images == ["a.png", "b.png"]


def test_images_default_is_independent_per_instance():
    """Regression: `field(default_factory=list)` must not share state across instances."""
    a = Example(example_num=1, example_text="A")
    b = Example(example_num=2, example_text="B")
    a.images.append("a.png")
    assert b.images == []


# --------------------------------------------------------------------------- #
# __str__                                                                     #
# --------------------------------------------------------------------------- #

def test_str_format():
    ex = Example(example_num=3, example_text="x = 1")
    assert str(ex) == "Example 3: x = 1"
