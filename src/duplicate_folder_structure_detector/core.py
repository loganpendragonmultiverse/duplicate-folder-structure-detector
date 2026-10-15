from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT = "duplicate-folder-structure-detector"


def _require(data: dict[str, Any], key: str) -> Any:
    value = data.get(key)
    if value is None or value == "" or value == []:
        raise ValueError(f"{key} is required")
    return value


def _duplicate_trees(data: dict[str, Any]) -> dict[str, Any]:
    root = Path(_require(data, "root")).resolve()
    if not root.is_dir():
        raise ValueError("root must be an existing directory")
    ignored_names = {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        *(str(name) for name in data.get("ignored_names", [])),
    }
    minimum_descendants = int(data.get("minimum_descendants", 1))
    if minimum_descendants < 1:
        raise ValueError("minimum_descendants must be positive")

    def excluded(path: Path) -> bool:
        return any(part in ignored_names for part in path.relative_to(root).parts)

    signatures: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for directory in [root, *sorted(path for path in root.rglob("*") if path.is_dir())]:
        if excluded(directory):
            continue
        descendants = tuple(
            sorted(
                path.relative_to(directory).as_posix()
                for path in directory.rglob("*")
                if path.is_dir() and not excluded(path)
            )
        )
        if len(descendants) >= minimum_descendants:
            signatures[descendants].append(directory.relative_to(root).as_posix() or ".")
    groups: list[dict[str, Any]] = [
        {
            "directories": paths,
            "structure": list(signature),
            "descendant_count": len(signature),
            "signature": hashlib.sha256("\n".join(signature).encode()).hexdigest()[:16],
        }
        for signature, paths in signatures.items()
        if len(paths) > 1
    ]
    groups.sort(key=lambda item: (-len(item["directories"]), item["directories"]))
    return {
        "duplicate_groups": groups,
        "minimum_descendants": minimum_descendants,
        "ignored_names": sorted(ignored_names),
        "directories_scanned": sum(len(paths) for paths in signatures.values()),
    }


def compare_roots(data: dict[str, Any]) -> dict[str, Any]:
    roots = data["compare_roots"]
    if (
        not isinstance(roots, list)
        or len(roots) != 2
        or not all(isinstance(p, str) and p for p in roots)
    ):
        raise ValueError("compare_roots must contain exactly two directory paths")
    custom = data.get("ignored_names", [])
    if not isinstance(custom, list) or not all(isinstance(name, str) for name in custom):
        raise ValueError("ignored_names must be an array of names")
    ignored = {".git", ".venv", "node_modules", "__pycache__", *custom}

    def scan(raw: str) -> dict[str, Any]:
        root = Path(raw)
        if root.is_symlink() or not root.is_dir():
            raise ValueError("comparison roots must be existing non-symlink directories")
        root = root.resolve()
        directories: set[str] = set()
        errors = []
        skipped = []
        pending = [root]
        while pending:
            current = pending.pop()
            try:
                with os.scandir(current) as iterator:
                    entries = sorted(iterator, key=lambda entry: entry.name)
                for entry in entries:
                    relative = (current / entry.name).relative_to(root).as_posix()
                    if entry.name in ignored:
                        continue
                    if entry.is_symlink():
                        skipped.append(relative)
                    elif entry.is_dir(follow_symlinks=False):
                        directories.add(relative)
                        pending.append(current / entry.name)
            except OSError as exc:
                errors.append(
                    {"path": current.relative_to(root).as_posix(), "error": type(exc).__name__}
                )
        return {
            "root": str(root),
            "directories": sorted(directories),
            "errors": sorted(errors, key=lambda item: item["path"]),
            "skipped_symlinks": sorted(skipped),
            "complete": not errors,
        }

    left, right = (scan(raw) for raw in roots)
    a, b = set(left["directories"]), set(right["directories"])
    complete = left["complete"] and right["complete"]
    return {
        "comparison": {
            "left": left,
            "right": right,
            "complete": complete,
            "same_structure": a == b if complete else None,
            "shared": sorted(a & b),
            "left_only": sorted(a - b),
            "right_only": sorted(b - a),
        },
        "ignored_names": sorted(ignored),
    }


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": 1,
        "project": PROJECT,
        **(compare_roots(data) if "compare_roots" in data else _duplicate_trees(data)),
    }


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [f"# {report['project'].replace('-', ' ').title()} report", ""]
    for key, value in report.items():
        if key not in {"version", "project"}:
            lines.extend(
                [
                    f"## {key.replace('_', ' ').title()}",
                    "",
                    f"```json\n{json.dumps(value, indent=2, ensure_ascii=False, default=str)}\n```",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"
