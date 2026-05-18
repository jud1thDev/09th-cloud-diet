from __future__ import annotations

import re
import json
from pathlib import Path

from .analyzers import correlate, run_baseline, run_multi
from .artifacts import write_artifacts
from .io import read_bundle
from .llm import get_provider
from .models import PipelineResult


def default_output_dir(bundle) -> Path:
    match = re.search(r"members/([^/]+)/season-2/problems/week-(\d+)/([^/]+)$", str(bundle.problem_dir))
    if not match:
        return bundle.problem_dir / "output"
    member, week, scenario = match.groups()
    root = bundle.problem_dir.parents[5]
    return root / "members" / member / "season-2" / "submissions" / f"week-{week}" / scenario


def discover_assigned_problem_dirs(
    repo_root: str | Path,
    *,
    member: str,
    season: int,
    week: int,
) -> list[Path]:
    root = Path(repo_root).resolve()
    week_dir = root / "members" / member / f"season-{season}" / "problems" / f"week-{week:02d}"
    if not week_dir.exists():
        raise FileNotFoundError(f"week directory not found: {week_dir}")

    assignment_path = week_dir / "assignment.json"
    if assignment_path.exists():
        assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
        scenarios = assignment.get("scenarios", [])
        assigned = [week_dir / scenario for scenario in scenarios if (week_dir / scenario).is_dir()]
        if assigned:
            return assigned

    # Fallback: the folder is already member-scoped, so any scenario directory
    # with a Terraform input is considered assigned work for that week.
    assigned = sorted(
        path
        for path in week_dir.iterdir()
        if path.is_dir() and (path / "main.tf").exists()
    )
    if assigned:
        return assigned
    raise FileNotFoundError(f"no assigned scenarios found under: {week_dir}")


def run_pipeline(
    problem_dir: str | Path,
    *,
    mode: str = "compare",
    provider_name: str = "local",
    output_dir: str | Path | None = None,
) -> PipelineResult:
    bundle = read_bundle(problem_dir)
    provider = get_provider(provider_name)

    baseline = run_baseline(bundle, provider) if mode in {"compare", "single"} else None
    multi = run_multi(bundle, provider) if mode in {"compare", "multi"} else None
    selected = multi if mode in {"compare", "multi"} else baseline
    assert selected is not None

    emergent = correlate(selected.findings)
    target_dir = Path(output_dir) if output_dir else default_output_dir(bundle)
    artifacts = write_artifacts(target_dir, bundle, selected.findings, baseline, multi, emergent)
    return PipelineResult(
        bundle=bundle,
        selected=selected,
        baseline=baseline,
        multi=multi,
        emergent_findings=emergent,
        artifacts=artifacts,
    )
