# Testing

Use Python 3.10 or newer:

```bash
python -m pip install -e '.[dev]'
ruff format --check .
ruff check .
mypy src
pytest
python -m build
```

Keep the existing 90% branch-coverage gate. Synthetic fixtures cover matching and
differing trees, ignored-branch pruning, unreadable directories and entry metadata,
symlinks, malformed controls, incomplete exit status and exclusive report creation.
No source directory is changed by the tool.

Install the built wheel and source distribution separately into fresh environments
outside the checkout. Run the full suite with `pytest -o addopts='' /path/to/tests`
and verify the imported package comes from site-packages. Retain the separate
source coverage check; disabling coverage in installed acceptance does not replace
it. Smoke-test `duplicate-trees` with explicit synthetic absolute directory roots.
CI retains Linux, Windows and macOS coverage on the supported Python matrix.
