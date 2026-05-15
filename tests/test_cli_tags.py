"""Tests for reqsnap.cli_tags."""
import argparse
import pytest
from pathlib import Path

from reqsnap.tagger import add_tag
from reqsnap.cli_tags import cmd_tag_add, cmd_tag_remove, cmd_tag_list


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    d = tmp_path / "snaps"
    d.mkdir()
    return d


def _args(snap_dir: Path, **kwargs) -> argparse.Namespace:
    defaults = {"snap_dir": str(snap_dir), "key": None, "tag": None, "filter": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_tag_add_stores_tag(snap_dir, capsys):
    args = _args(snap_dir, key="abc", tag="smoke")
    cmd_tag_add(args)
    from reqsnap.tagger import get_tags
    assert get_tags(snap_dir, "abc") == ["smoke"]


def test_cmd_tag_add_prints_confirmation(snap_dir, capsys):
    args = _args(snap_dir, key="abc", tag="smoke")
    cmd_tag_add(args)
    out = capsys.readouterr().out
    assert "abc" in out and "smoke" in out


def test_cmd_tag_remove_removes_tag(snap_dir, capsys):
    add_tag(snap_dir, "abc", "smoke")
    args = _args(snap_dir, key="abc", tag="smoke")
    cmd_tag_remove(args)
    from reqsnap.tagger import get_tags
    assert get_tags(snap_dir, "abc") == []


def test_cmd_tag_list_all_tags(snap_dir, capsys):
    add_tag(snap_dir, "k1", "smoke")
    add_tag(snap_dir, "k2", "regression")
    args = _args(snap_dir)
    cmd_tag_list(args)
    out = capsys.readouterr().out
    assert "smoke" in out
    assert "regression" in out


def test_cmd_tag_list_by_key(snap_dir, capsys):
    add_tag(snap_dir, "k1", "smoke")
    args = _args(snap_dir, key="k1")
    cmd_tag_list(args)
    out = capsys.readouterr().out
    assert "smoke" in out


def test_cmd_tag_list_by_key_no_tags(snap_dir, capsys):
    args = _args(snap_dir, key="missing")
    cmd_tag_list(args)
    out = capsys.readouterr().out
    assert "No tags" in out


def test_cmd_tag_list_filter(snap_dir, capsys):
    add_tag(snap_dir, "k1", "smoke")
    add_tag(snap_dir, "k2", "regression")
    args = _args(snap_dir, filter="smoke")
    cmd_tag_list(args)
    out = capsys.readouterr().out
    assert "k1" in out
    assert "k2" not in out


def test_cmd_tag_list_empty(snap_dir, capsys):
    args = _args(snap_dir)
    cmd_tag_list(args)
    out = capsys.readouterr().out
    assert "No tags found" in out
