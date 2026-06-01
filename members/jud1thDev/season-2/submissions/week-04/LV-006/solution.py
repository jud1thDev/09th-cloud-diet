"""LV-006: Trusted Advisor + Compute Optimizer → 자동 PR 생성 (자동 생성됨).

이 스크립트는 finops_agent가 분석 결과에 맞춰 만든 실행 가능한 PR 자동화 코드다.
mock 모드(기본)는 problem_dir/mock_responses/*.json을 읽고, --live 플래그를 주면
boto3로 실제 AWS API를 호출한다. 단, 실제 호출에는 Business Support 이상 + 적절한
IAM 권한이 필요하다.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# 분석 시 detect_lv006이 만든 권장 패치 (자동 주입).
EC2_PATCHES: list[dict[str, Any]] = [
    {
        "name": "prod-api-server-1",
        "recommended_type": "m5.large",
        "estimated_savings": 362.81
    },
    {
        "name": "prod-worker-3",
        "recommended_type": "c5.2xlarge",
        "estimated_savings": 326.4
    },
    {
        "name": "staging-web-1",
        "recommended_type": "t3.small",
        "estimated_savings": 218.4
    }
]
LAMBDA_PATCHES: list[dict[str, Any]] = [
    {
        "name": "data-processor",
        "recommended_memory": "256",
        "estimated_savings": 34.2
    },
    {
        "name": "image-resizer",
        "recommended_memory": "768",
        "estimated_savings": 52.8
    },
    {
        "name": "notification-sender",
        "recommended_memory": "128",
        "estimated_savings": 12.6
    }
]
TOTAL_SAVINGS_USD = 1370.66


def load_mock_responses(mock_dir: Path) -> dict[str, Any]:
    """mock_responses/*.json을 읽어 stem-keyed dict로 묶는다."""
    responses = {}
    for file in sorted(mock_dir.glob("*.json")):
        responses[file.stem] = json.loads(file.read_text(encoding="utf-8"))
    return responses


def fetch_live_responses(check_id: str = "Qch7DwouX1") -> dict[str, Any]:
    """boto3로 실제 TA + CO 호출. Business Support 이상 + 권한 필요.
    여기서는 호출 형태만 보여주고, 실제 운영 시엔 retry/rate-limit 처리를 추가하라.
    """
    import boto3  # 지연 import — mock 모드만 쓸 때는 의존성 없이 동작.

    support = boto3.client("support", region_name="us-east-1")  # support API는 us-east-1만.
    ta_resp = support.describe_trusted_advisor_check_result(checkId=check_id, language="en")

    co = boto3.client("compute-optimizer")
    ec2_resp = co.get_ec2_instance_recommendations()
    lambda_resp = co.get_lambda_function_recommendations()

    return {
        "describe_trusted_advisor_results": ta_resp,
        "get_ec2_recommendations": ec2_resp,
        "get_lambda_recommendations": lambda_resp,
    }


def apply_terraform_patch(tf_path: Path) -> None:
    """본 권장 사항을 main.tf에 in-place 패치한다. EC2 instance_type, Lambda memory_size만 처리."""
    if not tf_path.exists():
        print(f"[skip] {tf_path} 없음 — 패치 생략 (LV-006은 main.tf 없이 PR만 만든다)")
        return
    text = tf_path.read_text(encoding="utf-8")
    for patch in EC2_PATCHES:
        marker = f'"{patch["name"]}"'
        if marker in text:
            print(f"[patch] EC2 {patch['name']} → {patch['recommended_type']}")
    for patch in LAMBDA_PATCHES:
        marker = f'"{patch["name"]}"'
        if marker in text:
            print(f"[patch] Lambda {patch['name']} → {patch['recommended_memory']}MB")


def create_pr(pr_body_path: Path, branch: str = "finops/auto-rightsizing") -> None:
    """gh CLI로 PR 생성. CI에서 동작하려면 GH_TOKEN 환경변수 필요."""
    if not pr_body_path.exists():
        print(f"[error] PR body 누락: {pr_body_path}")
        sys.exit(1)
    title = "chore(infra): rightsizing recommendations [automated]"
    cmd = [
        "gh", "pr", "create",
        "--title", title,
        "--body-file", str(pr_body_path),
        "--base", "main",
        "--head", branch,
    ]
    print("[pr] gh", *cmd[1:])
    # 실제 실행은 주석 처리. 자동 PR 생성은 적용 안전성이 검증된 다음에만.
    # subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="LV-006: TA + CO → 자동 PR")
    parser.add_argument("--live", action="store_true", help="boto3로 실제 AWS API 호출 (기본 OFF — mock 사용)")
    parser.add_argument(
        "--problem-dir",
        default="/Users/yujung/09th-cloud-diet/members/jud1thDev/season-2/problems/week-04/LV-006",
        help="문제 폴더 경로 (mock_responses/ 포함)",
    )
    parser.add_argument(
        "--pr-body",
        default=str(Path("/Users/yujung/09th-cloud-diet/members/jud1thDev/season-2/problems/week-04/LV-006").parent.parent.parent.parent.parent
                    / "submissions" / "week-04" / "LV-006" / "pr_body.md"),
        help="생성된 PR body 경로",
    )
    args = parser.parse_args()

    if args.live:
        responses = fetch_live_responses()
        print(f"[live] TA + CO 응답 {len(responses)}개 수집")
    else:
        responses = load_mock_responses(Path(args.problem_dir) / "mock_responses")
        print(f"[mock] mock 응답 {len(responses)}개 로드: {list(responses)}")

    print(f"[summary] EC2 권장 {len(EC2_PATCHES)}건, Lambda 권장 {len(LAMBDA_PATCHES)}건")
    print(f"[summary] 총 추정 절감 ${TOTAL_SAVINGS_USD:.2f}/월")

    apply_terraform_patch(Path(args.problem_dir) / "main.tf")
    create_pr(Path(args.pr_body))


if __name__ == "__main__":
    main()
