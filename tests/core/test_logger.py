"""Tests for the bytedojo logger module."""

import logging
import re

import pytest

from bytedojo.core import logger as logger_mod
from bytedojo.core.logger import (
    LoggerFormatter,
    Theme,
    get_config,
    get_logger,
    setup_logger,
)


# --------------------------------------------------------------------------- #
# Theme — ANSI color sentinels                                                #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("attr", [
    "RED", "GREEN", "YELLOW", "BLUE", "PURPLE", "AQUA", "ORANGE", "GRAY",
    "BOLD", "RESET",
])
def test_theme_constants_are_ansi_strings(attr):
    """Every named attribute is a non-empty ANSI escape sequence."""
    value = getattr(Theme, attr)
    assert isinstance(value, str)
    assert value.startswith("\033[")


def test_theme_reset_is_ansi_reset():
    assert Theme.RESET == "\033[0m"


# --------------------------------------------------------------------------- #
# get_config                                                                  #
# --------------------------------------------------------------------------- #

def test_get_config_debug_uses_detailed_format():
    cfg = get_config(debug=True)
    assert cfg["handlers"]["console"]["level"] == "DEBUG"
    assert cfg["handlers"]["console"]["formatter"] == "detailed"
    assert cfg["loggers"]["bytedojo"]["level"] == "DEBUG"


def test_get_config_non_debug_uses_simple_format():
    cfg = get_config(debug=False)
    assert cfg["handlers"]["console"]["level"] == "INFO"
    assert cfg["handlers"]["console"]["formatter"] == "simple"
    assert cfg["loggers"]["bytedojo"]["level"] == "INFO"


def test_get_config_disables_existing_loggers_false():
    """Other libraries' loggers stay live — bytedojo doesn't hijack them."""
    assert get_config()["disable_existing_loggers"] is False


def test_get_config_bytedojo_logger_does_not_propagate():
    """Without propagate=False the root logger would double-print messages."""
    assert get_config()["loggers"]["bytedojo"]["propagate"] is False


# --------------------------------------------------------------------------- #
# setup_logger / get_logger                                                   #
# --------------------------------------------------------------------------- #

def test_setup_then_get_returns_a_named_logger():
    """The conftest autouse already initialised the logger; get_logger works."""
    log = get_logger()
    assert isinstance(log, logging.Logger)
    assert log.name == "bytedojo"


def test_get_logger_raises_when_uninitialised(monkeypatch):
    """Reset the module global and confirm get_logger surfaces a clear error."""
    monkeypatch.setattr(logger_mod, "_logger", None)
    with pytest.raises(RuntimeError, match="not initialized"):
        get_logger()


def test_setup_logger_can_be_called_twice():
    """Idempotent enough to call again without raising."""
    setup_logger(debug=False)
    setup_logger(debug=True)
    # After the second call we still have a working logger.
    assert get_logger() is not None


# --------------------------------------------------------------------------- #
# LoggerFormatter — colour application                                        #
# --------------------------------------------------------------------------- #

def _make_record(level: int, msg: str, *, name: str = "bytedojo") -> logging.LogRecord:
    return logging.LogRecord(
        name=name, level=level, pathname="x.py", lineno=1,
        msg=msg, args=(), exc_info=None,
    )


def test_formatter_wraps_levelname_in_color():
    """The level name comes out wrapped in its theme color + RESET."""
    fmt = LoggerFormatter("%(levelname)s")
    out = fmt.format(_make_record(logging.WARNING, "hi"))
    assert Theme.YELLOW in out
    assert Theme.RESET in out
    assert "WARNING" in out


def test_formatter_wraps_message_in_color():
    fmt = LoggerFormatter("%(message)s")
    out = fmt.format(_make_record(logging.INFO, "hello"))
    assert "hello" in out
    assert Theme.RESET in out


def test_formatter_does_not_mutate_original_record():
    """The colour wrapping is applied to a copy, not the live record."""
    record = _make_record(logging.WARNING, "hello")
    LoggerFormatter("%(message)s").format(record)
    assert record.msg == "hello"
    assert record.levelname == "WARNING"


def test_formatter_colorizes_timestamps_in_detailed_format():
    """The HH:MM:SS pattern gets the orange highlight."""
    fmt = LoggerFormatter(
        "[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )
    out = fmt.format(_make_record(logging.INFO, "tick"))
    # The detailed-format timestamp pattern is wrapped: [<ORANGE>HH:MM:SS<RESET>]
    assert re.search(rf"\[{re.escape(Theme.ORANGE)}\d{{2}}:\d{{2}}:\d{{2}}{re.escape(Theme.RESET)}\]", out)


def test_formatter_handles_unknown_level_gracefully():
    """A custom level outside the colour map still renders the message."""
    record = logging.LogRecord(
        name="bytedojo", level=25, pathname="x.py", lineno=1,
        msg="custom", args=(), exc_info=None,
    )
    record.levelname = "CUSTOM_LEVEL"
    out = LoggerFormatter("%(message)s").format(record)
    assert "custom" in out
