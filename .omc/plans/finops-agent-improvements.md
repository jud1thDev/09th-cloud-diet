# finops_agent 개선 계획

## 배경

MA-003 제출 답안([report.md](../../members/jud1thDev/season-2/submissions/week-02/MA-003/report.md))과
원본 저장소 이슈 #2(600gramSik)를 비교한 결과, 패턴 탐지(L1-009/L3-031/L3-038)는 정확했으나
리포트 품질이 에이전트가 확보한 데이터를 따라가지 못함. 4가지 결함을 수정한다.

검증된 사실(측정 완료):
- MA-003 taggable 리소스 61개 중 태그 미준수 **51개** (compliant 10). 현재 detector는 합성 리소스 1개만 생성.
- MA-003 `metrics/metrics.json`은 **비어있지 않음** — 61개 리소스 × 720 datapoint. 패턴 직결 메트릭 보유:
  `image_count`(정책없는 ECR 3개 평균 369), `tag_coverage`(미태깅 0.0), `unallocated_spend_ratio`(~48%),
  `node_cpu_percent`(EKS 노드 평균 24.5%).
- XS-005 README/hint에 태그 거버넌스 키워드 없음 → L3-031 guard가 정상 차단(기존 테스트 안전).
- `Finding(...)` 생성자는 [detectors.py](../../finops_agent/detectors.py) `_make_findings` 한 곳뿐.

## 요구사항 요약

1. **태그 탐지 실측화** — `detect_l3_031`이 전체 컴포넌트 리소스를 스캔해 필수 태그
   (`cost-center`/`team`/`environment`/`project`) 미준수 리소스마다 finding 1개 생성.
2. **Detector 메트릭-aware화** — `detect_l1_009`/`detect_l3_031`/`detect_l3_038`이
   각 패턴 직결 메트릭을 evidence로 소비. report.md에 메트릭 관측 섹션 추가.
3. **L3-038 solution.tf 실질 조치** — m5.2xlarge 인스턴스를 m5.large로 다운그레이드.
4. **Root cause 텍스트 보강** — L3-031/L3-038/L1-009의 problem/cause/solution 텍스트를 구조적으로.

## 구현 단계

### Step 1 — `Finding`에 `resource_type` 추가 (models.py)
- [models.py](../../finops_agent/models.py) `Finding` 데이터클래스에 `resource_type: str = ""` 필드 추가.
- 유형별 분포 출력(Step 4)에 필요. 생성자가 `_make_findings` 한 곳뿐이라 파급 없음.

### Step 2 — detectors.py
- 모듈 상수 추가: `TAGGABLE_TYPES`(6개 타입), `REQUIRED_COST_TAGS`(4개 태그).
- 헬퍼 `_metric_mean(bundle, name, metric)` 추가 (artifacts.py와 동일 패턴).
- `_make_findings`: `resource_type=resource.resource_type` 전달.
- `detect_l3_031` 재작성:
  - `default_tags` 단축 + 키워드 guard는 **유지**.
  - `bundle.components`의 모든 리소스 중 `TAGGABLE_TYPES`이면서 4개 태그를 모두 갖지 못한 것을 수집.
  - 태그 존재 검사 정규식: `re.search(rf'(^|\s){re.escape(tag)}\s*=', body)` (측정으로 51개 검증됨).
  - `tag_coverage`/`unallocated_spend_ratio` 집계를 evidence 문자열에 포함.
  - 미준수 `Resource` 리스트를 `_make_findings`에 전달 (합성 리소스 제거).
- `detect_l1_009`: 정책 미적용 repo의 `image_count` 평균/최대를 evidence에 추가.
- `detect_l3_038`: 플래그된 노드의 `node_cpu_percent` 평균을 evidence에 추가.

### Step 3 — artifacts.py
- `build_solution`에 L3-038 처리 추가: 각 L3-038 finding 리소스에 대해
  `instance_type = "m5.2xlarge"` → `instance_type = "m5.large"` 치환.
  근거: 해당 노드 node_cpu_percent ~15~24% → 4x 축소 시 목표 사용률 ~60~96% 범위.
- `_pattern_problem_text`/`_pattern_cause_text`/`_pattern_solution_text`에
  L3-031/L3-038/L1-009 전용 분기 추가:
  - L3-031 problem: 미준수 개수 + `resource_type`별 분포(`Counter`).
  - L3-031 cause: 조직 태그 정책 미강제 / default_tags 부재 / CI 검증 게이트 부재.
  - L3-038 cause: pod request 과대 → 노드 플릿 과잉, node_cpu_percent 저사용률.
  - L1-009 cause: lifecycle 부재 → image_count 무한 누적.
- `build_report`에 `## 메트릭 관측` 섹션 추가 — 헬퍼 `_metrics_observations(bundle, findings)`로
  node_cpu_percent / image_count / tag_coverage 핵심 수치 요약.

### Step 4 — 테스트 (platform/tests/test_finops_agent.py)
- 신규: `test_l3_031_counts_noncompliant_resources` — MA-003 L3-031 finding 수 == 51.
- 신규: `test_solution_downgrades_eks_nodes` — MA-003 solution.tf에
  `m5.2xlarge` 부재 + `m5.large` 존재.
- 신규: `test_l1_009_evidence_includes_image_count` — L1-009 evidence에 `image_count` 언급.
- 신규: `test_l3_038_evidence_includes_cpu` — L3-038 evidence에 `node_cpu_percent` 언급.
- 기존 5개 테스트 회귀 없음 확인.

## 수용 기준 (테스트 가능)

- [ ] `pytest platform/tests/test_finops_agent.py` 전체 통과 (기존 5 + 신규 4).
- [ ] MA-003 실행 시 L3-031 finding 수 == 51, report.md "발견 이슈"에 "51개 리소스" 표기.
- [ ] MA-003 submission.md Problem Identification에 유형별 분포(`aws_instance 35개` 등) 출력.
- [ ] MA-003 solution.tf에 `instance_type = "m5.2xlarge"` 0건, `m5.large`로 치환됨.
- [ ] MA-003 report.md "핵심 근거"에 `image_count`·`node_cpu_percent` 수치 등장.
- [ ] XS-005 실행 시 `patterns_found == {"L3-025","L3-029"}` 유지 (L3-031 미발화).

## 리스크와 완화

- **R1: 기존 테스트 회귀** — `test_xs005`/`test_xs001`은 L3-031 키워드 guard로 보호됨(확인 완료).
  완화: Step 4에서 기존 테스트 먼저 실행.
- **R2: `Finding` 필드 추가 파급** — `_make_findings` 단일 생성자 확인 완료. 기본값 `""`로 안전.
- **R3: m5.large가 일부 노드(node_cpu 67%)엔 과한 축소** — detector는 m5.2xlarge만 플래그하며
  해당 서브셋 평균은 ~15~24%. m5.large 목표 사용률 합리적. 완화: 결정 사항으로 명시.
- **R4: 태그 정규식 오탐** — `(^|\s)tag\s*=` 형태는 측정으로 51개 정확 검증됨.

## 검증 단계

1. `pytest platform/tests/test_finops_agent.py -v`
2. `python run_agent.py --week 2 --mode compare` 후 MA-003 산출물 육안 확인.
3. report.md / submission.md / solution.tf를 이슈 #2와 비교.
