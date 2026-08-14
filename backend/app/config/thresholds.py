"""Configurable thresholds and scoring weights for grid stress analysis.

All stress detection limits and the stress-score formula live here so that no
magic numbers are hardcoded across the analysis modules. Every value is
documented in docs/architecture/STRESS_ANALYSIS.md.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StressThresholds:
    # --- Voltage (per unit) ---
    # NORMAL:  normal_low <= V <= normal_high
    # WARNING: warning_low <= V < normal_low  OR  normal_high < V <= warning_high
    # CRITICAL: V < critical_low  OR  V > critical_high
    voltage_normal_low: float = 0.95
    voltage_normal_high: float = 1.05
    voltage_warning_low: float = 0.93
    voltage_warning_high: float = 1.07
    voltage_critical_low: float = 0.93
    voltage_critical_high: float = 1.07

    # --- Transmission lines (percent of thermal limit) ---
    # NORMAL:   loading < line_warning_threshold
    # WARNING:  line_warning_threshold <= loading <= line_overload_threshold
    # CRITICAL: loading > line_overload_threshold
    line_warning_threshold: float = 80.0
    line_overload_threshold: float = 100.0

    # --- Generation balance (MW) ---
    # Tolerance used when deciding whether a generator sits at its configured
    # minimum or maximum active-power limit.
    generator_limit_epsilon_mw: float = 1.0
    # A slack generator absorbing power (negative output) indicates excess
    # generation; below this (negative) value we flag EXCESS_GENERATION.
    excess_generation_threshold_mw: float = -1.0
    # Slack output at or above this fraction of its max marks the system as
    # GENERATION_INSUFFICIENT / IMBALANCED_SYSTEM.
    insufficient_slack_fraction: float = 0.98
    # Slack generation share above this fraction of total generation marks the
    # system as IMBALANCED_SYSTEM (over-reliance on the balancing bus).
    slack_reliance_threshold: float = 0.70

    # --- Renewable impact (percent) ---
    # Penetration levels used when no baseline analysis is available.
    renewable_low_penetration: float = 30.0
    renewable_high_penetration: float = 60.0

    # --- Stress score (0 = minimal stress, 100 = severe stress) ---
    # Component weights must sum to 1.0.
    score_weights: dict[str, float] = field(
        default_factory=lambda: {
            "voltage": 0.40,
            "transmission": 0.35,
            "generation": 0.15,
            "renewable": 0.10,
        }
    )
    # Classification bands for the overall score.
    low_score_max: float = 25.0
    moderate_score_max: float = 50.0
    high_score_max: float = 75.0

    # --- Component severity point mapping (drives component scores) ---
    severity_warning_points: float = 30.0
    severity_critical_points: float = 100.0
    # Extra points per additional affected component, capped.
    voltage_extra_per_bus: float = 10.0
    voltage_extra_cap: float = 30.0
    line_extra_per_line: float = 5.0
    line_extra_cap: float = 25.0


stress_thresholds = StressThresholds()
