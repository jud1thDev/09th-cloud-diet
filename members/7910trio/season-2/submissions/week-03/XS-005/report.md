# Single vs Multi-Agent FinOps Comparison

## Metrics

| Mode | Issues | Recall | Tokens | Wall-clock (s) | Analysis mode |
| --- | ---: | ---: | ---: | ---: | --- |
| Single agent baseline | 1 | 0.5 | 6879 | 44.2173 | llm |
| Multi-agent | 1 | 0.5 | 24844 | 44.5372 | llm |

## Agent Topology

- Single agent baseline: one agent receives all domains in one context.
- Multi-agent:
  - cost_agent: cost_anomaly
  - metric_agent: compute_scaling, network_egress
  - architecture_agent: compute_scaling, network_egress, storage_tagging
  - finops_agent: cost_anomaly, network_egress, storage_tagging
  - rootcause_orchestrator: cost_analysis, metric_analysis, architecture_analysis, finops_analysis

## Delta

- Issue count delta: 0
- Recall delta: 0.0
- Token delta: 17965
- Wall-clock delta: 0.3199s

## Emergent Findings

- RC1-nat-s3-endpoint-misalignment

## Measurement Data

### Single Agent
- nat_cost: 1150.03
- nat_waste: 191.67166666666665
- monthly_estimated_waste: 191.67166666666665
- nat_cost_spike: True
- uses_nat_gateway: True
- has_s3_endpoint: False
- scaling_oscillation: False
- analysis_mode: llm
- hint_pattern_ids: ['L3-025', 'L3-029', 'XS-005']
- hint_measurement_focus: ['Recall', '토큰', 'Wall-clock', '비용', 'token', 'cost']

### Multi-Agent
- nat_cost: 1150.03
- nat_waste: 191.67166666666665
- monthly_estimated_waste: 191.67166666666665
- nat_cost_spike: True
- uses_nat_gateway: True
- has_s3_endpoint: False
- scaling_oscillation: False
- analysis_mode: llm
- hint_pattern_ids: ['L3-025', 'L3-029', 'XS-005']
- hint_measurement_focus: ['Recall', '토큰', 'Wall-clock', '비용', 'token', 'cost']

## Retrospective

- Single-agent baseline is simpler and cheaper, but receives all domains in one context and is more prone to missing cross-domain evidence.
- Multi-agent mode isolates domain context, then lets the root-cause orchestrator fuse evidence across network, compute, storage, and cost.
- Token and wall-clock overhead should be interpreted together with recall and emergent findings.
