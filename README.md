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
