"""낭비 패턴 탐지기(detector) 모음.

각 탐지기는 "이런 조건이면 낭비"라는 규칙 하나다. AI가 추측하는 방식이 아니라,
Terraform 코드와 지표를 정규식·수치 조건으로 검사하는 결정론적 규칙이다. 그래서
같은 입력에는 항상 같은 결과가 나온다.

읽는 순서 추천:
1. PATTERN_META — 패턴 ID별 메타데이터(제목/도메인/심각도/권장조치)
2. detect_l1_004 같은 개별 탐지기 함수 — 한 패턴의 판별 규칙
3. DETECTORS / detect_component — 모든 탐지기를 한 컴포넌트에 적용하는 진입점
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Callable

from .io import metric_means, metric_summary_for
from .models import Bundle, Component, Finding, Resource


# 패턴 ID → 사람이 읽는 메타데이터. 탐지기는 조건만 판별하고, 제목·도메인·심각도·
# 권장조치 같은 고정 정보는 여기서 가져와 Finding을 채운다.
PATTERN_META = {
    "L1-004": {
        "title": "개발 환경 RDS Multi-AZ 과잉",
        "domain": "database",
        "issue_type": "overprovisioned",
        "severity": "medium",
        "recommendation": "개발 환경 RDS는 Single-AZ로 전환하고 프로덕션만 Multi-AZ를 유지한다.",
    },
    "L1-009": {
        "title": "ECR lifecycle 정책 부재",
        "domain": "storage",
        "issue_type": "data",
        "severity": "medium",
        "recommendation": "ECR lifecycle 정책을 추가해 오래된 이미지를 자동 정리한다.",
    },
    "L1-010": {
        "title": "DynamoDB 용량 과잉 프로비저닝",
        "domain": "database",
        "issue_type": "overprovisioned",
        "severity": "high",
        "recommendation": "실사용량에 맞춰 RCU/WCU를 축소하거나 On-Demand 모드로 전환한다.",
    },
    "L1-011": {
        "title": "S3 lifecycle 정책 부재",
        "domain": "storage",
        "issue_type": "data",
        "severity": "medium",
        "recommendation": "S3 lifecycle 정책을 추가해 오래된 객체를 저비용 스토리지 클래스로 이동한다.",
    },
    "L2-014": {
        "title": "Lambda 메모리 과잉 할당",
        "domain": "compute",
        "issue_type": "overprovisioned",
        "severity": "high",
        "recommendation": "실측 duration을 기준으로 Lambda 메모리를 512MB 수준으로 축소한다.",
    },
    "L2-015": {
        "title": "Lambda timeout 과잉",
        "domain": "compute",
        "issue_type": "overprovisioned",
        "severity": "high",
        "recommendation": "P99 실행시간에 맞춰 timeout을 축소하고 재시도 폭증을 차단한다.",
    },
    "L2-020": {
        "title": "미사용 RDS Read Replica",
        "domain": "database",
        "issue_type": "unused",
        "severity": "high",
        "recommendation": "사용하지 않는 Read Replica를 제거하거나 실제 read routing을 구성한다.",
    },
    "L3-025": {
        "title": "Single-AZ NAT로 인한 cross-AZ 비용",
        "domain": "network",
        "issue_type": "network",
        "severity": "medium",
        "recommendation": "각 AZ별 NAT Gateway와 AZ-local route table을 사용한다.",
    },
    "L3-029": {
        "title": "S3 트래픽 NAT 경유",
        "domain": "storage",
        "issue_type": "network",
        "severity": "high",
        "recommendation": "현재 리전의 S3 Gateway Endpoint를 private route table에 연결해 S3 트래픽을 NAT 경로에서 제거한다.",
    },
    "L3-031": {
        "title": "비용 할당 태그 누락",
        "domain": "governance",
        "issue_type": "tagging",
        "severity": "medium",
        "recommendation": "provider default_tags와 필수 CostCenter 태그 정책을 적용한다.",
    },
    "L3-038": {
        "title": "EKS 노드 과잉 프로비저닝",
        "domain": "compute",
        "issue_type": "overprovisioned",
        "severity": "high",
        "recommendation": "pod request를 실제 사용량에 맞추고 초과 노드를 축소한다.",
    },
}


# L3-031(태그 거버넌스)에서 "태그가 붙어 있어야 마땅한" 리소스 타입과 필수 태그 목록.
TAGGABLE_TYPES = {
    "aws_instance",
    "aws_db_instance",
    "aws_s3_bucket",
    "aws_lb",
    "aws_eks_cluster",
    "aws_ecr_repository",
}
REQUIRED_COST_TAGS = ("cost-center", "team", "environment", "project")


def _contains(body: str, pattern: str) -> bool:
    """리소스 블록 본문에 정규식 pattern이 한 번이라도 나오면 True."""
    return re.search(pattern, body, re.MULTILINE) is not None


def _metric_names(bundle: Bundle, resource: Resource) -> set[str]:
    """그 리소스가 가진 지표 이름 집합을 돌려준다."""
    return set(metric_summary_for(bundle, resource.name).get("metrics", {}).keys())


def _resource_has_tag(body: str, tag: str) -> bool:
    """리소스 블록 안에 `tag = ...` 형태로 해당 태그가 설정돼 있으면 True."""
    return re.search(rf"(^|\s){re.escape(tag)}\s*=", body) is not None


def _provider_region(terraform: str) -> str | None:
    """`provider "aws"` 블록에서 region 값을 뽑는다 (예: "ap-northeast-2")."""
    match = re.search(r'provider\s+"aws"\s*{[\s\S]*?region\s*=\s*"([^"]+)"', terraform)
    return match.group(1) if match else None


def _make_findings(
    pattern_id: str,
    resources: list[Resource],
    evidence: list[str],
    bundle: Bundle,
) -> list[Finding]:
    """탐지된 리소스 목록을 Finding 객체 목록으로 변환하는 공통 헬퍼.

    제목·도메인·심각도 같은 고정 정보는 PATTERN_META에서 채운다. 탐지된 리소스가
    없으면 빈 목록을 돌려준다 (= 이 패턴은 발견되지 않음).
    """
    if not resources:
        return []
    meta = PATTERN_META[pattern_id]
    return [
        Finding(
            pattern_id=pattern_id,
            title=meta["title"],
            domain=meta["domain"],
            resource=resource.name,
            issue_type=meta["issue_type"],
            severity=meta["severity"],
            evidence=evidence,
            recommendation=meta["recommendation"],
            estimated_savings=0.0,
            resource_type=resource.resource_type,
        )
        for resource in resources
    ]


def detect_l1_004(component: Component, bundle: Bundle) -> list[Finding]:
    """L1-004: 개발 환경(dev) DB인데 Multi-AZ 이중화가 켜져 있는 경우."""
    resources = [
        resource
        for resource in component.resources
        if resource.resource_type == "aws_db_instance"
        and _contains(resource.body, r'Environment\s*=\s*"dev"')
        and _contains(resource.body, r"multi_az\s*=\s*true")
    ]
    return _make_findings(
        "L1-004",
        resources,
        ["dev 태그와 multi_az=true가 같은 DB 블록에 존재한다."],
        bundle,
    )


def detect_l1_009(component: Component, bundle: Bundle) -> list[Finding]:
    """L1-009: ECR 저장소는 있는데 연결된 lifecycle 정리 정책이 없는 경우."""
    # 먼저 lifecycle 정책이 가리키는 ECR repository 이름을 모은다 (= 이미 정책이 붙은 것).
    lifecycle_targets = {
        match.group(1)
        for resource in component.resources
        if resource.resource_type == "aws_ecr_lifecycle_policy"
        for match in [re.search(r"aws_ecr_repository\.([A-Za-z0-9_-]+)\.name", resource.body)]
        if match
    }
    # 정책이 붙지 않은 repository만 낭비로 본다.
    resources = [
        resource
        for resource in component.resources
        if resource.resource_type == "aws_ecr_repository"
        and resource.name not in lifecycle_targets
    ]
    evidence = ["ECR repository는 존재하지만 같은 컴포넌트에 lifecycle 정책 리소스가 없다."]
    image_counts = metric_means(bundle, [resource.name for resource in resources], "image_count")
    if image_counts:
        evidence.append(
            f"정책 미적용 repo의 image_count 평균 {round(sum(image_counts) / len(image_counts))}개로 "
            "이미지가 정리 없이 누적되고 있다."
        )
    return _make_findings("L1-009", resources, evidence, bundle)


def detect_l1_010(component: Component, bundle: Bundle) -> list[Finding]:
    """L1-010: DynamoDB가 PROVISIONED 모드라 고정 용량 비용을 계속 무는 경우."""
    resources = [
        resource
        for resource in component.resources
        if resource.resource_type == "aws_dynamodb_table"
        and _contains(resource.body, r'billing_mode\s*=\s*"PROVISIONED"')
    ]
    return _make_findings(
        "L1-010",
        resources,
        ["billing_mode=PROVISIONED이며 큰 read/write capacity가 함께 보인다."],
        bundle,
    )


def detect_l1_011(component: Component, bundle: Bundle) -> list[Finding]:
    """L1-011: lifecycle 정책이 없는 S3 bucket. 단, 같은 컴포넌트에 정책이 붙은
    bucket이 하나라도 있어야 finding으로 본다 (정책 누락의 명확한 증거가 필요).
    """
    # lifecycle configuration이 가리키는 S3 bucket 이름 = 이미 정책이 있는 bucket.
    lifecycle_targets = {
        match.group(1)
        for resource in component.resources
        if resource.resource_type == "aws_s3_bucket_lifecycle_configuration"
        for match in [re.search(r"aws_s3_bucket\.([A-Za-z0-9_-]+)\.id", resource.body)]
        if match
    }
    resources = [
        resource
        for resource in component.resources
        if resource.resource_type == "aws_s3_bucket"
        and resource.name not in lifecycle_targets
    ]
    # Avoid treating any arbitrary component with plain S3 buckets as a lifecycle
    # problem; require at least one lifecycle-managed peer as evidence of a
    # bucket family where policy drift exists.
    if not lifecycle_targets:
        return []
    return _make_findings(
        "L1-011",
        resources,
        ["S3 bucket에 대응하는 lifecycle configuration을 찾지 못했다."],
        bundle,
    )


def detect_l2_014(component: Component, bundle: Bundle) -> list[Finding]:
    """L2-014: Lambda 메모리가 2048MB 이상으로 과하게 할당된 경우."""
    resources = [
        resource
        for resource in component.resources
        if resource.resource_type == "aws_lambda_function"
        and _contains(resource.body, r"memory_size\s*=\s*(?:2048|3008|4096)")
    ]
    return _make_findings(
        "L2-014",
        resources,
        ["Lambda memory_size가 3008MB 수준으로 높게 설정되어 있다."],
        bundle,
    )


def detect_l2_015(component: Component, bundle: Bundle) -> list[Finding]:
    """L2-015: Lambda timeout이 최대치(900초)로 설정돼 실패 호출 과금이 큰 경우."""
    resources = [
        resource
        for resource in component.resources
        if resource.resource_type == "aws_lambda_function"
        and _contains(resource.body, r"timeout\s*=\s*900")
    ]
    return _make_findings(
        "L2-015",
        resources,
        ["Lambda timeout=900초가 설정되어 실패 호출의 과금 상한이 매우 크다."],
        bundle,
    )


def detect_l2_020(component: Component, bundle: Bundle) -> list[Finding]:
    """L2-020: replicate_source_db가 설정된 RDS Read Replica (미사용 의심)."""
    resources = [
        resource
        for resource in component.resources
        if resource.resource_type == "aws_db_instance"
        and "replicate_source_db" in resource.body
    ]
    return _make_findings(
        "L2-020",
        resources,
        ["replicate_source_db가 설정된 Read Replica가 다수 존재한다."],
        bundle,
    )


def detect_l3_025(component: Component, bundle: Bundle) -> list[Finding]:
    """L3-025: 중앙 NAT 한 곳에 여러 AZ subnet이 묶여 cross-AZ 전송비가 발생.

    근거 두 가지: NAT 지표에 cross-AZ 트래픽이 0보다 크고, route table이
    `all_private`로 여러 AZ를 한 경로에 몰아넣고 있다.
    """
    # cross-AZ 트래픽이 실제로 발생 중인 NAT Gateway.
    nat_resources = [
        resource
        for resource in component.resources
        if resource.resource_type == "aws_nat_gateway"
        and metric_summary_for(bundle, resource.name)
        .get("metrics", {})
        .get("cross_az_bytes_mb_per_hr", {})
        .get("mean", 0)
        > 0
    ]
    # 여러 AZ subnet을 한 경로에 묶은 route table.
    route_tables = [
        resource
        for resource in component.resources
        if resource.resource_type == "aws_route_table"
        and 'associated_subnets = "all_private"' in resource.body
    ]
    resources = nat_resources + route_tables
    return _make_findings(
        "L3-025",
        resources,
        [
            'route table이 associated_subnets="all_private"로 표현되어 있다.',
            "NAT 메트릭에서 cross_az_bytes_mb_per_hr가 0보다 크다.",
        ],
        bundle,
    )


def detect_l3_029(component: Component, bundle: Bundle) -> list[Finding]:
    """L3-029: S3로 가는 트래픽이 Gateway Endpoint 대신 NAT 경로로 새는 경우.

    `nat_bytes_out_mb_per_hr` 지표가 있는 리소스를 finding으로 잡고, direct S3
    경로 리소스·Gateway Endpoint·provider와 endpoint의 리전 불일치를 근거로 덧붙인다.
    """
    # NAT egress 지표가 있으면 S3 트래픽이 NAT를 타고 있을 가능성이 있다.
    resources = [
        resource
        for resource in component.resources
        if "nat_bytes_out_mb_per_hr" in _metric_names(bundle, resource)
    ]
    evidence = ["리소스 메트릭에 nat_bytes_out_mb_per_hr와 s3_request_count_per_hr가 함께 존재한다."]
    direct_s3_resources = [
        resource
        for resource in component.resources
        if "s3_direct_bytes_mb_per_hr" in _metric_names(bundle, resource)
    ]
    gateway_endpoints = [
        resource
        for resource in component.resources
        if resource.resource_type == "aws_vpc_endpoint"
    ]
    if direct_s3_resources:
        evidence.append(f"같은 컴포넌트에 direct S3 경로 메트릭을 가진 리소스 {len(direct_s3_resources)}개가 있다.")
    if gateway_endpoints:
        evidence.append(f"같은 컴포넌트에 Gateway Endpoint 리소스 {len(gateway_endpoints)}개가 있다.")
        provider_region = _provider_region(bundle.terraform)
        endpoint_regions = {
            match.group(1)
            for resource in gateway_endpoints
            for match in [re.search(r'com\.amazonaws\.([^."]+)\.s3', resource.body)]
            if match
        }
        if provider_region and endpoint_regions and provider_region not in endpoint_regions:
            evidence.append(
                f"provider 리전은 {provider_region}인데 endpoint service_name은 {', '.join(sorted(endpoint_regions))} 리전을 가리킨다."
            )
    return _make_findings(
        "L3-029",
        resources,
        evidence,
        bundle,
    )


def detect_l3_031(component: Component, bundle: Bundle) -> list[Finding]:
    """L3-031: 필수 비용 할당 태그 누락 (거버넌스 패턴).

    다른 탐지기와 달리 컴포넌트 단위가 아니라 번들 전체를 본다. 전달된
    component 인자는 무시하고, bundle.components 전체를 훑는다.
    """
    # provider에 default_tags가 이미 있으면 공통 태그가 깔린 것이므로 낭비 아님.
    if "default_tags" in bundle.terraform:
        return []
    # 이 시나리오가 애초에 '태그 거버넌스' 문제인지 README/hint 키워드로 먼저 확인.
    tag_context = f"{bundle.readme}\n{bundle.hint}".lower()
    if not any(keyword in tag_context for keyword in ["tag governance", "tag 누락", "비용 할당 태그", "cost allocation tag"]):
        return []
    noncompliant = [
        resource
        for comp in bundle.components
        for resource in comp.resources
        if resource.resource_type in TAGGABLE_TYPES
        and not all(_resource_has_tag(resource.body, tag) for tag in REQUIRED_COST_TAGS)
    ]
    evidence = [
        "provider 블록에 default_tags가 없고, cost-center/team/environment/project 태그가 "
        "리소스별로 누락되어 있다."
    ]
    coverage = metric_means(bundle, [resource.name for resource in noncompliant], "tag_coverage")
    if coverage:
        evidence.append(
            f"미준수 리소스의 tag_coverage 평균이 {round(sum(coverage) / len(coverage), 1)}%로 "
            "사실상 태깅되지 않았다."
        )
    all_resource_names = [resource.name for comp in bundle.components for resource in comp.resources]
    unallocated = metric_means(bundle, all_resource_names, "unallocated_spend_ratio")
    if unallocated:
        evidence.append(
            f"unallocated_spend_ratio 평균 {round(sum(unallocated) / len(unallocated), 1)}%만큼 "
            "비용이 미할당 상태로 집계된다."
        )
    return _make_findings("L3-031", noncompliant, evidence, bundle)


def detect_l3_038(component: Component, bundle: Bundle) -> list[Finding]:
    """L3-038: EKS 노드가 m5.2xlarge로 고정돼 노드 플릿이 과도하게 큰 경우."""
    resources = [
        resource
        for resource in component.resources
        if resource.resource_type == "aws_instance"
        and 'instance_type = "m5.2xlarge"' in resource.body
    ]
    evidence = ["m5.2xlarge 노드가 다수 존재해 노드 플릿이 과도하게 크다."]
    cpu = metric_means(bundle, [resource.name for resource in resources], "node_cpu_percent")
    if cpu:
        evidence.append(
            f"해당 노드의 node_cpu_percent 평균 {round(sum(cpu) / len(cpu), 1)}%로 "
            "프로비저닝 대비 사용률이 매우 낮다."
        )
    return _make_findings("L3-038", resources, evidence, bundle)


# 패턴 ID → 탐지기 함수 레지스트리. 새 탐지기를 추가하려면 여기에 등록만 하면 된다.
DETECTORS: dict[str, Callable[[Component, Bundle], list[Finding]]] = {
    "L1-004": detect_l1_004,
    "L1-009": detect_l1_009,
    "L1-010": detect_l1_010,
    "L1-011": detect_l1_011,
    "L2-014": detect_l2_014,
    "L2-015": detect_l2_015,
    "L2-020": detect_l2_020,
    "L3-025": detect_l3_025,
    "L3-029": detect_l3_029,
    "L3-031": detect_l3_031,
    "L3-038": detect_l3_038,
}


def detect_component(component: Component, bundle: Bundle) -> list[Finding]:
    """한 컴포넌트에 등록된 모든 탐지기를 돌려 발견된 finding을 모은다.

    어떤 탐지기를 쓸지 컴포넌트 주석의 패턴 ID로 고르지 않는다. 모든 탐지기를
    전부 돌린다 — "여기 답은 이거"라는 힌트를 보지 않겠다는 뜻이다.
    """
    findings: list[Finding] = []
    for pattern_id, detector in DETECTORS.items():
        # L3-031은 번들 전역 패턴이라 컴포넌트마다 돌리면 중복만 생긴다. 여기선 건너뛰고
        # detect_bundle_globals()에서 딱 한 번만 돌린다.
        if pattern_id == "L3-031":
            continue
        findings.extend(detector(component, bundle))
    return findings


def detect_bundle_globals(bundle: Bundle) -> list[Finding]:
    """번들 전체 단위로만 의미 있는 패턴(현재는 L3-031)을 한 번 검사한다."""
    if not bundle.components:
        return []
    return detect_l3_031(bundle.components[0], bundle)


def group_findings_by_pattern(findings: list[Finding]) -> dict[str, list[Finding]]:
    """finding 목록을 패턴 ID별로 묶는다 (산출물 생성 단계에서 자주 쓴다)."""
    grouped: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        grouped[finding.pattern_id].append(finding)
    return dict(grouped)
