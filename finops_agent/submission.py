from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from .models import PipelineResult


def _repo_from_group_config(repo_root: Path) -> str:
    config = (repo_root / "platform" / "config" / "group.yaml").read_text(encoding="utf-8")
    match = re.search(r'^\s*repo:\s*"([^"]+)"', config, re.MULTILINE)
    if not match:
        raise ValueError("platform/config/group.yaml에서 원본 repo를 찾지 못했습니다.")
    return match.group(1)


def build_issue_body(result: PipelineResult) -> str:
    submission = result.artifacts["submission"].read_text(encoding="utf-8").rstrip()
    solution = result.artifacts["solution"].read_text(encoding="utf-8").rstrip()
    report_name = result.artifacts["report"].name
    return f"""{submission}

### Optimized Terraform
```hcl
{solution}
```

### Attached Reports
{report_name}
_(Files committed to submissions/ directory)_
"""


class GitHubSubmissionClient:
    def __init__(self, repo: str, token: str) -> None:
        self.repo = repo
        self.token = token

    @classmethod
    def from_environment(cls, repo_root: Path) -> "GitHubSubmissionClient":
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or ""
        if not token:
            try:
                token = subprocess.check_output(
                    ["gh", "auth", "token"], text=True
                ).strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        if not token:
            raise RuntimeError("GITHUB_TOKEN 또는 GH_TOKEN이 필요합니다. gh CLI 로그인 또는 환경변수 설정 필요.")
        repo = os.getenv("FINOPS_SUBMISSION_REPO") or _repo_from_group_config(repo_root)
        return cls(repo=repo, token=token)

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        payload: dict | None = None,
        allow_not_found: bool = False,
    ) -> dict | None:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(
            f"https://api.github.com{endpoint}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            if allow_not_found and exc.code == 404:
                return None
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {exc.code}: {detail}") from exc

    def upload_text_file(self, repo_path: str, content: str, message: str) -> dict | None:
        existing = self._request(
            "GET",
            f"/repos/{self.repo}/contents/{repo_path}",
            allow_not_found=True,
        )
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        }
        if existing and existing.get("sha"):
            payload["sha"] = existing["sha"]
        return self._request(
            "PUT",
            f"/repos/{self.repo}/contents/{repo_path}",
            payload=payload,
        )

    def create_issue(self, title: str, body: str) -> dict:
        result = self._request(
            "POST",
            f"/repos/{self.repo}/issues",
            payload={"title": title, "body": body, "labels": ["submission"]},
        )
        assert result is not None
        return result


def submit_result(
    result: PipelineResult,
    *,
    repo_root: Path,
    member: str,
    season: int,
) -> dict:
    client = GitHubSubmissionClient.from_environment(repo_root)
    bundle = result.bundle
    base_path = f"members/{member}/season-{season}/submissions/week-{bundle.week:02d}/{bundle.scenario_id}"
    solution = result.artifacts["solution"].read_text(encoding="utf-8")
    report = result.artifacts["report"].read_text(encoding="utf-8")
    issue_body = build_issue_body(result)

    client.upload_text_file(
        f"{base_path}/solution.tf",
        solution,
        f"Upload solution.tf ({member}, {bundle.scenario_id})",
    )
    client.upload_text_file(
        f"{base_path}/report.md",
        report,
        f"Upload report.md ({member}, {bundle.scenario_id})",
    )
    issue = client.create_issue(
        f"[Week {bundle.week}] {bundle.scenario_id} 답안 제출",
        issue_body,
    )
    return issue
