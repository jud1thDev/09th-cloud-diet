"""문제 폴더의 파일을 읽어 분석용 Bundle로 조립한다 (파이프라인의 입력 단계).

핵심 역할은 세 가지다.
1. 폴더 안 파일(README/main.tf/hint/cost_report/metrics)을 읽는다. 폴더 바깥은
   절대 건드리지 않는다 — "정답을 몰래 베끼지 않는다"는 원칙.
2. main.tf 텍스트를 컴포넌트·리소스 단위로 파싱한다.
3. metrics의 원본 시계열을 평균/최대/최소 같은 요약 통계로 압축한다.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import Bundle, Component, Resource


# `# Component 1/3 · seeded from L3-029` 형태의 컴포넌트 경계 주석을 잡는다.
COMPONENT_RE = re.compile(
    r"#\s*Component\s+(\d+)/(\d+)\s+·\s+seeded from\s+(L[123]-\d+)"
)
# `resource "aws_db_instance" "main" {` 형태의 리소스 선언 시작을 잡는다.
RESOURCE_RE = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*{')


def _balanced_block(text: str, start: int) -> tuple[str, int]:
    """start 위치부터 중괄호 짝을 맞춰 블록 하나를 통째로 잘라낸다.

    `{` 를 만나면 깊이를 +1, `}` 면 -1 해서 깊이가 0으로 돌아오는 지점이
    블록의 끝이다. (블록 원문, 블록 다음 인덱스)를 돌려준다.
    """
    open_idx = text.find("{", start)
    depth = 0
    for idx in range(open_idx, len(text)):
        char = text[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1], idx + 1
    return text[start:], len(text)


def parse_resources(text: str) -> list[Resource]:
    """Terraform 텍스트에서 모든 `resource` 블록을 찾아 Resource 목록으로 만든다."""
    resources: list[Resource] = []
    for match in RESOURCE_RE.finditer(text):
        block, _ = _balanced_block(text, match.start())
        resources.append(
            Resource(
                resource_type=match.group(1),
                name=match.group(2),
                body=block,
            )
        )
    return resources


def parse_components(terraform: str) -> list[Component]:
    """`# Component ...` 주석 경계를 기준으로 main.tf를 컴포넌트 단위로 쪼갠다.

    한 컴포넌트 구간은 그 주석 다음부터 다음 컴포넌트 주석 직전까지다.
    """
    matches = list(COMPONENT_RE.finditer(terraform))
    components: list[Component] = []
    for idx, match in enumerate(matches):
        start = match.end()
        # 다음 컴포넌트 주석 시작 전까지가 이 컴포넌트의 영역. 마지막이면 파일 끝까지.
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(terraform)
        text = terraform[start:end]
        components.append(
            Component(
                index=int(match.group(1)),
                total=int(match.group(2)),
                pattern_id=match.group(3),
                text=text,
                resources=parse_resources(text),
            )
        )
    return components


def summarize_metrics(raw: dict[str, Any]) -> dict[str, Any]:
    """metrics.json의 원본 시계열을 리소스별 요약 통계로 압축한다.

    원본 datapoints 배열은 수백 개라 그대로 분석에 넣으면 컨텍스트가 커진다.
    그래서 평균/최대/최소/0값 비율/개수만 남긴다. 탐지기는 이 요약값만 본다.
    """
    summary: dict[str, Any] = {
        "metadata": raw.get("metadata", {}),
        "resources": {},
    }
    for name, resource in raw.get("resources", {}).items():
        metrics: dict[str, Any] = {}
        for metric_name, metric in resource.get("metrics", {}).items():
            points = metric.get("datapoints", [])
            if not points:
                continue
            metrics[metric_name] = {
                "unit": metric.get("unit", ""),
                "mean": round(sum(points) / len(points), 2),
                "max": round(max(points), 2),
                "min": round(min(points), 2),
                "zero_pct": round(sum(1 for point in points if point == 0) / len(points) * 100, 1),
                "points_count": len(points),
            }
        summary["resources"][name] = {
            "resource_type": resource.get("resource_type", ""),
            "metrics": metrics,
        }
    return summary


def _extract_readme_patterns(readme: str) -> list[str]:
    """README의 `- `L3-029`` 형태 목록에서 선언된 패턴 ID들을 뽑는다."""
    return re.findall(r"-\s+`(L[123]-\d+)`", readme)


def _derive_level(pattern_ids: list[str]) -> str:
    """패턴 ID들 중 가장 높은 단계를 문제 난이도로 본다 (예: L3가 있으면 "L3")."""
    if not pattern_ids:
        return "L1"
    max_level = max(int(pattern[1]) for pattern in pattern_ids)
    return f"L{max_level}"


def _derive_week(readme: str, problem_dir: Path) -> int:
    """주차 번호를 알아낸다. 폴더 경로의 `week-NN`을 우선 보고, 없으면 README를 본다."""
    path_match = re.search(r"week-(\d+)", str(problem_dir))
    if path_match:
        return int(path_match.group(1))
    match = re.search(r"Week\s+(\d+)", readme)
    return int(match.group(1)) if match else 0


def read_bundle(problem_dir: str | Path) -> Bundle:
    """문제 폴더 하나를 읽어 분석에 필요한 모든 입력을 담은 Bundle을 만든다.

    이 함수가 읽는 것은 problem_dir 안의 파일뿐이다. 각 파일은 없어도 되며,
    없으면 빈 값으로 둔다. 이후 모든 분석 단계는 여기서 나온 Bundle만 사용한다.
    """
    path = Path(problem_dir).resolve()
    if not path.exists():
        raise FileNotFoundError(f"problem directory not found: {path}")

    readme = (path / "README.md").read_text(encoding="utf-8") if (path / "README.md").exists() else ""
    terraform = (path / "main.tf").read_text(encoding="utf-8") if (path / "main.tf").exists() else ""
    hint = (path / "hint.txt").read_text(encoding="utf-8") if (path / "hint.txt").exists() else ""
    cost_report = (
        json.loads((path / "cost_report.json").read_text(encoding="utf-8"))
        if (path / "cost_report.json").exists()
        else {}
    )
    metrics_raw = (
        json.loads((path / "metrics" / "metrics.json").read_text(encoding="utf-8"))
        if (path / "metrics" / "metrics.json").exists()
        else {}
    )
    components = parse_components(terraform)
    readme_patterns = _extract_readme_patterns(readme)
    # README에 선언된 패턴을 우선 쓰고, 없으면 컴포넌트 주석의 seed 패턴으로 대체한다.
    pattern_ids = readme_patterns or [component.pattern_id for component in components]

    available_files = sorted(
        str(file.relative_to(path))
        for file in path.rglob("*")
        if file.is_file()
    )

    return Bundle(
        problem_dir=path,
        scenario_id=path.name,
        week=_derive_week(readme, path),
        readme=readme,
        terraform=terraform,
        hint=hint,
        cost_report=cost_report,
        metrics_summary=summarize_metrics(metrics_raw),
        components=components,
        pattern_ids=pattern_ids,
        level=_derive_level(pattern_ids),
        available_files=available_files,
    )


def metric_summary_for(bundle: Bundle, resource_name: str) -> dict[str, Any]:
    """리소스 이름으로 요약 지표를 찾는다.

    이름이 그대로 없으면 끝의 `_숫자`를 떼고 다시 찾는다 (예: `nat_3` → `nat`).
    Terraform 리소스 이름과 metrics 키가 인덱스 차이로 어긋날 때를 위한 보정.
    """
    resources = bundle.metrics_summary.get("resources", {})
    if resource_name in resources:
        return resources[resource_name]
    base = re.sub(r"_\d+$", "", resource_name)
    return resources.get(base, {})


def metric_mean(bundle: Bundle, resource_name: str, metric_name: str) -> float | None:
    """리소스의 특정 지표 평균값을 꺼낸다. 지표가 없으면 None."""
    return (
        metric_summary_for(bundle, resource_name)
        .get("metrics", {})
        .get(metric_name, {})
        .get("mean")
    )


def metric_means(bundle: Bundle, resource_names: list[str], metric_name: str) -> list[float]:
    """여러 리소스에서 같은 지표의 평균값을 모은다 (값이 있는 것만)."""
    means = []
    for name in resource_names:
        mean = metric_mean(bundle, name, metric_name)
        if mean is not None:
            means.append(mean)
    return means
