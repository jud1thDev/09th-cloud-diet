# Week 5 — AI 워크로드(L4) 학습 자료

> 이번 주차 목표: 시즌 1에 없던 **AI/ML 워크로드 비용 구조**(LLM 추론·Bedrock·SageMaker·GPU)를 학습하고, 본인 도구에 **L4 시나리오 5~7개**를 추가.
> 일반 인프라와 완전히 다른 함정(약정 과잉, endpoint autoscaling 미설정, GPU 야간 미정지, 토큰 과금, 캐시 부재)이 핵심.

---

## 🎯 이번 주차에서 가져가야 할 것

1. **Bedrock 과금 모델** — On-Demand(토큰당) vs Provisioned Throughput(MU 시간당 약정)의 break-even
2. **SageMaker Endpoint Auto Scaling** — target tracking / scheduled scaling 미설정 시 GPU 인스턴스 상시 과금
3. **GPU 인스턴스 스케줄링** — 야간·주말 미정지로 인한 낭비, Instance Scheduler로 자동 정지
4. **LLM TCO** — API 토큰 과금 vs 자체 호스팅(GPU/Inferentia) TCO 비교 방법론
5. **캐시 부재** — prompt caching / semantic(embedding) cache로 반복 컨텍스트 비용 절감

---

## 🔴 필수 (이번 주차 토론 베이스)

### 1. [Effective cost optimization strategies for Amazon Bedrock — AWS ML Blog](https://aws.amazon.com/blogs/machine-learning/effective-cost-optimization-strategies-for-amazon-bedrock/)
**AWS / 읽기 30분**
On-Demand vs Provisioned Throughput 선택 기준, 모델 선택·프롬프트 최적화·캐싱까지 Bedrock 비용 최적화의 전체 지도. L4-001(PT 과잉) 직결.

### 2. [Increase model invocation capacity with Provisioned Throughput — Amazon Bedrock Docs](https://docs.aws.amazon.com/bedrock/latest/userguide/prov-throughput.html)
**AWS 공식 / 읽기 20분**
Model Unit(MU) = 분당 토큰 처리량 단위. 시간당 과금 + 1개월/6개월 약정 구조. "약정이라 고정비로 인식 → 활용률 안 봄"이 L4-001 함정의 본질. ([구매 절차](https://docs.aws.amazon.com/bedrock/latest/userguide/prov-thru-purchase.html))

### 3. [Optimize your ML deployments with auto scaling on Amazon SageMaker — AWS ML Blog](https://aws.amazon.com/blogs/machine-learning/optimize-your-machine-learning-deployments-with-auto-scaling-on-amazon-sagemaker/)
**AWS / 읽기 30분**
target tracking / step / scheduled scaling으로 inference endpoint를 수요에 맞게 조정. 미설정 시 GPU 인스턴스가 트래픽 0에도 상시 과금되는 함정. ([Inference cost optimization best practices](https://docs.aws.amazon.com/sagemaker/latest/dg/inference-cost-optimization.html))

---

## 🟡 권장 (자기 도구 적용 시 참고)

### Bedrock 단가 / 캐싱 (L4-001 · 임베딩 캐시)

| 자료 | 한 줄 설명 |
|------|-----------|
| [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) · [On-Demand Tiers](https://aws.amazon.com/bedrock/service-tiers/) | 모델별 input/output 토큰 단가 + PT 시간 단가. TCO 계산의 입력 |
| [Prompt caching for faster model inference — Bedrock Docs](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html) | 반복 컨텍스트 캐싱으로 비용 최대 90%·지연 최대 85% 절감 |
| [Lower cost and latency using ElastiCache as a semantic cache — AWS DB Blog](https://aws.amazon.com/blogs/database/lower-cost-and-latency-for-ai-using-amazon-elasticache-as-a-semantic-cache-with-amazon-bedrock/) | 임베딩 기반 유사 질의 응답 재사용(semantic cache) — 추론 비용 최대 86% 절감 |

### SageMaker / GPU 스케줄링 (Endpoint autoscaling · GPU 야간 미정지)

| 자료 | 한 줄 설명 |
|------|-----------|
| [Configuring autoscaling inference endpoints — AWS ML Blog](https://aws.amazon.com/blogs/machine-learning/configuring-autoscaling-inference-endpoints-in-amazon-sagemaker/) | endpoint autoscaling 정책 구성 실전 |
| [Right-sizing and auto-scaling an inference system — AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/gen-ai-inference-architecture-and-best-practices-on-aws/right-sizing-and-auto-scaling.html) | GPU inference 시스템 right-sizing 베스트 프랙티스 |
| [Instance Scheduler on AWS — Solutions](https://aws.amazon.com/solutions/implementations/instance-scheduler-on-aws/) | tag + Lambda로 EC2/RDS 자동 start/stop. 업무시간만 운영 시 최대 70% 절감 |
| [Stop and start EC2 on a schedule using Quick Setup — SSM Docs](https://docs.aws.amazon.com/systems-manager/latest/userguide/quick-setup-scheduler.html) | GPU 인스턴스 야간·주말 자동 정지의 가장 간단한 진입점 |

---

## 🟩 한국어 사례 (실전 — 자체 호스팅 TCO)

### 1. [네오사피엔스의 AWS g6e 기반 LLM 추론 배치 워크로드 최적화 사례 — AWS 기술 블로그](https://aws.amazon.com/ko/blogs/tech/neosapience-llm-inference-optimization-aws-g6e/)
**AWS 한국 기술 블로그 / 읽기 35분**
g6e(L40S) + INT8 양자화 조합이 단일 GPU 성능·체감 레이턴시·운영 안정성 관점에서 최적이었던 실측 사례. 인스턴스–정밀도 조합 선택 방법론.

### 2. [Task-specialized LLM 비용 효율 서빙: Inferentia2 + Hugging Face Optimum — AWS 기술 블로그](https://aws.amazon.com/ko/blogs/tech/task-specialized-llm-serving-aws-inferentia2-huggingface-optimum/)
**AWS 한국 기술 블로그 / 읽기 30분**
GPU 대신 Inferentia2로 비용 효율 추론. 대규모 배치에서 경쟁력 있는 self-host 대안.

### 3. [HyperAccel, EC2 F2(LPU) 기반 고효율 LLM 추론 — AWS 기술 블로그](https://aws.amazon.com/ko/blogs/tech/hyperaccel-fpga-on-aws/)
**AWS 한국 기술 블로그 / 읽기 25분**
H100(p5.4xlarge) ~$6.88/h vs F2(f2.6xlarge) ~$1.98/h — **하드웨어 선택이 LLM 추론 TCO를 어떻게 바꾸는지** 정량 비교. L4 TCO 시나리오 설계에 직접 활용.

### 4. [vLLM과 TensorRT-LLM을 활용한 LLM 추론 최적화 1편 — velog](https://velog.io/@noimnotfree/vLLM%EA%B3%BC-TensorRT-LLM%EC%9D%84-%ED%99%9C%EC%9A%A9%ED%95%9C-LLM-%EC%B6%94%EB%A1%A0-%EC%B5%9C%EC%A0%81%ED%99%94-1%ED%8E%B8-%EC%84%A4%EC%B9%98-%EB%B0%A9%EB%B2%95)
**개인 블로그 / 읽기 20분**
양자화 + KV Cache로 모델 크기·추론 속도 최적화. self-host 처리량(throughput) 단가를 낮추는 실전 기법.

---

## 🟢 심화 (시간 남으면)

### 1. [Optimizing costs of generative AI applications on AWS — AWS ML Blog](https://aws.amazon.com/blogs/machine-learning/optimizing-costs-of-generative-ai-applications-on-aws/)
**AWS / 읽기 35분**
GenAI 애플리케이션 전체(모델·추론·RAG·벡터DB)의 비용 구조와 최적화 레버.

### 2. [Effectively use prompt caching on Amazon Bedrock — AWS ML Blog](https://aws.amazon.com/blogs/machine-learning/effectively-use-prompt-caching-on-amazon-bedrock/)
**AWS / 읽기 25분**
prompt caching을 실제로 적용해 cache hit rate를 높이는 패턴과 측정.

### 3. [Amazon SageMaker faster auto scaling for generative AI models — AWS ML Blog](https://aws.amazon.com/blogs/machine-learning/amazon-sagemaker-inference-launches-faster-auto-scaling-for-generative-ai-models/)
**AWS / 읽기 20분**
최대 6배 빠른 scale-up 감지. GPU endpoint의 over-provisioning을 줄이는 최신 기능.

---

## 📋 토론 토픽 (월요일 22:00 세션용)

읽어 오고 본인 도구에 L4 시나리오로 녹일 수 있게 준비:

1. **PT break-even** — On-Demand(토큰당)와 Provisioned Throughput(MU 시간당) 비용이 교차하는 트래픽 지점은? 활용률 몇 %부터 PT가 손해?
2. **Endpoint 활용률 탐지** — SageMaker endpoint의 `InvocationsPerInstance`·GPU utilization을 어떻게 받아 over-provisioning을 판정?
3. **GPU 야간 미정지** — dev/실험용 GPU 인스턴스의 가동 시간 패턴을 어떤 메트릭으로 보고 스케줄 정지를 권장?
4. **API vs self-host TCO** — 특정 트래픽에서 Bedrock 토큰 과금과 자체 GPU 호스팅(인스턴스+운영) 중 어디가 싼지 계산식은?
5. **캐시 부재 탐지** — 반복 프롬프트/임베딩 재계산을 어떤 신호로 감지하고 prompt/semantic cache를 권장?

---

## 🎯 산출물 (다음 주까지)

- [ ] **L4 시나리오 5~7개 추가** — 본인 도구의 패턴 카탈로그에 AI 워크로드 시나리오 정의(상황 / 청구서 모양 / 탐지 신호 / 권장 / 절감 수식)
- [ ] **L4 탐지 로직** — Bedrock/SageMaker/GPU 관련 메트릭·구성에서 낭비를 식별하는 detector
- [ ] **Report** — L4 도메인 비용 구조 정리 + 본인 도구 적용 결과 + 회고
- [ ] (옵션) PT break-even / self-host TCO 계산기 모듈

---

## 📎 참고

- 시나리오 카탈로그 Week 5 (요약): [docs/SCENARIOS_S2.md](SCENARIOS_S2.md)
- 시나리오 카탈로그 Week 5 (상세본): [docs/SCENARIOS_S2_DETAILED.md](SCENARIOS_S2_DETAILED.md)
- 본주 본인 시나리오: Problems → 시즌 2 → Week 5
