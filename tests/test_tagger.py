"""Tests for reqsnap.tagger."""
import pytest
from pathlib import Path

from reqsnap.tagger import (
    add_tag,
    all_tags,
    filter_by_tag,
    get_tags,
    remove_tag,
    _tags_path,
)


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    return snap_dir


def test_get_tags_empty_when_no_tags_file(snap_dir):
    assert get_tags(snap_dir, "abc123") == []


def test_add_tag_creates_tags_file(snap_dir):
    add_tag(snap_dir, "abc123", "smoke")
    assert _tags_path(snap_dir).exists()


def test_add_tag_stored_correctly(snap_dir):
    add_tag(snap_dir, "abc123", "smoke")
    assert get_tags(snap_dir, "abc123") == ["smoke"]


def test_add_tag_deduplicates(snap_dir):
    add_tag(snap_dir, "abc123", "smoke")
    add_tag(snap_dir, "abc123", "smoke")
    assert get_tags(snap_dir, "abc123") == ["smoke"]


def test_add_multiple_tags(snap_dir):
    add_tag(snap_dir, "abc123", "smoke")
    add_tag(snap_dir, "abc123", "regression")
    assert set(get_tags(snap_dir, "abc123")) == {"smoke", "regression"}


def test_remove_tag(snap_dir):
    add_tag(snap_dir, "abc123", "smoke")
    add_tag(snap_dir, "abc123", "regression")
    remove_tag(snap_dir, "abc123", "smoke")
    assert get_tags(snap_dir, "abc123") == ["regression"]


def test_remove_tag_noop_when_absent(snap_dir):
    add_tag(snap_dir, "abc123", "smoke")
    remove_tag(snap_dir, "abc123", "nonexistent")
    assert get_tags(snap_dir, "abc123") == ["smoke"]


def test_filter_by_tag_returns_matching_keys(snap_dir):
    add_tag(snap_dir, "key1", "smoke")
    add_tag(snap_dir, "key2", "regression")
    add_tag(snap_dir, "key3", "smoke")
    result = filter_by_tag(snap_dir, "smoke")
    assert set(result) == {"key1", "key3"}


def test_filter_by_tag_empty_when_none_match(snap_dir):
    add_tag(snap_dir, "key1", "smoke")
    assert filter_by_tag(snap_dir, "regression") == []


def test_all_tags_sorted_and_unique(snap_dir):
    add_tag(snap_dir, "key1", "smoke")
    add_tag(snap_dir, "key2", "regression")
    add_tag(snap_dir, "key3", "smoke")
    assert all_tags(snap_dir) == ["regression", "smoke"]


def test_all_tags_empty_directory(snap_dir):
    assert all_tags(snap_dir) == []
