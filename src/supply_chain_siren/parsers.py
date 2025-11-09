from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from .models import DependencySpec

RE_REQUIREMENT = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9_.-]+)"
    r"(?:\s*(?:==|>=|<=|~=|!=|===)\s*(?P<version>[^\s;]+))?"
    r"(?:\s*;.*)?$"
)


def discover_manifests(root: Path) -> list[Path]:
    """Return a list of manifest files we know how to parse."""
    candidates = [
        "requirements.txt",
        "requirements-dev.txt",
        "package-lock.json",
        "package.json",
        "Pipfile.lock",
        "poetry.lock",
    ]
    manifests: list[Path] = []
    for candidate in candidates:
        for path in root.rglob(candidate):
            if path.is_file():
                manifests.append(path)
    return manifests


def parse_manifest(path: Path) -> list[DependencySpec]:
    """Parse a manifest into dependency specs."""
    if path.name in {"requirements.txt", "requirements-dev.txt"}:
        return list(_parse_requirements(path))
    if path.name == "package-lock.json":
        return list(_parse_package_lock(path))
    if path.name == "package.json":
        return list(_parse_package_json(path))
    if path.name in {"Pipfile.lock", "poetry.lock"}:
        return list(_parse_pep_lock(path))
    return []


def _parse_requirements(path: Path) -> Iterable[DependencySpec]:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = RE_REQUIREMENT.match(line)
        if not match:
            continue
        name = match.group("name")
        version = match.group("version")
        yield DependencySpec(name=name.lower(), version=version, ecosystem="pypi", source_path=path)


def _parse_package_lock(path: Path) -> Iterable[DependencySpec]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    dependencies = payload.get("dependencies", {})

    def walk(dep_map: dict[str, dict]) -> Iterable[DependencySpec]:
        for name, info in dep_map.items():
            version = info.get("version")
            yield DependencySpec(
                name=name.lower(), version=version, ecosystem="npm", source_path=path
            )
            nested = info.get("dependencies")
            if isinstance(nested, dict):
                yield from walk(nested)

    return walk(dependencies)


def _parse_package_json(path: Path) -> Iterable[DependencySpec]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    dependencies = payload.get("dependencies", {})
    dev_dependencies = payload.get("devDependencies", {})

    for name, version in {**dependencies, **dev_dependencies}.items():
        yield DependencySpec(name=name.lower(), version=version, ecosystem="npm", source_path=path)


def _parse_pep_lock(path: Path) -> Iterable[DependencySpec]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if path.name == "Pipfile.lock":
        sections = ["default", "develop"]
    else:  # poetry.lock (its JSON is a list, can't treat same)
        # Poetry lock is TOML-like; for MVP skip heavy parsing.
        return []

    specs: list[DependencySpec] = []
    for section in sections:
        deps = payload.get(section, {})
        if isinstance(deps, dict):
            for name, info in deps.items():
                version = info.get("version")
                specs.append(
                    DependencySpec(
                        name=name.lower(), version=version, ecosystem="pypi", source_path=path
                    )
                )
    return specs

