from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT = "duplicate-folder-structure-detector"


def _ignored_names(data: dict[str, Any]) -> set[str]:
    custom = data.get("ignored_names", [])
    if not isinstance(custom, list) or not all(isinstance(name, str) for name in custom):
        raise ValueError("ignored_names must be an array of names")
    return {".git", ".venv", "node_modules", "__pycache__", *custom}


def _scan_directories(raw: str, ignored: set[str]) -> dict[str, Any]:
    root = Path(raw)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("roots must be existing non-symlink directories")
    root = root.resolve()
    directories: set[str] = set()
    errors: list[dict[str, str]] = []
    skipped: list[str] = []
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            with os.scandir(current) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError as exc:
            errors.append(
                {"path": current.relative_to(root).as_posix(), "error": type(exc).__name__}
            )
            continue
        for entry in entries:
            relative = (current / entry.name).relative_to(root).as_posix()
            if entry.name in ignored:
                continue
            try:
                if entry.is_symlink():
                    skipped.append(relative)
                elif entry.is_dir(follow_symlinks=False):
                    directories.add(relative)
                    pending.append(current / entry.name)
            except OSError as exc:
                errors.append({"path": relative, "error": type(exc).__name__})
    return {
        "root": str(root),
        "directories": sorted(directories),
        "errors": sorted(errors, key=lambda item: item["path"]),
        "skipped_symlinks": sorted(skipped),
        "complete": not errors,
    }


def _duplicate_trees(data: dict[str, Any]) -> dict[str, Any]:
    raw = data.get("root")
    if not isinstance(raw, str) or not raw:
        raise ValueError("root must be a directory path")
    ignored_names = _ignored_names(data)
    minimum_descendants = data.get("minimum_descendants", 1)
    if type(minimum_descendants) is not int or minimum_descendants < 1:
        raise ValueError("minimum_descendants must be a positive integer")
    scan = _scan_directories(raw, ignored_names)
    root = Path(scan["root"])
    directories = [root, *(root / name for name in scan["directories"])]
    failed = [root / error["path"] for error in scan["errors"]]
    signatures: dict[tuple[str, ...], list[str]] = defaultdict(list)
    unknown: list[str] = []
    for directory in directories:
        if any(path == directory or directory in path.parents for path in failed):
            unknown.append(directory.relative_to(root).as_posix())
            continue
        descendants = tuple(
            sorted(
                path.relative_to(directory).as_posix()
                for path in directories
                if directory in path.parents
            )
        )
        if len(descendants) >= minimum_descendants:
            signatures[descendants].append(directory.relative_to(root).as_posix())
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
        "directories_scanned": len(directories),
        "errors": scan["errors"],
        "skipped_symlinks": scan["skipped_symlinks"],
        "unknown_directories": sorted(unknown),
        "complete": scan["complete"],
    }


def compare_roots(data: dict[str, Any]) -> dict[str, Any]:
    roots = data["compare_roots"]
    if (
        not isinstance(roots, list)
        or len(roots) != 2
        or not all(isinstance(p, str) and p for p in roots)
    ):
        raise ValueError("compare_roots must contain exactly two directory paths")
    ignored = _ignored_names(data)
    left, right = (_scan_directories(raw, ignored) for raw in roots)
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
    if not isinstance(data, dict):
        raise TypeError("input must be a JSON object")
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
