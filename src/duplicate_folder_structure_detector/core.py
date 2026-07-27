from __future__ import annotations

import hashlib
import json
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


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    return {"version": 1, "project": PROJECT, **_duplicate_trees(data)}


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
