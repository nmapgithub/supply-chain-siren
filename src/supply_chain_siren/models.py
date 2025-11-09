from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field

Ecosystem = Literal["pypi", "npm"]


class DependencySpec(BaseModel):
    """Represents a dependency discovered in a manifest."""

    name: str = Field(..., description="Package identifier as declared in the manifest.")
    version: str | None = Field(
        default=None, description="Pinned version where available; None for non-pinned specs."
    )
    ecosystem: Ecosystem = Field(..., description="Ecosystem the dependency belongs to.")
    source_path: Path = Field(..., description="Manifest file the dependency originated from.")

    @computed_field
    @property
    def slug(self) -> str:
        return f"{self.ecosystem}:{self.name.lower()}"


class PackageMetadata(BaseModel):
    """Normalized metadata fetched from upstream registries."""

    name: str
    ecosystem: Ecosystem
    latest_version: str | None = None
    latest_published: datetime | None = None
    first_published: datetime | None = None
    maintainers: list[str] = Field(default_factory=list)
    weekly_downloads: int | None = None
    homepage: str | None = None
    repository_url: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RiskSignal(BaseModel):
    """Single risk factor identified during analysis."""

    reason: str
    score: int = Field(ge=0, le=100, description="Severity of the signal on a 0-100 scale.")
    category: Literal[
        "typosquat", "fresh-release", "stale-package", "metadata-gaps", "popularity", "maintainers"
    ]


class PackageAssessment(BaseModel):
    dependency: DependencySpec
    metadata: PackageMetadata | None = None
    signals: list[RiskSignal] = Field(default_factory=list)
    score: int = 0

    def add_signal(self, signal: RiskSignal) -> None:
        self.signals.append(signal)
        self.score = min(100, self.score + signal.score)

