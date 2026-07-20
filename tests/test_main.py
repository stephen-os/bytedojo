"""Tests for the CLI entry point."""

import sys

from bytedojo.main import _force_utf8_output


_UTF8 = {"encoding": "utf-8", "errors": "replace"}


class _FakeStream:
    """Records reconfigure() calls the way a real TextIOWrapper accepts them."""

    def __init__(self):
        self.calls = []

    def reconfigure(self, **kwargs):
        self.calls.append(kwargs)


class _RaisingStream(_FakeStream):
    """A stream that refuses reconfiguration, e.g. an already-detached one."""

    def reconfigure(self, **kwargs):
        raise ValueError("cannot reconfigure")


# --------------------------------------------------------------------------- #
# _force_utf8_output                                                          #
# --------------------------------------------------------------------------- #

def test_reconfigures_both_streams_to_utf8(monkeypatch):
    """Box rules and ✓/✗ must survive a redirected cp1252 stdout."""
    out, err = _FakeStream(), _FakeStream()
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)

    _force_utf8_output()

    assert out.calls == [_UTF8]
    assert err.calls == [_UTF8]


def test_respects_explicit_pythonioencoding(monkeypatch):
    """A user who set PYTHONIOENCODING keeps the encoding they asked for."""
    out = _FakeStream()
    monkeypatch.setenv("PYTHONIOENCODING", "latin-1")
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", _FakeStream())

    _force_utf8_output()

    assert out.calls == []


def test_survives_streams_without_reconfigure(monkeypatch):
    """Captured/replaced streams may not expose reconfigure at all."""
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.setattr(sys, "stdout", object())
    monkeypatch.setattr(sys, "stderr", object())

    _force_utf8_output()   # must not raise


def test_survives_streams_that_refuse_reconfigure(monkeypatch):
    """Reconfiguration failure must not take the whole CLI down."""
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.setattr(sys, "stdout", _RaisingStream())
    monkeypatch.setattr(sys, "stderr", _RaisingStream())

    _force_utf8_output()   # must not raise
