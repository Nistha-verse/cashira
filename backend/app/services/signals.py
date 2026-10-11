"""Transparent, deterministic cash-flow signals for lender review."""

from __future__ import annotations

from typing import Any

from ..config import settings

SIGNAL_RULE_VERSIONS = {f"S{i}": f"cashira-s{i}-v1" for i in range(1, 8)}
SEVERITY_RANK = {"green": 0, "amber": 1, "red": 2, "none": -1}


def _signal(signal_id: str, severity: str, reason_key: str, params: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": signal_id,
        "severity": severity,
        "reason_key": reason_key,
        "params": params,
        "rule_version": SIGNAL_RULE_VERSIONS[signal_id],
    }


def render_signal_reason(signal: dict[str, Any], lang: str = "en") -> dict[str, Any]:
    from ..i18n import t

    params = signal["params"]
    rendered_params = {
        "weeks": params.get("decline_weeks", 0),
        "drop": round(float(params.get("cumulative_drop", 0)) * 100, 1),
        "ratio": round(float(params.get("ratio", 0)) * 100, 1),
        "coverage": round(float(params.get("coverage", 0)), 2),
        "days": params.get("days_since_last_transaction", 0),
        "cv": round(float(params.get("coefficient_of_variation", 0)) * 100, 1),
    }
    return {**signal, "text": t(signal["reason_key"], lang, **rendered_params)}


def signal_s1(weekly: dict[str, Any], thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thresholds = thresholds or settings.signal_thresholds
    decline_count = int(weekly.get("consecutive_weekly_declines") or 0)
    weeks = weekly.get("weeks", [])
    run_size = decline_count + 1
    first = weeks[-run_size]["sales"] if decline_count and len(weeks) >= run_size else 0
    latest = weeks[-1]["sales"] if weeks else 0
    cumulative_drop = (first - latest) / first if first else 0.0
    if decline_count >= thresholds["decline_red_weeks"] or cumulative_drop >= thresholds["decline_red_drop"]:
        severity = "red"
    elif decline_count >= thresholds["decline_amber_weeks"] and cumulative_drop >= thresholds["decline_amber_drop"]:
        severity = "amber"
    else:
        severity = "none"
    return _signal("S1", severity, "signals.s1", {"decline_weeks": decline_count, "cumulative_drop": round(cumulative_drop, 4)})


def signal_s2(weekly: dict[str, Any], thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thresholds = thresholds or settings.signal_thresholds
    recent = float(weekly.get("last_2_week_average_sales") or 0)
    baseline = float((weekly.get("trailing_8_week_baseline") or {}).get("sales") or 0)
    ratio = recent / baseline if baseline else 1.0
    severity = "red" if ratio < thresholds["sales_ratio_red"] else "amber" if ratio < thresholds["sales_ratio_amber"] else "none"
    return _signal("S2", severity, "signals.s2", {"recent_sales": round(recent, 2), "baseline_sales": round(baseline, 2), "ratio": round(ratio, 4)})


def signal_s3(weekly: dict[str, Any], loan: dict[str, Any] | None, thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thresholds = thresholds or settings.signal_thresholds
    standard_emi = float((loan or {}).get("standard_emi") or 0)
    monthly_net = float(weekly.get("four_week_net_monthly_equivalent") or 0)
    coverage = monthly_net / standard_emi if standard_emi else 0.0
    severity = "red" if coverage < thresholds["emi_coverage_red"] else "amber" if coverage < thresholds["emi_coverage_amber"] else "none"
    return _signal("S3", severity, "signals.s3", {"monthly_net": round(monthly_net, 2), "standard_emi": round(standard_emi, 2), "coverage": round(coverage, 4)})


def signal_s4(weekly: dict[str, Any], thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thresholds = thresholds or settings.signal_thresholds
    days = weekly.get("days_since_last_transaction")
    days = int(days) if days is not None else thresholds["gap_red_days"]
    severity = "red" if days >= thresholds["gap_red_days"] else "amber" if days >= thresholds["gap_amber_days"] else "none"
    return _signal("S4", severity, "signals.s4", {"days_since_last_transaction": days, "data_may_be_incomplete": severity != "none"})


def signal_s5(weekly: dict[str, Any], thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thresholds = thresholds or settings.signal_thresholds
    baseline = weekly.get("trailing_8_week_baseline") or {}
    baseline_outflow = float(baseline.get("outflow") or 0) * 2
    recent_outflow = float(weekly.get("last_2_week_outflow") or 0)
    baseline_inflow = float(baseline.get("inflow") or 0) * 2
    recent_inflow = float(weekly.get("last_2_week_inflow") or 0)
    outflow_ratio = recent_outflow / baseline_outflow if baseline_outflow else 1.0
    inflow_ratio = recent_inflow / baseline_inflow if baseline_inflow else 1.0
    severity = "amber" if outflow_ratio > thresholds["outflow_spike_ratio"] and inflow_ratio <= 1.0 else "none"
    return _signal("S5", severity, "signals.s5", {"recent_outflow": round(recent_outflow, 2), "baseline_outflow": round(baseline_outflow, 2), "outflow_ratio": round(outflow_ratio, 4), "inflow_ratio": round(inflow_ratio, 4)})


def signal_s6(repayment: dict[str, Any] | None) -> dict[str, Any]:
    repayment = repayment or {}
    overdue = bool(repayment.get("overdue"))
    late_recent = bool(repayment.get("late_recent"))
    severity = "red" if overdue else "amber" if late_recent else "none"
    return _signal("S6", severity, "signals.s6", {"late_recent": late_recent, "overdue": overdue})


def signal_s7(coefficient_of_variation: float = 0.0, thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    thresholds = thresholds or settings.signal_thresholds
    severity = "amber" if coefficient_of_variation > thresholds["volatility_cv_amber"] else "none"
    return _signal("S7", severity, "signals.s7", {"coefficient_of_variation": round(coefficient_of_variation, 4)})


def evaluate_signals(
    weekly: dict[str, Any],
    loan: dict[str, Any] | None,
    repayment: dict[str, Any] | None,
    coefficient_of_variation: float = 0.0,
    thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    signals = [
        signal_s1(weekly, thresholds),
        signal_s2(weekly, thresholds),
        signal_s3(weekly, loan, thresholds),
        signal_s4(weekly, thresholds),
        signal_s5(weekly, thresholds),
        signal_s6(repayment),
        signal_s7(coefficient_of_variation, thresholds),
    ]
    active = [item for item in signals if item["severity"] != "none"]
    status = max((item["severity"] for item in active), key=lambda severity: SEVERITY_RANK[severity], default="green")
    first = sorted(active, key=lambda item: (-SEVERITY_RANK[item["severity"]], item["id"]))
    return {"status": status, "signals": signals, "what_to_look_at_first": [item["id"] for item in first]}
