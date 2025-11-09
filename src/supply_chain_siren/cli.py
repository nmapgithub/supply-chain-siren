from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .models import PackageAssessment
from .osint import fetch_metadata
from .parsers import discover_manifests, parse_manifest
from .scoring import assess_dependency

console = Console()


def cli(
    path: Path = typer.Argument(Path("."), exists=True, resolve_path=True, help="Folder to scan."),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Optional path to write JSON report."
    ),
) -> None:
    """Scan the target repository for suspicious dependencies."""
    manifests = discover_manifests(path)
    if not manifests:
        console.print("[yellow]No supported dependency manifests discovered.[/]")
        raise typer.Exit(code=1)

    console.print(f"[bold cyan]Discovered {len(manifests)} manifest(s). Starting analysis...[/]")
    assessments: dict[str, PackageAssessment] = {}

    with Progress(
        SpinnerColumn(spinner_name="line"),
        TextColumn("{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Collecting dependencies", total=len(manifests))
        for manifest in manifests:
            specs = parse_manifest(manifest)
            for spec in specs:
                assessments.setdefault(spec.slug, PackageAssessment(dependency=spec))
            progress.advance(task)

    with Progress(
        SpinnerColumn(spinner_name="line"),
        TextColumn("{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Contacting registries", total=len(assessments))
        for slug, assessment in assessments.items():
            metadata = fetch_metadata(assessment.dependency)
            enriched = assess_dependency(assessment.dependency, metadata)
            assessments[slug] = enriched
            progress.advance(task)

    _render_table(list(assessments.values()))

    if output:
        _write_report(output, list(assessments.values()))
        console.print(f"[green]Report exported to[/] {output}")


def _render_table(assessments: list[PackageAssessment]) -> None:
    if not assessments:
        console.print("[green]No dependencies evaluated.[/]")
        return

    table = Table(title="Supply Chain Risk Surface", expand=True)
    table.add_column("Package", no_wrap=True)
    table.add_column("Version", no_wrap=True)
    table.add_column("Score", justify="right")
    table.add_column("Signals", overflow="fold")

    for assessment in sorted(assessments, key=lambda a: a.score, reverse=True):
        spec = assessment.dependency
        version = spec.version or (assessment.metadata.latest_version if assessment.metadata else "-")
        reasons = "\n".join(signal.reason for signal in assessment.signals) or "No obvious risks"
        table.add_row(f"{spec.name} ({spec.ecosystem})", str(version), str(assessment.score), reasons)

    console.print(table)


def _write_report(path: Path, assessments: list[PackageAssessment]) -> None:
    payload = []
    for assessment in assessments:
        payload.append(
            {
                "dependency": assessment.dependency.model_dump(),
                "metadata": assessment.metadata.model_dump() if assessment.metadata else None,
                "signals": [signal.model_dump() for signal in assessment.signals],
                "score": assessment.score,
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def main() -> None:
    typer.run(cli)


if __name__ == "__main__":
    main()

