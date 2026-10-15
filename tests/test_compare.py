import os
from pathlib import Path

import pytest

from duplicate_folder_structure_detector.core import analyze


def test_topology_diff_and_determinism(tmp_path):
    left, right = tmp_path / "a", tmp_path / "b"
    for root in (left, right):
        (root / "shared" / "nested").mkdir(parents=True)
        (root / "cache" / "ignored").mkdir(parents=True)
    (left / "only" / "deep").mkdir(parents=True)
    (right / "other").mkdir()
    (left / "file").write_text("different")
    (right / "another").write_text("files")
    data = {"compare_roots": [str(left), str(right)], "ignored_names": ["cache"]}
    report = analyze(data)
    assert report == analyze(data)
    comparison = report["comparison"]
    assert comparison["shared"] == ["shared", "shared/nested"]
    assert comparison["left_only"] == ["only", "only/deep"]
    assert comparison["right_only"] == ["other"]
    assert comparison["complete"] and not comparison["same_structure"]


def test_equal_structure_ignores_files_and_empty_roots(tmp_path):
    left, right = tmp_path / "a", tmp_path / "b"
    left.mkdir()
    right.mkdir()
    (left / "file").write_bytes(b"one")
    (right / "file").write_bytes(b"different")
    assert analyze({"compare_roots": [str(left), str(right)]})["comparison"]["same_structure"]


def test_unreadable_scan_is_incomplete(tmp_path, monkeypatch):
    left, right = tmp_path / "a", tmp_path / "b"
    left.mkdir()
    right.mkdir()
    original = os.scandir

    def denied(path):
        if Path(path) == left:
            raise PermissionError("denied fixture")
        return original(path)

    monkeypatch.setattr(os, "scandir", denied)
    comparison = analyze({"compare_roots": [str(left), str(right)]})["comparison"]
    assert comparison["same_structure"] is None and not comparison["complete"]
    assert comparison["left"]["errors"] == [{"path": ".", "error": "PermissionError"}]


def test_symlinks_are_rejected_or_skipped(tmp_path):
    left, right = tmp_path / "a", tmp_path / "b"
    left.mkdir()
    right.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(left, target_is_directory=True)
        (left / "loop").symlink_to(left, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError, match="non-symlink"):
        analyze({"compare_roots": [str(link), str(right)]})
    result = analyze({"compare_roots": [str(left), str(right)]})["comparison"]
    assert result["left"]["skipped_symlinks"] == ["loop"]
    assert result["same_structure"]


@pytest.mark.parametrize("roots", [None, [], ["one"], ["one", 2], "path"])
def test_invalid_roots(roots):
    with pytest.raises(ValueError, match="exactly two"):
        analyze({"compare_roots": roots})


def test_missing_root_and_bad_ignore(tmp_path):
    with pytest.raises(ValueError, match="existing"):
        analyze({"compare_roots": [str(tmp_path), str(tmp_path / "missing")]})
    with pytest.raises(ValueError, match="ignored_names"):
        analyze({"compare_roots": [str(tmp_path), str(tmp_path)], "ignored_names": "cache"})
