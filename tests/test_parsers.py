from __future__ import annotations

import json

from supply_chain_siren.parsers import parse_manifest


def test_parse_requirements(tmp_path):
    manifest = tmp_path / "requirements.txt"
    manifest.write_text("requests==2.31.0\n# comment\nnumpy>=1.0\n", encoding="utf-8")

    deps = parse_manifest(manifest)

    assert {dep.name for dep in deps} == {"requests", "numpy"}
    assert deps[0].ecosystem == "pypi"


def test_parse_package_json(tmp_path):
    payload = {
        "dependencies": {"react": "^18.0.0"},
        "devDependencies": {"eslint": "^8.0.0"},
    }
    manifest = tmp_path / "package.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    deps = parse_manifest(manifest)
    assert {dep.name for dep in deps} == {"react", "eslint"}
    assert all(dep.ecosystem == "npm" for dep in deps)

