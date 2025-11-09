from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx
from platformdirs import user_cache_dir

from .models import DependencySpec, PackageMetadata
from .utils import load_resource_json

CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours
HTTP_TIMEOUT = 10.0


class MetadataCache:
    def __init__(self) -> None:
        cache_dir = Path(user_cache_dir("supply-chain-siren"))
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / "registry_cache.json"
        try:
            self.payload = json.loads(self.cache_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.payload = {}
        except json.JSONDecodeError:
            self.payload = {}

    def get(self, key: str) -> dict[str, Any] | None:
        entry = self.payload.get(key)
        if not entry:
            return None
        if time.time() - entry.get("timestamp", 0) > CACHE_TTL_SECONDS:
            return None
        return entry.get("data")

    def set(self, key: str, data: dict[str, Any]) -> None:
        self.payload[key] = {"timestamp": time.time(), "data": data}
        self.cache_file.write_text(json.dumps(self.payload, indent=2), encoding="utf-8")


_cache = MetadataCache()
_client = httpx.Client(timeout=HTTP_TIMEOUT)
_top_packages = load_resource_json("data/top_packages.json")


def fetch_metadata(spec: DependencySpec) -> PackageMetadata | None:
    key = spec.slug
    cached = _cache.get(key)
    if cached:
        return PackageMetadata(**cached)

    try:
        if spec.ecosystem == "pypi":
            metadata = _fetch_pypi(spec)
        elif spec.ecosystem == "npm":
            metadata = _fetch_npm(spec)
        else:
            return None
    except httpx.HTTPError:
        return None

    if metadata:
        _cache.set(key, metadata.model_dump(mode="json"))
    return metadata


def _fetch_pypi(spec: DependencySpec) -> PackageMetadata | None:
    url = f"https://pypi.org/pypi/{spec.name}/json"
    resp = _client.get(url)
    if resp.status_code != 200:
        return None

    payload = resp.json()
    info = payload.get("info", {})
    releases = payload.get("releases", {})
    latest_version = info.get("version")

    release_times = []
    first_release = None
    for version, files in releases.items():
        for file_entry in files:
            upload_time = file_entry.get("upload_time_iso_8601")
            if upload_time:
                release_times.append(upload_time)
                if first_release is None or upload_time < first_release:
                    first_release = upload_time

    latest_published = None
    if release_times:
        latest_published = max(release_times)

    maintainers = info.get("maintainers") or []
    maintainers = [m.get("name") if isinstance(m, dict) else str(m) for m in maintainers]

    return PackageMetadata(
        name=spec.name,
        ecosystem="pypi",
        latest_version=latest_version,
        latest_published=_parse_datetime(latest_published),
        first_published=_parse_datetime(first_release),
        maintainers=[m for m in maintainers if m],
        weekly_downloads=payload.get("last_month_downloads"),
        homepage=info.get("home_page"),
        repository_url=info.get("project_url"),
        raw=payload,
    )


def _fetch_npm(spec: DependencySpec) -> PackageMetadata | None:
    url = f"https://registry.npmjs.org/{spec.name}"
    resp = _client.get(url)
    if resp.status_code != 200:
        return None
    payload = resp.json()

    time_section = payload.get("time", {})
    versions = payload.get("versions", {})
    latest = payload.get("dist-tags", {}).get("latest")

    latest_published = None
    first_published = None
    for version, published in time_section.items():
        if version in {"created", "modified"}:
            continue
        if not latest_published or published > latest_published:
            latest_published = published
        if not first_published or published < first_published:
            first_published = published

    maintainers_data = payload.get("maintainers") or []
    maintainers = []
    for maintainer in maintainers_data:
        if isinstance(maintainer, dict):
            maint_name = maintainer.get("name")
            if maint_name:
                maintainers.append(maint_name)
        elif isinstance(maintainer, str):
            maintainers.append(maintainer)

    downloads = _fetch_npm_downloads(spec.name)

    version_payload = versions.get(latest, {})
    homepage = version_payload.get("homepage")
    repo = version_payload.get("repository")
    repo_url = None
    if isinstance(repo, dict):
        repo_url = repo.get("url")
    elif isinstance(repo, str):
        repo_url = repo

    return PackageMetadata(
        name=spec.name,
        ecosystem="npm",
        latest_version=latest,
        latest_published=_parse_datetime(latest_published),
        first_published=_parse_datetime(first_published),
        maintainers=maintainers,
        weekly_downloads=downloads,
        homepage=homepage,
        repository_url=repo_url,
        raw=payload,
    )


def _fetch_npm_downloads(package: str) -> int | None:
    url = f"https://api.npmjs.org/downloads/point/last-week/{package}"
    try:
        resp = _client.get(url)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("downloads")
    except httpx.HTTPError:
        return None


def _parse_datetime(text: str | None):
    if not text:
        return None
    try:
        from datetime import datetime

        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def get_top_packages(ecosystem: str) -> list[str]:
    return _top_packages.get(ecosystem, [])

