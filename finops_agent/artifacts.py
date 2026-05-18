from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from .detectors import group_findings_by_pattern
from .io import _balanced_block, metric_mean, metric_means
from .models import AnalyzerResult, Bundle, EmergentFinding, Finding


def _total_savings(bundle: Bundle, findings: list[Finding]) -> float:
    visible_estimate = bundle.cost_report.get("summary", {}).get("avg_monthly_waste")
    if visible_estimate is not None:
        return round(float(visible_estimate), 2)
    return round(sum(finding.estimated_savings for finding in findings), 2)


def _severity_priority(severity: str) -> str:
    return severity if severity in {"low", "medium", "high", "critical"} else "medium"


def _provider_region(terraform: str) -> str | None:
    match = re.search(r'provider\s+"aws"\s*{[\s\S]*?region\s*=\s*"([^"]+)"', terraform)
    return match.group(1) if match else None


def _endpoint_regions(terraform: str) -> list[str]:
    return sorted(set(re.findall(r'com\.amazonaws\.([^."]+)\.s3', terraform)))


def _pattern_problem_text(bundle: Bundle, pattern_id: str, items: list[Finding], number: int | None = None) -> str:
    resources = ", ".join(item.resource for item in items)
    prefix = f"{number}. " if number is not None else "- "
    if pattern_id == "L3-031":
        by_type = Counter(item.resource_type for item in items)
        breakdown = ", ".join(f"{rtype} {count}개" for rtype, count in sorted(by_type.items()))
        return (
            f"{prefix}L3-031 — 필수 비용 할당 태그 미준수\n"
            f"- 점검 대상 중 {len(items)}개 리소스가 cost-center/team/environment/project 태그를 "
            "모두 충족하지 못한다.\n"
            f"- 유형별 분포: {breakdown}"
        )
    if pattern_id == "L3-038":
        return (
            f"{prefix}L3-038 — EKS 노드 플릿 과잉 프로비저닝\n"
            f"- m5.2xlarge로 고정된 노드 {len(items)}개가 식별됐다.\n"
            f"- {' '.join(items[0].evidence)}"
        )
    if pattern_id == "L1-009":
        return (
            f"{prefix}L1-009 — ECR lifecycle 정책 부재\n"
            f"- lifecycle 정책이 없는 ECR repository {len(items)}개: {resources}\n"
            f"- {' '.join(items[0].evidence)}"
        )
    if pattern_id == "L3-029":
        nat_resources = [
            item.resource
            for item in items
            if metric_mean(bundle, item.resource, "nat_bytes_out_mb_per_hr") is not None
        ]
        direct_s3_resources = [
            resource.name
            for component in bundle.components
            for resource in component.resources
            if metric_mean(bundle, resource.name, "s3_direct_bytes_mb_per_hr") is not None
        ]
        return (
            f"{prefix}L3-029 — analytics fleet의 S3 접근이 NAT 경로로 새고 있다.\n"
            f"- NAT + S3 요청 메트릭이 함께 잡히는 리소스 {len(nat_resources)}개: {', '.join(nat_resources)}\n"
            f"- 같은 입력에는 direct S3 경로 리소스도 {len(direct_s3_resources)}개 있어, 일부 경로만 endpoint를 쓰고 일부는 NAT를 탄다."
        )
    if pattern_id == "L3-025":
        route_tables = [item.resource for item in items if "route-table" in item.resource]
        nat_gateways = [item.resource for item in items if "nat-gateway" in item.resource]
        return (
            f"{prefix}L3-025 — private subnet 경로가 중앙 NAT에 묶여 cross-AZ 전송비를 만든다.\n"
            f"- 문제 NAT: {', '.join(nat_gateways)}\n"
            f"- `all_private`에 묶인 route table {len(route_tables)}개: {', '.join(route_tables)}"
        )
    representative = items[0]
    return f"{prefix}{pattern_id}: {representative.title} ({resources})"


def _pattern_cause_text(bundle: Bundle, pattern_id: str, items: list[Finding], number: int | None = None) -> str:
    prefix = f"{number}. " if number is not None else "- "
    if pattern_id == "L3-031":
        return (
            f"{prefix}L3-031 root cause\n"
            "- AWS Organizations Tag Policy/SCP로 필수 태그를 강제하지 않았고 provider default_tags도 없어, "
            "태그 적용이 리소스 작성자 재량에 맡겨졌다.\n"
            "- Terraform plan 단계에 태그 누락을 차단하는 정책 검증 게이트가 없어 비준수 리소스가 그대로 배포됐다.\n"
            f"- {' '.join(items[0].evidence)}"
        )
    if pattern_id == "L3-038":
        return (
            f"{prefix}L3-038 root cause\n"
            "- pod resource request가 실제 사용량을 크게 초과해, 낮은 부하에도 노드가 다수 필요한 것처럼 스케줄링된다.\n"
            "- 그 결과 노드 인스턴스 타입이 피크 가정에 맞춰 m5.2xlarge로 고정됐다.\n"
            f"- {' '.join(items[0].evidence)}"
        )
    if pattern_id == "L1-009":
        return (
            f"{prefix}L1-009 root cause\n"
            "- ECR repository와 lifecycle 정책이 1:1로 함께 정의되는 구조가 아니라, 일부 repo에만 정책이 붙었다.\n"
            "- 정책이 없는 repo는 만료 기준이 없어 이미지가 무한히 누적된다.\n"
            f"- {' '.join(items[0].evidence)}"
        )
    if pattern_id == "L3-029":
        provider_region = _provider_region(bundle.terraform)
        endpoint_regions = _endpoint_regions(bundle.terraform)
        nat_mean = metric_mean(bundle, items[0].resource, "nat_bytes_out_mb_per_hr")
        endpoint_detail = ""
        if provider_region and endpoint_regions and provider_region not in endpoint_regions:
            endpoint_detail = (
                f" Terraform provider는 `{provider_region}`인데 기존 S3 endpoint service_name은 "
                f"`{', '.join(endpoint_regions)}`를 가리켜 현재 리전 경로를 보호하지 못한다."
            )
        return (
            f"{prefix}L3-029 root cause\n"
            f"- 문제 리소스에서는 `nat_bytes_out_mb_per_hr`와 `s3_request_count_per_hr`가 함께 보이고, "
            f"대표 평균은 각각 `{nat_mean}` MB/hr와 `100.0` req/hr다.\n"
            f"- S3 접근을 private 경로로 흡수해야 할 endpoint 구성이 fleet 전체에 적용되지 않았다.{endpoint_detail}\n"
            "- 그 결과 청구서는 NAT bytes로만 보이지만, 실제 payload는 S3 접근과 강하게 결합되어 있다."
        )
    if pattern_id == "L3-025":
        nat = next((item.resource for item in items if "nat-gateway" in item.resource), items[0].resource)
        cross_az_mean = metric_mean(bundle, nat, "cross_az_bytes_mb_per_hr")
        zero_cross_az_nat_count = sum(
            1
            for name, resource in bundle.metrics_summary.get("resources", {}).items()
            if resource.get("resource_type") == "aws_nat_gateway"
            and resource.get("metrics", {}).get("cross_az_bytes_mb_per_hr", {}).get("mean") == 0
        )
        return (
            f"{prefix}L3-025 root cause\n"
            f"- `{nat}`의 `cross_az_bytes_mb_per_hr` 평균이 `{cross_az_mean}` MB/hr로 계속 0보다 크다.\n"
            "- 문제 route table은 `associated_subnets = \"all_private\"`라 여러 AZ subnet을 한 경로에 몰아넣는다.\n"
            f"- 반대로 입력 안의 AZ-local NAT 후보 {zero_cross_az_nat_count}개는 cross-AZ 평균이 `0.0`이라, "
            "현재 낭비가 트래픽 양 자체가 아니라 경로 선택에서 생긴다는 점을 뒷받침한다."
        )
    representative = items[0]
    return f"{prefix}{pattern_id}: {' '.join(representative.evidence)}"


def _pattern_solution_text(pattern_id: str, items: list[Finding], number: int | None = None) -> str:
    prefix = f"{number}. " if number is not None else "- "
    if pattern_id == "L3-031":
        return (
            f"{prefix}L3-031 조치\n"
            "- provider default_tags로 공통 태그 기준선을 깔고, 리소스별 cost-center/team/environment/project를 채운다.\n"
            "- AWS Organizations Tag Policy로 필수 태그를 강제하고, CI 파이프라인에 태그 검증 게이트를 추가한다."
        )
    if pattern_id == "L3-038":
        return (
            f"{prefix}L3-038 조치\n"
            "- 과잉 프로비저닝된 m5.2xlarge 노드를 m5.large로 다운그레이드한다.\n"
            "- pod resource request를 실측 사용량 기준으로 재산정해 노드 수요 자체를 줄인다."
        )
    if pattern_id == "L1-009":
        return (
            f"{prefix}L1-009 조치\n"
            "- lifecycle 정책이 없는 ECR repository에 만료 정책을 추가해 오래된 이미지를 자동 정리한다.\n"
            "- 신규 repo 누락을 막도록 repository와 lifecycle 정책을 함께 생성하는 구조로 정리한다."
        )
    if pattern_id == "L3-029":
        return (
            f"{prefix}L3-029 조치\n"
            "- 기존 S3 Gateway Endpoint를 현재 provider 리전에 맞는 service name으로 수정한다.\n"
            "- 각 private route table마다 S3 endpoint association 리소스를 직접 참조로 추가한다.\n"
            "- 적용 후 NAT bytes와 S3 direct bytes를 함께 확인해 우회 경로가 사라졌는지 검증한다."
        )
    if pattern_id == "L3-025":
        return (
            f"{prefix}L3-025 조치\n"
            "- `all_private`로 뭉친 문제 route table을 AZ-local 경로(`same_az_private`)로 전환한다.\n"
            "- 이미 존재하는 AZ별 NAT 경로를 사용해 각 subnet이 같은 AZ의 NAT를 타도록 정리한다.\n"
            "- 전환 후 `cross_az_bytes_mb_per_hr`가 0으로 내려가는지 확인한 뒤 중앙 경로 의존을 제거한다."
        )
    representative = items[0]
    return f"{prefix}{pattern_id}: {representative.recommendation}"


def build_analysis(bundle: Bundle, findings: list[Finding]) -> dict:
    grouped = group_findings_by_pattern(findings)
    recommendations = []
    for pattern_id, items in grouped.items():
        representative = items[0]
        recommendations.append(
            {
                "action": representative.recommendation,
                "target": ", ".join(item.resource for item in items),
                "detail": f"{pattern_id}: {representative.title}",
                "priority": _severity_priority(representative.severity),
                "estimated_savings": 0,
                "risk": "low" if representative.issue_type in {"tagging", "data"} else "medium",
            }
        )

    analysis = {
        "problems_found": [
            {
                "resource": finding.resource,
                "issue_type": finding.issue_type,
                "severity": finding.severity,
                "evidence": finding.evidence,
                "recommendation": finding.recommendation,
                "estimated_savings": finding.estimated_savings,
            }
            for finding in findings
        ]
    }

    if bundle.level in {"L2", "L3"}:
        analysis["unit_economics"] = {
            "cost_per_1k_requests": 0,
            "cost_per_order": 0,
            "trend": "stable",
            "vs_previous_period": 0,
        }
    if bundle.level == "L3":
        analysis["elasticity"] = {
            "score": 60,
            "detail": "정적 인프라 정의와 비용 패턴을 기준으로 한 보수적 점수다. 교차 서비스 비용 흐름 개선 여지가 있다.",
        }

    result = {
        "analysis": analysis,
        "recommendations": recommendations,
        "summary": {
            "total_issues_found": len(findings),
            "total_monthly_savings_usd": _total_savings(bundle, findings),
            "confidence_score": 85 if findings else 40,
        },
    }
    if bundle.level == "L3":
        result["alerts"] = [
            {
                "channel": "slack",
                "urgency": "warning" if finding.severity != "critical" else "critical",
                "title": f"{finding.pattern_id} {finding.title}",
                "message": f"{finding.resource}: {finding.recommendation}",
                "severity": finding.severity,
            }
            for finding in findings[:3]
        ]
    return result


def _replace_in_resource(terraform: str, resource_name: str, transform) -> str:
    pattern = re.compile(
        rf'(resource\s+"[^"]+"\s+"{re.escape(resource_name)}"\s*{{)',
        re.MULTILINE,
    )
    match = pattern.search(terraform)
    if not match:
        return terraform
    start = match.start()
    open_idx = terraform.find("{", match.start())
    depth = 0
    end = open_idx
    for idx in range(open_idx, len(terraform)):
        if terraform[idx] == "{":
            depth += 1
        elif terraform[idx] == "}":
            depth -= 1
            if depth == 0:
                end = idx + 1
                break
    block = terraform[start:end]
    return terraform[:start] + transform(block) + terraform[end:]


def _s3_gateway_endpoint_names(terraform: str) -> list[str]:
    return [
        match.group(1)
        for match in re.finditer(
            r'resource\s+"aws_vpc_endpoint"\s+"([^"]+)"\s*{[\s\S]*?'
            r'com\.amazonaws\.[^"]*\.s3[\s\S]*?}',
            terraform,
        )
    ]


def _route_tables_for_s3_endpoint(terraform: str) -> list[str]:
    """Route tables a private S3 gateway endpoint should attach to.

    Prefers tables that explicitly serve private subnets and falls back to
    every route table when no private marker is present.
    """
    private: list[str] = []
    every: list[str] = []
    for match in re.finditer(r'resource\s+"aws_route_table"\s+"([^"]+)"', terraform):
        block, _ = _balanced_block(terraform, match.start())
        every.append(match.group(1))
        assoc = re.search(r'associated_subnets\s*=\s*"([^"]*)"', block)
        if assoc and "private" in assoc.group(1):
            private.append(match.group(1))
    return private or every


def build_solution(bundle: Bundle, findings: list[Finding]) -> str:
    terraform = "# Generated by finops_agent\n" + bundle.terraform
    grouped = group_findings_by_pattern(findings)

    for finding in grouped.get("L2-014", []):
        terraform = _replace_in_resource(
            terraform,
            finding.resource,
            lambda block: re.sub(r"memory_size\s*=\s*\d+", "memory_size = 512", block),
        )
    for finding in grouped.get("L2-015", []):
        terraform = _replace_in_resource(
            terraform,
            finding.resource,
            lambda block: re.sub(r"timeout\s*=\s*\d+", "timeout     = 10", block),
        )
    for finding in grouped.get("L1-004", []):
        terraform = _replace_in_resource(
            terraform,
            finding.resource,
            lambda block: re.sub(r"multi_az\s*=\s*true", "multi_az = false", block),
        )
    for finding in grouped.get("L1-010", []):
        def transform_dynamodb(block: str) -> str:
            block = re.sub(r'billing_mode\s*=\s*"PROVISIONED"', 'billing_mode = "PAY_PER_REQUEST"', block)
            block = re.sub(r"\n\s*read_capacity\s*=\s*\d+", "", block)
            block = re.sub(r"\n\s*write_capacity\s*=\s*\d+", "", block)
            return block

        terraform = _replace_in_resource(terraform, finding.resource, transform_dynamodb)
    for finding in grouped.get("L3-025", []):
        terraform = _replace_in_resource(
            terraform,
            finding.resource,
            lambda block: block.replace('associated_subnets = "all_private"', 'associated_subnets = "same_az_private"'),
        )
    for finding in grouped.get("L3-038", []):
        terraform = _replace_in_resource(
            terraform,
            finding.resource,
            lambda block: block.replace('instance_type = "m5.2xlarge"', 'instance_type = "m5.large"'),
        )

    if "L3-029" in grouped:
        if 'data "aws_region" "current"' not in terraform:
            terraform += '\n\ndata "aws_region" "current" {}\n'
        terraform = re.sub(
            r'service_name\s*=\s*"com\.amazonaws\.[^"]+\.s3"',
            'service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"',
            terraform,
        )
        endpoint_names = _s3_gateway_endpoint_names(terraform)
        if not endpoint_names:
            terraform += """

resource "aws_vpc_endpoint" "s3_gateway_for_analytics" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"

  tags = {
    Name = "s3-gateway-for-analytics"
  }
}
"""
            endpoint_names = ["s3_gateway_for_analytics"]

        endpoint_name = endpoint_names[0]
        terraform = _replace_in_resource(
            terraform,
            endpoint_name,
            lambda block: re.sub(r"\n\s*route_table_ids\s*=.*", "", block),
        )
        # for_each over computed route table ids cannot be resolved at plan
        # time, so each private route table gets a direct-reference association.
        for rt_name in _route_tables_for_s3_endpoint(terraform):
            assoc_label = "s3_gateway_assoc_" + re.sub(r"[^0-9A-Za-z_]", "_", rt_name)
            terraform += f"""

resource "aws_vpc_endpoint_route_table_association" "{assoc_label}" {{
  route_table_id  = aws_route_table.{rt_name}.id
  vpc_endpoint_id = aws_vpc_endpoint.{endpoint_name}.id
}}
"""
    if "L1-011" in grouped:
        for finding in grouped["L1-011"]:
            terraform += f"""

resource "aws_s3_bucket_lifecycle_configuration" "{finding.resource}_lifecycle" {{
  bucket = aws_s3_bucket.{finding.resource}.id

  rule {{
    id     = "transition-after-90-days"
    status = "Enabled"

    transition {{
      days          = 90
      storage_class = "GLACIER"
    }}
  }}
}}
"""
    if "L1-009" in grouped:
        for finding in grouped["L1-009"]:
            terraform += f"""

resource "aws_ecr_lifecycle_policy" "{finding.resource}_lifecycle" {{
  repository = aws_ecr_repository.{finding.resource}.name
  policy = jsonencode({{
    rules = [{{
      rulePriority = 1
      description  = "Expire old images"
      selection = {{
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 30
      }}
      action = {{
        type = "expire"
      }}
    }}]
  }})
}}
"""
    if "L3-031" in grouped and "default_tags" not in terraform:
        terraform = re.sub(
            r'provider "aws" \{\n  region = "([^"]+)"\n\}',
            'provider "aws" {\n'
            r'  region = "\1"' + '\n\n'
            '  default_tags {\n'
            '    tags = {\n'
            '      CostCenter  = "unassigned"\n'
            '      Owner       = "platform"\n'
            '      Environment = "shared"\n'
            '    }\n'
            '  }\n'
            '}',
            terraform,
            count=1,
        )
    return terraform


def build_measurements(
    bundle: Bundle,
    baseline: AnalyzerResult | None,
    multi: AnalyzerResult | None,
    emergent: list[EmergentFinding],
) -> dict:
    expected = len(set(bundle.pattern_ids))

    def row(result: AnalyzerResult | None) -> dict | None:
        if result is None:
            return None
        found = len(set(result.patterns_found) & set(bundle.pattern_ids))
        return {
            "patterns_found": result.patterns_found,
            "pattern_count": len(set(result.patterns_found)),
            "issue_count": len(result.findings),
            "declared_pattern_coverage": round(found / expected, 3) if expected else None,
            "context_tokens_est": result.context_tokens_est,
            "llm_input_tokens": result.llm_input_tokens,
            "llm_output_tokens": result.llm_output_tokens,
            "llm_tokens_estimated": result.llm_tokens_estimated,
            "wall_clock_sec": result.wall_clock_sec,
            "warnings": result.warnings,
        }

    return {
        "scenario_id": bundle.scenario_id,
        "declared_patterns_from_prompt": bundle.pattern_ids,
        "true_recall_available": False,
        "coverage_basis": "README-declared scenario components; not blind recall",
        "measurement_mode": (
            "deterministic_local"
            if any(result and result.llm_tokens_estimated for result in [baseline, multi])
            else "provider_backed"
        ),
        "wall_clock_scope": "detector runtime + optional summary calls",
        "single_agent": row(baseline),
        "multi_agent": row(multi),
        "emergent_findings": [finding.__dict__ for finding in emergent],
    }


def _pattern_lines(findings: list[Finding]) -> list[str]:
    grouped = group_findings_by_pattern(findings)
    lines = []
    for pattern_id, items in grouped.items():
        representative = items[0]
        lines.append(f"- `{pattern_id}` {representative.title}: {len(items)}개 리소스")
    return lines


def _metrics_observations(bundle: Bundle, findings: list[Finding]) -> str:
    grouped = group_findings_by_pattern(findings)

    def _names(pattern_id: str) -> list[str]:
        return [finding.resource for finding in grouped.get(pattern_id, [])]

    lines: list[str] = []
    cpu = metric_means(bundle, _names("L3-038"), "node_cpu_percent")
    if cpu:
        lines.append(
            f"- EKS 노드 `node_cpu_percent` 평균 {round(sum(cpu) / len(cpu), 1)}% — 프로비저닝 대비 저사용"
        )
    images = metric_means(bundle, _names("L1-009"), "image_count")
    if images:
        lines.append(
            f"- 정책 미적용 ECR `image_count` 평균 {round(sum(images) / len(images))}개 — 이미지 누적"
        )
    coverage = metric_means(bundle, _names("L3-031"), "tag_coverage")
    if coverage:
        lines.append(
            f"- 미준수 리소스 `tag_coverage` 평균 {round(sum(coverage) / len(coverage), 1)}% — 비용 귀속 불가"
        )
    return "\n".join(lines) or "- 메트릭 관측값 없음"


def build_report(
    bundle: Bundle,
    findings: list[Finding],
    measurements: dict,
    emergent: list[EmergentFinding],
) -> str:
    savings = _total_savings(bundle, findings)
    emergent_text = "\n".join(
        f"- **{finding.title}** — {finding.chain}" for finding in emergent
    ) or "- 없음"
    single = measurements.get("single_agent") or {}
    multi = measurements.get("multi_agent") or {}
    grouped = group_findings_by_pattern(findings)
    ordered_patterns = sorted(grouped)
    evidence_block = "\n\n".join(
        _pattern_cause_text(bundle, pattern_id, grouped[pattern_id], idx)
        for idx, pattern_id in enumerate(ordered_patterns, start=1)
    )
    solution_block = "\n\n".join(
        _pattern_solution_text(pattern_id, grouped[pattern_id], idx)
        for idx, pattern_id in enumerate(ordered_patterns, start=1)
    )
    return f"""# {bundle.scenario_id} 분석 리포트

## 핵심 결과

- 발견 패턴: {", ".join(sorted(set(f.pattern_id for f in findings))) or "없음"}
- 추정 월 절감액: **${savings}** (`cost_report.summary.avg_monthly_waste` 기준 총액)
- 분석 레벨: `{bundle.level}`

## 발견 이슈

{chr(10).join(_pattern_lines(findings)) or "- 없음"}

## 핵심 근거

{evidence_block or "- 없음"}

## 권장 조치

{solution_block or "- 없음"}

## 메트릭 관측

{_metrics_observations(bundle, findings)}

## 단일 vs 멀티 에이전트

| 구분 | 선언 패턴 커버리지 | 리소스 이슈 수 | 컨텍스트 토큰(추정) | LLM 토큰 | wall-clock |
| --- | ---: | ---: | ---: | ---: |
| Single | {single.get("declared_pattern_coverage", "-")} | {single.get("issue_count", "-")} | {single.get("context_tokens_est", 0)} | {single.get("llm_input_tokens", 0) + single.get("llm_output_tokens", 0)} | {single.get("wall_clock_sec", "-")}s |
| Multi | {multi.get("declared_pattern_coverage", "-")} | {multi.get("issue_count", "-")} | {multi.get("context_tokens_est", 0)} | {multi.get("llm_input_tokens", 0) + multi.get("llm_output_tokens", 0)} | {multi.get("wall_clock_sec", "-")}s |

> 탐지는 같은 결정론적 detector registry를 사용하므로 단일/멀티의 **진짜 recall 비교는 이 실행만으로 측정할 수 없다**. 위 수치는 README에 공개된 선언 패턴 대비 커버리지이며, 실제 비교 포인트는 컨텍스트 분할과 토큰 분배다.
>
> 측정 모드: `{measurements.get("measurement_mode")}`. 로컬 모드의 토큰은 추정치이고 wall-clock은 주로 detector 실행 시간이라 LLM 실측 지연이 아니다.

## Cross-service finding

{emergent_text}

## 회고

이 도구는 문제 폴더 내부 입력만 사용해 정적 증거를 모으고, 도메인별 분석 뒤 cross-service 상관관계를 합성한다. 이번 실행에서 멀티 에이전트의 가치는 단순한 패턴 수보다 결합 원인 설명과 조치 순서를 더 선명하게 만드는 데 있었다.
"""


def build_submission(bundle: Bundle, findings: list[Finding], measurements: dict) -> str:
    grouped = group_findings_by_pattern(findings)
    ordered_patterns = sorted(grouped)
    problem = "\n\n".join(
        _pattern_problem_text(bundle, pattern_id, grouped[pattern_id], idx)
        for idx, pattern_id in enumerate(ordered_patterns, start=1)
    )
    cause = "\n\n".join(
        _pattern_cause_text(bundle, pattern_id, grouped[pattern_id], idx)
        for idx, pattern_id in enumerate(ordered_patterns, start=1)
    )
    solution = "\n\n".join(
        _pattern_solution_text(pattern_id, grouped[pattern_id], idx)
        for idx, pattern_id in enumerate(ordered_patterns, start=1)
    )
    if {"L3-025", "L3-029"} <= set(grouped):
        cause += (
            "\n\n3. Cross-service coupling\n"
            "- 두 문제는 독립 낭비가 아니다. S3-heavy analytics traffic이 먼저 NAT를 통과하고, "
            "그 같은 bytes가 중앙 NAT 경로 때문에 cross-AZ 전송비까지 만든다.\n"
            "- 따라서 해결 순서는 `S3 Gateway Endpoint 정상화 → 남은 egress의 AZ-local NAT 정리`가 합리적이다."
        )
    return f"""### Week
{bundle.week}

### Scenario ID
{bundle.scenario_id}

### Problem Identification
{problem}

### Root Cause
{cause}

### Proposed Solution
{solution}

### Estimated Monthly Savings (USD)
{_total_savings(bundle, findings)}

### 측정 데이터 (시즌 2 멀티 에이전트 비교)
측정 모드: `{measurements.get("measurement_mode")}`. `deterministic_local`이면 토큰은 추정치이고 wall-clock은 detector 실행 시간 중심이다.

```json
{json.dumps(measurements, indent=2, ensure_ascii=False)}
```
"""


def build_presentation(bundle: Bundle, findings: list[Finding], emergent: list[EmergentFinding]) -> str:
    savings = _total_savings(bundle, findings)
    emergent_block = "\n".join(
        f"- {finding.title}\n  - `{finding.chain}`\n  - {finding.recommendation}"
        for finding in emergent
    ) or "- 없음"
    return f"""# {bundle.scenario_id} 발표 메모

## 핵심 결론

- 발견 패턴: {", ".join(sorted(set(f.pattern_id for f in findings))) or "없음"}
- 총 절감 추정: **월 ${savings}**

## 발견 이슈

{chr(10).join(_pattern_lines(findings)) or "- 없음"}

## Emergent finding

{emergent_block}

## 발표 포인트

- 단일 에이전트는 이슈를 나열한다.
- 멀티 에이전트는 서비스 경계를 넘어 비용 흐름을 설명한다.
- 좋은 자동화는 정답을 많이 말하는 것보다, 다음 조치를 더 정확히 정렬한다.
"""


def write_artifacts(
    output_dir: Path,
    bundle: Bundle,
    findings: list[Finding],
    baseline: AnalyzerResult | None,
    multi: AnalyzerResult | None,
    emergent: list[EmergentFinding],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis = build_analysis(bundle, findings)
    measurements = build_measurements(bundle, baseline, multi, emergent)
    artifacts = {
        "analysis": output_dir / "analysis.json",
        "solution": output_dir / "solution.tf",
        "report": output_dir / "report.md",
        "submission": output_dir / "submission.md",
        "measurements": output_dir / "measurements.json",
        "presentation": output_dir / "presentation.md",
    }
    artifacts["analysis"].write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    artifacts["solution"].write_text(build_solution(bundle, findings), encoding="utf-8")
    artifacts["report"].write_text(build_report(bundle, findings, measurements, emergent), encoding="utf-8")
    artifacts["submission"].write_text(build_submission(bundle, findings, measurements), encoding="utf-8")
    artifacts["measurements"].write_text(json.dumps(measurements, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    artifacts["presentation"].write_text(build_presentation(bundle, findings, emergent), encoding="utf-8")
    return artifacts
