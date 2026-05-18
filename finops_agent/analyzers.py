from __future__ import annotations

import json
import time
from collections import defaultdict

from .detectors import detect_bundle_globals, detect_component
from .llm import BaseProvider, estimate_tokens
from .models import AnalyzerResult, Bundle, EmergentFinding, Finding


def _serialize_findings(findings: list[Finding]) -> list[dict]:
    return [
        {
            "pattern_id": finding.pattern_id,
            "resource": finding.resource,
            "title": finding.title,
            "domain": finding.domain,
        }
        for finding in findings
    ]


def _patterns(findings: list[Finding]) -> list[str]:
    return sorted({finding.pattern_id for finding in findings})


def _context_for_bundle(bundle: Bundle) -> str:
    return "\n".join(
        [
            bundle.readme,
            bundle.terraform,
            json.dumps(bundle.metrics_summary, ensure_ascii=False),
            json.dumps(bundle.cost_report, ensure_ascii=False),
            bundle.hint,
        ]
    )


def _context_for_components(bundle: Bundle, components: list) -> str:
    component_resource_names = {resource.name for component in components for resource in component.resources}
    component_metric_names = component_resource_names | {
        resource_name.rsplit("_", 1)[0]
        for resource_name in component_resource_names
        if resource_name.rsplit("_", 1)[-1].isdigit()
    }
    isolated_metrics = {
        "metadata": bundle.metrics_summary.get("metadata", {}),
        "resources": {
            name: data
            for name, data in bundle.metrics_summary.get("resources", {}).items()
            if name in component_metric_names
        },
    }
    return "\n".join(
        [
            bundle.readme,
            *(component.text for component in components),
            json.dumps(isolated_metrics, ensure_ascii=False),
            json.dumps(bundle.cost_report.get("summary", {}), ensure_ascii=False),
        ]
    )


def run_baseline(bundle: Bundle, provider: BaseProvider) -> AnalyzerResult:
    start = time.perf_counter()
    findings = [finding for component in bundle.components for finding in detect_component(component, bundle)]
    findings.extend(detect_bundle_globals(bundle))
    context = _context_for_bundle(bundle)
    prompt = f"Summarize the following findings as a FinOps analyst: {_serialize_findings(findings)}"
    llm = provider.complete("You are a FinOps analyst.", prompt)
    return AnalyzerResult(
        name="single",
        findings=findings,
        patterns_found=_patterns(findings),
        context_tokens_est=estimate_tokens(context),
        llm_input_tokens=llm.input_tokens,
        llm_output_tokens=llm.output_tokens,
        llm_tokens_estimated=llm.estimated,
        wall_clock_sec=round(time.perf_counter() - start, 6),
        llm_usage=llm.__dict__,
        warnings=[llm.error] if llm.error else [],
    )


def run_multi(bundle: Bundle, provider: BaseProvider) -> AnalyzerResult:
    start = time.perf_counter()
    by_domain: dict[str, list] = defaultdict(list)
    component_findings = {
        component.index: detect_component(component, bundle)
        for component in bundle.components
    }
    for component in bundle.components:
        inferred_domains = {
            finding.domain for finding in component_findings[component.index]
        }
        domain = sorted(inferred_domains)[0] if inferred_domains else "general"
        by_domain[domain].append(component)

    findings: list[Finding] = []
    context_tokens_est = 0
    llm_input_tokens = 0
    llm_output_tokens = 0
    llm_tokens_estimated = False
    warnings: list[str] = []
    specialist_summaries: list[dict] = []

    for domain, components in sorted(by_domain.items()):
        domain_findings = [finding for component in components for finding in component_findings[component.index]]
        findings.extend(domain_findings)
        context = _context_for_components(bundle, components)
        prompt = f"Summarize {domain} findings: {_serialize_findings(domain_findings)}"
        llm = provider.complete(f"You are the {domain} FinOps specialist.", prompt)
        context_tokens_est += estimate_tokens(context)
        llm_input_tokens += llm.input_tokens
        llm_output_tokens += llm.output_tokens
        llm_tokens_estimated = llm_tokens_estimated or llm.estimated
        if llm.error:
            warnings.append(f"{domain}: {llm.error}")
        specialist_summaries.append(
            {
                "domain": domain,
                "patterns": _patterns(domain_findings),
                "resources": [finding.resource for finding in domain_findings],
            }
        )

    orchestrator_prompt = f"Connect these domain findings: {specialist_summaries}"
    orchestrator_llm = provider.complete("You are the FinOps orchestrator.", orchestrator_prompt)
    global_findings = detect_bundle_globals(bundle)
    findings.extend(global_findings)
    context_tokens_est += estimate_tokens(orchestrator_prompt)
    llm_input_tokens += orchestrator_llm.input_tokens
    llm_output_tokens += orchestrator_llm.output_tokens
    llm_tokens_estimated = llm_tokens_estimated or orchestrator_llm.estimated
    if orchestrator_llm.error:
        warnings.append(f"orchestrator: {orchestrator_llm.error}")

    return AnalyzerResult(
        name="multi",
        findings=findings,
        patterns_found=_patterns(findings),
        context_tokens_est=context_tokens_est,
        llm_input_tokens=llm_input_tokens,
        llm_output_tokens=llm_output_tokens,
        llm_tokens_estimated=llm_tokens_estimated,
        wall_clock_sec=round(time.perf_counter() - start, 6),
        llm_usage=orchestrator_llm.__dict__,
        warnings=warnings,
    )


def correlate(findings: list[Finding]) -> list[EmergentFinding]:
    patterns = {finding.pattern_id for finding in findings}
    emergent: list[EmergentFinding] = []
    if {"L3-029", "L3-025"} <= patterns:
        emergent.append(
            EmergentFinding(
                title="S3 대량 트래픽이 중앙 NAT 경로에서 이중 과금된다",
                detail="Storage 관점은 NAT bytes의 payload가 S3임을 설명하고, Network 관점은 같은 bytes가 cross-AZ 경로까지 타고 있음을 설명한다.",
                chain="S3-heavy analytics traffic → centralized NAT → NAT processing + cross-AZ transfer",
                recommendation="먼저 S3 Gateway Endpoint로 대량 payload를 제거한 뒤, 남은 egress만 AZ-local NAT로 정리한다.",
            )
        )
    if {"L2-014", "L1-011"} <= patterns:
        emergent.append(
            EmergentFinding(
                title="캐시 부재가 Lambda 비용과 S3 비용을 동시에 키운다",
                detail="컴퓨트와 스토리지를 따로 보면 정상처럼 보이지만, 매 호출마다 S3를 읽는 구조가 두 비용을 함께 증폭시킨다.",
                chain="Lambda invocation → repeated S3 GET → duration + request cost amplification",
                recommendation="애플리케이션 캐시를 도입하고 오래된 객체는 lifecycle로 정리한다.",
            )
        )
    if {"L2-014", "L2-015", "L1-010"} <= patterns:
        emergent.append(
            EmergentFinding(
                title="재시도 루프가 서버리스와 DB 비용을 함께 증폭한다",
                detail="긴 Lambda timeout과 과잉 용량의 DynamoDB가 결합되면 실패 요청이 여러 번 재처리되며 비용이 연쇄적으로 증가한다.",
                chain="API traffic → Lambda retry → DynamoDB throttle → repeated work",
                recommendation="timeout을 줄이고 retry/backpressure를 조정한 뒤 DynamoDB 용량을 재설계한다.",
            )
        )
    return emergent
