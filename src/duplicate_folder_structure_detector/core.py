from __future__ import annotations

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
    signatures: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for directory in [root, *sorted(path for path in root.rglob("*") if path.is_dir())]:
        if any(
            part in {".git", ".venv", "node_modules", "__pycache__"} for part in directory.parts
        ):
            continue
        descendants = tuple(
            sorted(
                path.relative_to(directory).as_posix()
                for path in directory.rglob("*")
                if path.is_dir()
                and (
                    not any(
                        part in {".git", ".venv", "node_modules", "__pycache__"}
                        for part in path.parts
                    )
                )
            )
        )
        if descendants:
            signatures[descendants].append(directory.relative_to(root).as_posix() or ".")
    groups = [
        {"directories": paths, "structure": list(signature)}
        for signature, paths in signatures.items()
        if len(paths) > 1
    ]
    groups.sort(key=lambda item: (-len(item["directories"]), item["directories"]))
    return {
        "duplicate_groups": groups,
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
