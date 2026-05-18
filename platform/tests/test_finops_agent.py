from __future__ import annotations

import json
from pathlib import Path

from finops_agent.runner import discover_assigned_problem_dirs, run_pipeline
from finops_agent.submission import build_issue_body


ROOT = Path(__file__).resolve().parents[2]


def test_xs005_compare_pipeline(tmp_path: Path) -> None:
    problem = ROOT / "members/jud1thDev/season-2/problems/week-03/XS-005"
    result = run_pipeline(problem, output_dir=tmp_path)

    assert result.bundle.level == "L3"
    assert set(result.selected.patterns_found) == {"L3-025", "L3-029"}
    assert result.emergent_findings

    analysis = json.loads((tmp_path / "analysis.json").read_text(encoding="utf-8"))
    measurements = json.loads((tmp_path / "measurements.json").read_text(encoding="utf-8"))
    solution = (tmp_path / "solution.tf").read_text(encoding="utf-8")
    submission = (tmp_path / "submission.md").read_text(encoding="utf-8")

    assert round(analysis["summary"]["total_monthly_savings_usd"]) == 426
    assert "alerts" in analysis
    assert measurements["true_recall_available"] is False
    assert measurements["single_agent"]["declared_pattern_coverage"] == 1.0
    assert measurements["multi_agent"]["declared_pattern_coverage"] == 1.0
    assert measurements["emergent_findings"]
    assert "comp2_route-table-7rc8oa" in solution
    assert 'associated_subnets = "same_az_private"' in solution
    assert 'service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"' in solution
    assert 'resource "aws_vpc_endpoint_route_table_association"' in solution
    assert "route_table_id  = aws_route_table.comp2_route-table-7rc8oa.id" in solution
    assert 'data "aws_route_table"' not in solution
    assert "for_each" not in solution
    assert "### Problem Identification" in submission


def _write_xs001_fixture(base: Path) -> Path:
    problem = base / "week-03" / "XS-001"
    (problem / "metrics").mkdir(parents=True)
    (problem / "README.md").write_text(
        "# XS-001\n\n- `L2-014`\n- `L1-011`\n",
        encoding="utf-8",
    )
    (problem / "main.tf").write_text(
        '''
provider "aws" {
  region = "us-east-1"
}

# Component 1/2 · seeded from L2-014
resource "aws_lambda_function" "lambda_big" {
  memory_size = 3008
}

# Component 2/2 · seeded from L1-011
resource "aws_s3_bucket" "raw" {}
resource "aws_s3_bucket" "curated" {}
resource "aws_s3_bucket_lifecycle_configuration" "curated" {
  bucket = aws_s3_bucket.curated.id
}
''',
        encoding="utf-8",
    )
    (problem / "cost_report.json").write_text(
        json.dumps({"summary": {"avg_monthly_waste": 902}}),
        encoding="utf-8",
    )
    (problem / "metrics" / "metrics.json").write_text(
        json.dumps({"resources": {}}),
        encoding="utf-8",
    )
    return problem


def test_xs001_detects_l1_and_l2_patterns(tmp_path: Path) -> None:
    problem = _write_xs001_fixture(tmp_path)
    result = run_pipeline(problem, output_dir=tmp_path)

    assert result.bundle.level == "L2"
    assert set(result.selected.patterns_found) == {"L1-011", "L2-014"}
    analysis = json.loads((tmp_path / "analysis.json").read_text(encoding="utf-8"))
    assert "unit_economics" in analysis["analysis"]


def test_ma003_detects_multi_domain_patterns(tmp_path: Path) -> None:
    problem = ROOT / "members/jud1thDev/season-2/problems/week-02/MA-003"
    result = run_pipeline(problem, output_dir=tmp_path)

    assert result.bundle.level == "L3"
    assert {"L1-009", "L3-031", "L3-038"} <= set(result.selected.patterns_found)


def test_l3_031_counts_noncompliant_resources(tmp_path: Path) -> None:
    problem = ROOT / "members/jud1thDev/season-2/problems/week-02/MA-003"
    result = run_pipeline(problem, output_dir=tmp_path)

    l3_031 = [f for f in result.selected.findings if f.pattern_id == "L3-031"]
    assert len(l3_031) == 51
    submission = (tmp_path / "submission.md").read_text(encoding="utf-8")
    assert "51개 리소스가 cost-center" in submission
    assert "aws_instance 35개" in submission


def test_solution_downgrades_eks_nodes(tmp_path: Path) -> None:
    problem = ROOT / "members/jud1thDev/season-2/problems/week-02/MA-003"
    run_pipeline(problem, output_dir=tmp_path)

    solution = (tmp_path / "solution.tf").read_text(encoding="utf-8")
    assert 'instance_type = "m5.2xlarge"' not in solution
    assert 'instance_type = "m5.large"' in solution


def test_l1_009_evidence_includes_image_count(tmp_path: Path) -> None:
    problem = ROOT / "members/jud1thDev/season-2/problems/week-02/MA-003"
    result = run_pipeline(problem, output_dir=tmp_path)

    l1_009 = [f for f in result.selected.findings if f.pattern_id == "L1-009"]
    assert l1_009
    assert any("image_count" in line for line in l1_009[0].evidence)


def test_l3_038_evidence_includes_cpu_metric(tmp_path: Path) -> None:
    problem = ROOT / "members/jud1thDev/season-2/problems/week-02/MA-003"
    result = run_pipeline(problem, output_dir=tmp_path)

    l3_038 = [f for f in result.selected.findings if f.pattern_id == "L3-038"]
    assert l3_038
    assert any("node_cpu_percent" in line for line in l3_038[0].evidence)


def test_discovers_assigned_problem_from_week_assignment() -> None:
    problems = discover_assigned_problem_dirs(
        ROOT,
        member="jud1thDev",
        season=2,
        week=3,
    )

    assert [problem.name for problem in problems] == ["XS-005"]


def test_issue_body_includes_terraform_and_attached_report(tmp_path: Path) -> None:
    problem = ROOT / "members/jud1thDev/season-2/problems/week-03/XS-005"
    result = run_pipeline(problem, output_dir=tmp_path)
    body = build_issue_body(result)

    assert "### Optimized Terraform" in body
    assert "### Attached Reports" in body
    assert "report.md" in body
