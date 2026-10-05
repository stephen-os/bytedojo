"""Tests for ConfigRepository."""

from bytedojo.core.repositories import ConfigRepository


def test_get_with_default(conn):
    config = ConfigRepository(conn)
    assert config.get("nonexistent", default="fallback") == "fallback"
    assert config.get("nonexistent") is None


def test_set_get_roundtrip(conn):
    config = ConfigRepository(conn)
    config.set("review_frequency_days", "14")
    assert config.get("review_frequency_days") == "14"


def test_set_overwrites_existing(conn):
    config = ConfigRepository(conn)
    config.set("k", "1")
    config.set("k", "2")
    assert config.get("k") == "2"


def test_all_includes_seeded_defaults(conn):
    cfg = ConfigRepository(conn).all()
    assert cfg.get("default_source") == "leetcode"
    assert "initialized_at" in cfg
