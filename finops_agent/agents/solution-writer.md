---
name: solution-writer
role: writer
inputs: [Finding, EmergentFinding]
outputs: [str]
llm_calls: 1
retry: 0
---

# Solution Report Writer

> 검증된 `Finding[]` + `EmergentFinding[]`를 받아 `report.md` 본문 자연어 narrative를 생성한다. 파일 자체는 `artifacts.build_report()`가 만들고, 이 카드의 출력은 본문 한 섹션에만 들어간다.

## 역할

TBD — W2 5단계.

## 입력 신호

- `Finding[]` (reviewer 통과본)
- `EmergentFinding[]` (analyzers.correlate)
- bundle.readme · bundle.cost_report.summary

## 출력 포맷

마크다운 문자열 (300~500자):
- 시나리오 한 줄 요약
- 핵심 낭비 2~3개 (severity 기준)
- cross-service 결합 원인 1개 (있을 때만)
- 권장 조치 순서

## 도메인 원칙

TBD — W2 5단계. 후보:
- 토스 스타일 (`Documents/Obsidian Vault/CLAUDE.md` 참고): 짧은 문장, 메타담화 제거, 능동형
- "왜 낭비인가"를 수치로 — "메모리 1024MB 할당, 실측 평균 180MB" 식
