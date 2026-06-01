#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from finops_agent.runner import discover_assigned_problem_dirs, run_pipeline
from finops_agent.submission import submit_result


def _prompt_week() -> int:
    raw = input("분석할 주차를 입력하세요 (예: 3): ").strip()
    if not raw:
        raise SystemExit("주차가 비어 있습니다.")
    try:
        week = int(raw)
    except ValueError as exc:
        raise SystemExit("주차는 숫자로 입력해야 합니다.") from exc
    if week <= 0:
        raise SystemExit("주차는 1 이상의 숫자여야 합니다.")
    return week


def _approve_submission() -> bool:
    answer = input("원본 저장소에 지금 제출할까요? [y/N]: ").strip()
    return answer.lower() == "y"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the reusable weekly FinOps agent pipeline.")
    parser.add_argument("--mode", choices=["compare", "single", "multi", "agentic"], default="compare")
    parser.add_argument("--provider", choices=["local", "openai", "claude"], default="local")
    parser.add_argument("--output-dir", help="Optional custom artifact directory")
    parser.add_argument("--week", type=int, help="Optional week number. If omitted, the CLI prompts interactively.")
    parser.add_argument("--member", default="jud1thDev", help="Member id used for assignment discovery")
    parser.add_argument("--season", type=int, default=2, help="Season number used for assignment discovery")
    args = parser.parse_args()

    week = args.week or _prompt_week()
    repo_root = Path(__file__).resolve().parent
    problem_dirs = discover_assigned_problem_dirs(
        repo_root,
        member=args.member,
        season=args.season,
        week=week,
    )
    scenarios = ", ".join(path.name for path in problem_dirs)
    print(f"할당 문제 발견: week-{week:02d} → {scenarios}")

    for idx, problem_dir in enumerate(problem_dirs, start=1):
        if idx > 1:
            print()
        output_dir = args.output_dir
        if output_dir and len(problem_dirs) > 1:
            output_dir = str(Path(output_dir) / problem_dir.name)
        result = run_pipeline(
            problem_dir,
            mode=args.mode,
            provider_name=args.provider,
            output_dir=output_dir,
        )
        print(f"Scenario: {result.bundle.scenario_id}")
        print(f"Mode: {args.mode}")
        print(f"Patterns found: {', '.join(result.selected.patterns_found) or 'none'}")
        print(f"Issues found: {len(result.selected.findings)}")
        print(f"Artifacts: {next(iter(result.artifacts.values())).parent}")
        for name, path in result.artifacts.items():
            print(f"  - {name}: {path}")
        print("\n--- 제출 미리보기 ---")
        print(result.artifacts["submission"].read_text(encoding="utf-8"))
        print("첨부 예정:")
        print(f"  - solution.tf: {result.artifacts['solution']}")
        print(f"  - report.md: {result.artifacts['report']}")
        if _approve_submission():
            try:
                issue = submit_result(
                    result,
                    repo_root=repo_root,
                    member=args.member,
                    season=args.season,
                )
            except RuntimeError as exc:
                print(f"제출 실패: {exc}")
            else:
                print(f"제출 완료: {issue.get('html_url', issue.get('url', 'issue created'))}")
        else:
            print("제출하지 않았습니다. 산출물만 저장했습니다.")


if __name__ == "__main__":
    main()
