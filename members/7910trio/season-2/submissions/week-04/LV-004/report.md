# Single vs Multi-Agent FinOps Comparison

## Metrics

| Mode | Issues | Recall | Tokens | Wall-clock (s) | Analysis mode |
| --- | ---: | ---: | ---: | ---: | --- |
| Single agent baseline | 2 | 1.0 | 12439 | 27.4142 | llm |
| Multi-agent | 3 | 1.0 | 4151 | 40.9585 | llm |

## LLM Diagnostics

- Single agent requested: True
- Single agent client enabled: True
- Single agent error: None
- Multi-agent requested: True
- Multi-agent client enabled: True
- Multi-agent error: None

## Agent Topology

- Single agent baseline: one agent receives all domains in one context.
- Multi-agent:
  - cost_agent: cost_anomaly
  - metric_agent: compute_scaling, network_egress
  - architecture_agent: compute_scaling, network_egress, storage_tagging
  - finops_agent: cost_anomaly, network_egress, storage_tagging
  - rootcause_orchestrator: cost_analysis, metric_analysis, architecture_analysis, finops_analysis

## Delta

- Issue count delta: 1
- Recall delta: 0.0
- Token delta: -8288
- Wall-clock delta: 13.5443s

## Emergent Findings

- ri_coverage_gap
- ri_underutilization_waste
- spot_interruption_risk

## Single Agent Result

### Findings
- ri-underutilization-waste: Underutilized Reserved Instances create prepaid capacity waste
- spot-interruption-risk-concentration: Spot fleet concentrated in interruption-prone capacity pools

### Recommendations
- Sell long-remaining underutilized RIs, modify mid-utilization Convertible RIs, and let near-expiry low-value RIs expire

### Estimated Monthly Savings: $132.52

## Multi-Agent Result

### Findings
- ri_underutilization_waste: Underutilized Reserved Instances causing prepaid capacity waste
- ri_coverage_gap: Steady On‑Demand usage not covered by RIs or Savings Plans
- spot_interruption_risk: Spot fleet concentrated in interruption‑prone capacity pools

### Recommendations
- Sell long-remaining underutilized RIs, modify mid-utilization Convertible RIs, and let near-expiry low-value RIs expire

### Estimated Monthly Savings: $132.52

## Pattern Recall

- Single agent found patterns: ['LV-004']
- Multi-agent found patterns: []
- Emergent patterns: []

## Measurement Data

### Single Agent
- scenario_id: LV-004
- sell_candidate_count: 1
- modify_candidate_count: 1
- coverage_gap_count: 3
- risky_spot_window_count: 6
- recommended_pool_count: 3
- monthly_estimated_waste: 132.52
- analysis_mode: llm
- hint_pattern_ids: ['LV-004']
- hint_measurement_focus: []

### Multi-Agent
- scenario_id: LV-004
- sell_candidate_count: 1
- modify_candidate_count: 1
- coverage_gap_count: 3
- risky_spot_window_count: 6
- recommended_pool_count: 3
- monthly_estimated_waste: 132.52
- analysis_mode: llm
- hint_pattern_ids: ['LV-004']
- hint_measurement_focus: []

## Retrospective

- Single-agent baseline is simpler and cheaper, but receives all domains in one context and is more prone to missing cross-domain evidence.
- Multi-agent mode isolates domain context, then lets the root-cause orchestrator fuse evidence across network, compute, storage, and cost.
- Token and wall-clock overhead should be interpreted together with recall and emergent findings.
