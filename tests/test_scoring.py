from __future__ import annotations

from datetime import datetime, timezone

from pathlib import Path

from supply_chain_siren.models import DependencySpec, PackageMetadata
from supply_chain_siren.scoring import assess_dependency


def test_typosquat_detection(monkeypatch):
    spec = DependencySpec(
        name="reqeusts", version="1.0.0", ecosystem="pypi", source_path=Path(__file__)
    )
    metadata = PackageMetadata(
        name="reqeusts",
        ecosystem="pypi",
        latest_version="1.0.0",
        latest_published=datetime.now(timezone.utc),
        first_published=datetime.now(timezone.utc),
    )

    assessment = assess_dependency(spec, metadata)

    assert any(signal.category == "typosquat" for signal in assessment.signals)
    assert assessment.score > 0

