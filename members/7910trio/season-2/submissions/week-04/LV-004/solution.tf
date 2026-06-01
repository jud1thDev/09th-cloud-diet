"""
LV-004 solution: RI utilization, RI coverage, and Spot interruption optimizer.

This file is intentionally standalone for submission. It reads the mock API
payloads under inputs/week04/mock_api and produces actionable recommendations.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_RECOMMENDATIONS = ['Sell long-remaining underutilized RIs, modify mid-utilization Convertible RIs, and let near-expiry low-value RIs expire']
ESTIMATED_MONTHLY_SAVINGS_USD = 132.52
GENERATED_MEASUREMENT_SUMMARY = {'scenario_id': 'LV-004', 'sell_candidate_count': 1, 'modify_candidate_count': 1, 'coverage_gap_count': 3, 'risky_spot_window_count': 6, 'recommended_pool_count': 3, 'monthly_estimated_waste': 132.52, 'analysis_mode': 'llm', 'hint_pattern_ids': ['LV-004'], 'hint_measurement_focus': []}
SOURCE_AGENT_MODE = "multi_agent_final"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def analyze_ri_utilization(payload: dict[str, Any]) -> list[dict[str, Any]]:
    thresholds = payload.get("analysis_thresholds", {})
    sell_below = float(thresholds.get("sell_candidate_below_percent", 50))
    modify_below = float(thresholds.get("modify_candidate_below_percent", 70))
    short_term_months = float(thresholds.get("short_remaining_term_months", 3))
    findings = []

    for reservation in payload.get("reservations", []):
        utilization = float(reservation.get("utilization_percent") or 0)
        remaining = float(reservation.get("remaining_term_months") or 0)
        if utilization < sell_below and remaining > short_term_months:
            action = "sell"
            reason = "utilization below 50% and enough remaining term to recover value"
        elif utilization < sell_below:
            action = "let_expire"
            reason = "utilization is low, but remaining term is too short for Marketplace action"
        elif utilization < modify_below:
            action = "modify"
            reason = "utilization is between 50% and 70%; downsize or exchange Convertible RI"
        else:
            action = "keep"
            reason = "utilization is healthy"

        findings.append(
            {
                "reservation_id": reservation.get("reservation_id"),
                "instance_type": reservation.get("instance_type"),
                "utilization_percent": utilization,
                "remaining_term_months": remaining,
                "action": action,
                "reason": reason,
                "estimated_monthly_waste": float(reservation.get("estimated_monthly_waste") or 0),
                "estimated_recovery": float(reservation.get("estimated_market_recovery") or 0),
            }
        )
    return findings


def analyze_ri_coverage(payload: dict[str, Any]) -> list[dict[str, Any]]:
    thresholds = payload.get("analysis_thresholds", {})
    low_coverage = float(thresholds.get("low_coverage_below_percent", 50))
    high_on_demand_hours = float(thresholds.get("high_on_demand_hours", 0))
    findings = []

    for row in payload.get("coverage_by_instance_type", []):
        coverage = float(row.get("coverage_percent") or 0)
        on_demand_hours = float(row.get("on_demand_hours") or 0)
        variability = str(row.get("workload_variability", "unknown")).lower()
        has_gap = coverage < low_coverage and on_demand_hours >= high_on_demand_hours
        if not has_gap:
            action = "no_new_ri"
            reason = "coverage or On-Demand usage does not justify additional commitment"
        elif variability == "low":
            action = "buy_standard_ri"
            reason = "stable high-hour usage is a good Standard RI candidate"
        else:
            action = "buy_convertible_ri_or_savings_plan"
            reason = "usage is high but variable, so flexibility is safer than Standard RI"

        findings.append(
            {
                "instance_type": row.get("instance_type"),
                "coverage_percent": coverage,
                "on_demand_hours": on_demand_hours,
                "workload_variability": variability,
                "coverage_gap": has_gap,
                "action": action,
                "reason": reason,
                "estimated_monthly_savings": float(row.get("estimated_monthly_savings") or 0) if has_gap else 0.0,
            }
        )
    return findings


def learn_spot_interruption_patterns(payload: dict[str, Any]) -> dict[str, Any]:
    on_demand_prices = payload.get("on_demand_reference_prices", {})
    threshold = float(payload.get("interruption_signal_rule", {}).get("price_to_on_demand_ratio_threshold", 0.9))
    frequency: Counter[tuple[int, str, str]] = Counter()
    pool_stats: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"samples": 0, "spikes": 0, "max_ratio": 0.0})

    for row in payload.get("price_history", []):
        instance_type = str(row.get("instance_type"))
        az = str(row.get("availability_zone"))
        hour = int(row.get("hour_of_day") or 0)
        spot_price = float(row.get("spot_price") or 0)
        on_demand = float(on_demand_prices.get(instance_type) or 0)
        ratio = spot_price / on_demand if on_demand else 0.0
        is_spike = ratio >= threshold

        if is_spike:
            frequency[(hour, instance_type, az)] += 1
        stats = pool_stats[(instance_type, az)]
        stats["samples"] += 1
        stats["spikes"] += int(is_spike)
        stats["max_ratio"] = max(stats["max_ratio"], ratio)

    risky_windows = [
        {
            "hour_of_day": hour,
            "instance_type": instance_type,
            "availability_zone": az,
            "interruption_count": count,
        }
        for (hour, instance_type, az), count in frequency.most_common()
    ]
    capacity_pools = [
        {
            "instance_type": instance_type,
            "availability_zone": az,
            "samples": stats["samples"],
            "spikes": stats["spikes"],
            "risk_score": round(stats["spikes"] / stats["samples"], 4) if stats["samples"] else 0.0,
            "max_price_to_on_demand_ratio": round(stats["max_ratio"], 4),
        }
        for (instance_type, az), stats in pool_stats.items()
    ]
    return {
        "risky_windows": risky_windows,
        "capacity_pools": sorted(capacity_pools, key=lambda item: (item["risk_score"], item["max_price_to_on_demand_ratio"])),
    }


def recommend_fleet_diversification(spot_analysis: dict[str, Any], current_mix: list[dict[str, Any]]) -> dict[str, Any]:
    pools = spot_analysis.get("capacity_pools", [])
    safe_pools = [pool for pool in pools if float(pool.get("risk_score") or 0) == 0.0]
    fallback_pools = [pool for pool in pools if float(pool.get("risk_score") or 0) < 0.5]
    selected = (safe_pools or fallback_pools or pools)[:3]
    weight = round(1 / len(selected), 2) if selected else 0
    return {
        "current_mix": current_mix,
        "recommended_mix": [
            {
                "instance_type": pool.get("instance_type"),
                "availability_zone": pool.get("availability_zone"),
                "weight": weight,
                "risk_score": pool.get("risk_score"),
            }
            for pool in selected
        ],
        "allocation_strategy": "capacity-optimized",
        "reason": "shift weight away from pools with repeated price spikes near On-Demand price",
    }


def build_actionable_recommendations(
    ri_utilization: list[dict[str, Any]],
    ri_coverage: list[dict[str, Any]],
    fleet_strategy: dict[str, Any],
) -> list[dict[str, Any]]:
    recommendations = []
    for item in ri_utilization:
        if item["action"] in {"sell", "modify", "let_expire"}:
            recommendations.append(
                {
                    "category": "ri_utilization",
                    "target": item["reservation_id"],
                    "action": item["action"],
                    "reason": item["reason"],
                    "estimated_monthly_savings": item["estimated_monthly_waste"],
                    "estimated_recovery": item["estimated_recovery"],
                }
            )
    for item in ri_coverage:
        if item["coverage_gap"]:
            recommendations.append(
                {
                    "category": "ri_coverage",
                    "target": item["instance_type"],
                    "action": item["action"],
                    "reason": item["reason"],
                    "estimated_monthly_savings": item["estimated_monthly_savings"],
                }
            )
    if fleet_strategy.get("recommended_mix"):
        recommendations.append(
            {
                "category": "spot_fleet",
                "target": "spot_fleet_mix",
                "action": "diversify",
                "reason": fleet_strategy["reason"],
                "allocation_strategy": fleet_strategy["allocation_strategy"],
                "recommended_mix": fleet_strategy["recommended_mix"],
            }
        )
    return recommendations


def run(input_dir: str | Path) -> dict[str, Any]:
    base = Path(input_dir)
    mock_api = base / "mock_api"
    utilization = load_json(mock_api / "reservation_utilization.json")
    coverage = load_json(mock_api / "reservation_coverage.json")
    spot = load_json(mock_api / "spot_price_history.json")

    ri_utilization = analyze_ri_utilization(utilization)
    ri_coverage = analyze_ri_coverage(coverage)
    spot_analysis = learn_spot_interruption_patterns(spot)
    fleet = recommend_fleet_diversification(spot_analysis, spot.get("current_spot_fleet_mix", []))

    utilization_savings = sum(item["estimated_monthly_waste"] for item in ri_utilization if item["action"] in {"sell", "modify", "let_expire"})
    coverage_savings = sum(item["estimated_monthly_savings"] for item in ri_coverage if item["coverage_gap"])
    recommendations = build_actionable_recommendations(ri_utilization, ri_coverage, fleet)
    return {
        "scenario_id": "LV-004",
        "ri_utilization_findings": ri_utilization,
        "ri_coverage_findings": ri_coverage,
        "spot_interruption_patterns": spot_analysis,
        "fleet_diversification_strategy": fleet,
        "estimated_monthly_savings_usd": round(utilization_savings + coverage_savings, 2),
        "recommendations": recommendations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="LV-004 RI and Spot optimization agent")
    parser.add_argument("--input-dir", default="inputs/week04")
    parser.add_argument("--output", help="Optional path to write JSON result")
    args = parser.parse_args()
    result = run(args.input_dir)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()