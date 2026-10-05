"""Tests for the Example dataclass."""

from bytedojo.core.models.example import Example


def test_construct():
    ex = Example(example_num=1, example_text="nums = [1,2], target = 3")
    assert ex.example_num == 1
    assert ex.example_text == "nums = [1,2], target = 3"


def test_str_format():
    ex = Example(example_num=3, example_text="x = 1")
    assert str(ex) == "Example 3: x = 1"
