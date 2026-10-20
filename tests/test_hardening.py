import json
import os
from pathlib import Path

import pytest

from duplicate_folder_structure_detector.cli import main
from duplicate_folder_structure_detector.core import analyze


@pytest.mark.parametrize("data", [[], None, "root", 42, {"root": True}, {"root": 3}])
def test_malformed_input_is_rejected(data):
    with pytest.raises((ValueError, TypeError)):
        analyze(data)


@pytest.mark.parametrize("minimum", [True, "2", 1.5, None, -1])
def test_minimum_requires_positive_integer(tmp_path, minimum):
    with pytest.raises(ValueError, match="positive integer"):
        analyze({"root": str(tmp_path), "minimum_descendants": minimum})


@pytest.mark.parametrize("ignored", ["cache", None, [2]])
def test_ignored_names_are_typed(tmp_path, ignored):
    with pytest.raises(ValueError, match="ignored_names"):
        analyze({"root": str(tmp_path), "ignored_names": ignored})


def test_duplicate_scan_prunes_ignored_branches_and_withholds_unknown(tmp_path, monkeypatch):
    for name in ["left", "right", "unknown", "cache"]:
        (tmp_path / name / "shared").mkdir(parents=True)
    original = os.scandir
    visited = []

    def scan(path):
        visited.append(Path(path))
        if Path(path) == tmp_path / "unknown":
            raise PermissionError("synthetic")
        if Path(path) == tmp_path / "cache":
            raise AssertionError("ignored branch traversed")
        return original(path)

    monkeypatch.setattr(os, "scandir", scan)
    report = analyze({"root": str(tmp_path), "ignored_names": ["cache"]})
    assert not report["complete"]
    assert report["errors"] == [{"path": "unknown", "error": "PermissionError"}]
    assert report["unknown_directories"] == [".", "unknown"]
    assert report["duplicate_groups"][0]["directories"] == ["left", "right"]
    assert tmp_path / "cache" not in visited
    assert report["directories_scanned"] == 6


def test_entry_stat_failure_retains_uncertainty(tmp_path, monkeypatch):
    class Entry:
        name = "unreadable"

        def is_symlink(self):
            raise PermissionError("synthetic")

    class Scan:
        def __enter__(self):
            return iter([Entry()])

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(os, "scandir", lambda path: Scan())
    report = analyze({"root": str(tmp_path)})
    assert not report["complete"] and report["unknown_directories"] == ["."]
    assert report["errors"][0]["path"] == "unreadable"


def test_duplicate_scan_symlinks(tmp_path):
    (tmp_path / "real" / "nested").mkdir(parents=True)
    link = tmp_path / "link"
    try:
        link.symlink_to(tmp_path / "real", target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError, match="non-symlink"):
        analyze({"root": str(link)})
    report = analyze({"root": str(tmp_path)})
    assert report["skipped_symlinks"] == ["link"] and report["complete"]


def test_cli_incomplete_and_exclusive_output(tmp_path, monkeypatch):
    source = tmp_path / "input.json"
    source.write_text(json.dumps({"root": str(tmp_path)}))
    monkeypatch.setattr(os, "scandir", lambda path: (_ for _ in ()).throw(PermissionError()))
    assert main([str(source), "--format", "json"]) == 1
    output = tmp_path / "report.json"
    assert main([str(source), "--output", str(output)]) == 1
    assert not json.loads(source.read_text()).get("modified")
    assert main([str(source), "--output", str(output)]) == 2


def test_report_creation_race(tmp_path, monkeypatch):
    source = tmp_path / "input.json"
    source.write_text(json.dumps({"root": str(tmp_path)}))
    output = tmp_path / "raced.json"
    original = Path.open

    def raced(path, mode="r", *args, **kwargs):
        if path == output and mode == "x":
            with original(path, "w") as stream:
                stream.write("keep")
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", raced)
    assert main([str(source), "--output", str(output)]) == 2
    assert output.read_text() == "keep"
