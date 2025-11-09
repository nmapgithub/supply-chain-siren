from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rapidfuzz.distance import Levenshtein

from .models import DependencySpec, PackageAssessment, PackageMetadata, RiskSignal
from .osint import get_top_packages

RECENT_THRESHOLD_DAYS = 45
STALE_THRESHOLD_DAYS = 365
LOW_DOWNLOADS_THRESHOLD = 500


def assess_dependency(spec: DependencySpec, metadata: PackageMetadata | None) -> PackageAssessment:
    assessment = PackageAssessment(dependency=spec, metadata=metadata)

    if metadata is None:
        assessment.add_signal(
            RiskSignal(
                reason="Package metadata unavailable; registry lookup failed.",
                score=40,
                category="metadata-gaps",
            )
        )
        return assessment

    _evaluate_typosquat(spec, assessment)
    _evaluate_recency(metadata, assessment)
    _evaluate_staleness(metadata, assessment)
    _evaluate_popularity(metadata, assessment)
    _evaluate_maintainers(metadata, assessment)

    return assessment


def _evaluate_typosquat(spec: DependencySpec, assessment: PackageAssessment) -> None:
    top_packages = get_top_packages(spec.ecosystem)
    for top in top_packages:
        distance = Levenshtein.distance(spec.name, top)
        if distance == 0:
            return
        if distance <= 2:
            assessment.add_signal(
                RiskSignal(
                    reason=f"Name '{spec.name}' is {distance} edits away from popular package '{top}'.",
                    score=50,
                    category="typosquat",
                )
            )
            return


def _evaluate_recency(metadata: PackageMetadata, assessment: PackageAssessment) -> None:
    if metadata.first_published is None:
        return
    now = datetime.now(timezone.utc)
    if now - metadata.first_published <= timedelta(days=RECENT_THRESHOLD_DAYS):
        assessment.add_signal(
            RiskSignal(
                reason="Package is newly published; consider additional vetting.",
                score=25,
                category="fresh-release",
            )
        )


def _evaluate_staleness(metadata: PackageMetadata, assessment: PackageAssessment) -> None:
    if metadata.latest_published is None:
        return
    now = datetime.now(timezone.utc)
    if now - metadata.latest_published >= timedelta(days=STALE_THRESHOLD_DAYS):
        assessment.add_signal(
            RiskSignal(
                reason="Latest release is over a year old; project may be unmaintained.",
                score=20,
                category="stale-package",
            )
        )


def _evaluate_popularity(metadata: PackageMetadata, assessment: PackageAssessment) -> None:
    downloads = metadata.weekly_downloads
    if downloads is None:
        return
    if downloads < LOW_DOWNLOADS_THRESHOLD:
        assessment.add_signal(
            RiskSignal(
                reason=f"Weekly downloads are low ({downloads}); limited community adoption.",
                score=15,
                category="popularity",
            )
        )


def _evaluate_maintainers(metadata: PackageMetadata, assessment: PackageAssessment) -> None:
    maintainers = metadata.maintainers or []
    if len(maintainers) <= 1:
        assessment.add_signal(
            RiskSignal(
                reason="Single maintainer detected; project is susceptible to account compromise.",
                score=20,
                category="maintainers",
            )
        )

