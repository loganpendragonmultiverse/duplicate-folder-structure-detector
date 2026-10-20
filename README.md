# Duplicate Folder Structure Detector

[![CI](https://github.com/loganpendragonmultiverse/duplicate-folder-structure-detector/actions/workflows/ci.yml/badge.svg)](https://github.com/loganpendragonmultiverse/duplicate-folder-structure-detector/actions/workflows/ci.yml)

Find repeated directory trees even when the files inside them differ. The command uses explicit UTF-8 JSON input and produces reviewable JSON or Markdown output.

## Three-minute start

```bash
python -m pip install .
duplicate-trees examples/sample.json
duplicate-trees examples/sample.json --format json --output report.json
```

The example documents the input shape. Version 1.1 accepts `ignored_names` and `minimum_descendants`, then includes deterministic structural fingerprints and descendant counts in each duplicate group. Existing report files are never overwritten. Source inputs are read-only except where the documented purpose explicitly creates a new output artifact.

## Privacy and platforms

The tool runs locally and does not upload input or include telemetry. Python 3.10 or newer is supported on Windows, macOS, and Linux.

## Interpretation boundary

The signature compares directory topology only. Similar trees can be intentional, and file contents and names are not treated as duplicates.

## Development

```bash
python -m pip install -e ".[dev]"
ruff format --check .
ruff check .
mypy src
pytest
python -m build
```

The project is feature-complete for its documented v1 scope. Maintenance focuses on correctness, security, compatibility, and well-supported input improvements.

Part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Licensed under the [MIT License](LICENSE).

## Explain two directory trees (1.2)

Supply compare_roots with exactly two explicit directory paths instead of root:
    {"compare_roots": ["/books/edition-a", "/books/edition-b"], "ignored_names": ["cache"]}
The comparison lists shared, left_only, and right_only relative directory paths
in sorted order. Files and their contents are ignored: equal topology is never
a content-duplicate claim. Built-in and custom ignored names prune whole branches.
Symlink roots are rejected; descendant symlinks are skipped and reported.
Unreadable scans include errors and complete: false, with same_structure: null.
Differences in incomplete reports describe observed paths only and may be incomplete.
Source directories and files are never modified.

## Incomplete scans and safe reports

Both duplicate detection and two-root comparison prune ignored branches before
reading them, reject symlink roots, and skip descendant symlinks. Unreadable paths
appear in `errors`; `complete` is false and the command exits with status 1.
Duplicate detection lists affected parent trees in `unknown_directories` and
withholds their duplicate claims; fully observed sibling trees can still match.
`directories_scanned` counts all observed directories including the selected root.
`minimum_descendants` must be a positive integer, and `ignored_names` an array of
strings. Reports use exclusive creation, preserving existing files and dangling
symlinks. See [TESTING.md](TESTING.md).
