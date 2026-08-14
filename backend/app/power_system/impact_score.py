from pydantic import BaseModel

from app.core.config import Settings


class ImpactCategory(BaseModel):
    score: float
    detail: str


class GridImpactScore(BaseModel):
    score: float
    grade: str
    categories: dict[str, ImpactCategory]
    message: str


def _voltage_score(minimum_pu: float, maximum_pu: float) -> tuple[float, str]:
    penalty = 0.0
    for voltage in (minimum_pu, maximum_pu):
        deviation = abs(voltage - 1.0)
        if deviation > 0.05:
            penalty += min((deviation - 0.05) / 0.05 * 25.0, 25.0)
    score = max(0.0, 100.0 - penalty)
    detail = (
        f"Voltages within {minimum_pu:.3f}..{maximum_pu:.3f} pu "
        "(target band 0.95..1.05 pu)."
    )
    return round(score, 1), detail


def _loading_score(
    maximum_loading: float,
    overloaded_lines: int,
    settings: Settings,
) -> tuple[float, str]:
    if overloaded_lines > 0:
        penalty = min(25.0 + 10.0 * (overloaded_lines - 1), 100.0)
    elif maximum_loading > settings.line_warning_threshold:
        penalty = min((maximum_loading - settings.line_warning_threshold) / 20.0 * 15.0, 25.0)
    else:
        penalty = 0.0
    score = max(0.0, 100.0 - penalty)
    detail = f"Maximum line loading {maximum_loading:.1f}%; {overloaded_lines} overloaded line(s)."
    return round(score, 1), detail


def _losses_score(total_losses_mw: float, total_load_mw: float) -> tuple[float, str]:
    if total_load_mw <= 0:
        return 100.0, "No load; losses not penalized."
    ratio = total_losses_mw / total_load_mw
    penalty = min(ratio / 0.10 * 30.0, 30.0)
    score = max(0.0, 100.0 - penalty)
    return round(score, 1), f"Loss ratio {ratio * 100:.1f}% of total load (penalized above 10%)."


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def compute_impact_score(
    *,
    minimum_voltage_pu: float,
    maximum_voltage_pu: float,
    maximum_line_loading: float,
    overloaded_lines: int,
    total_losses_mw: float,
    total_load_mw: float,
    settings: Settings,
) -> GridImpactScore:
    voltage_score, voltage_detail = _voltage_score(minimum_voltage_pu, maximum_voltage_pu)
    loading_score, loading_detail = _loading_score(
        maximum_line_loading, overloaded_lines, settings
    )
    losses_score, losses_detail = _losses_score(total_losses_mw, total_load_mw)

    score = round(0.4 * voltage_score + 0.4 * loading_score + 0.2 * losses_score, 1)

    messages = []
    if minimum_voltage_pu < settings.voltage_warning_low or maximum_voltage_pu > settings.voltage_warning_high:
        messages.append("Voltage deviation from the operating band.")
    if overloaded_lines > 0:
        messages.append(f"{overloaded_lines} overloaded line(s).")
    if losses_score < 100:
        messages.append("Transmission losses above target.")
    message = " ".join(messages) if messages else "Grid is healthy; no violations detected."

    return GridImpactScore(
        score=score,
        grade=_grade(score),
        categories={
            "voltage": ImpactCategory(score=voltage_score, detail=voltage_detail),
            "loading": ImpactCategory(score=loading_score, detail=loading_detail),
            "losses": ImpactCategory(score=losses_score, detail=losses_detail),
        },
        message=message,
    )
