"""Deterministic, feature-based explanations for prioritized readings."""

import pandas as pd


def _explain_row(row: pd.Series) -> str:
    reasons: list[str] = []
    if row["flow_deviation_pct"] >= 35:
        reasons.append("Flow is substantially above the zone's historical baseline")
    elif row["flow_deviation_pct"] <= -35:
        reasons.append("Flow is substantially below the zone's historical baseline")
    if row["pressure_deviation_pct"] <= -15:
        reasons.append("Pressure is below the zone's expected range")
    if row["unaccounted_water_pct"] >= 30:
        reasons.append("Supplied flow volume significantly exceeds recorded consumption")
    if row["consumption_deviation_pct"] >= 35:
        reasons.append("Consumption is substantially above the zone's historical baseline")
    if row["persistence_count_8"] >= 4:
        reasons.append("The abnormal pattern has persisted across multiple recent readings")

    if not reasons:
        return "No strong abnormal pattern is evident from the current prototype signals."
    conclusion = "; ".join(reasons) + "."
    if row["risk_category"] == "HIGH RISK":
        conclusion += " This anomalous behaviour is recommended for human inspection."
    elif row["risk_category"] == "MONITOR":
        conclusion += " Continued monitoring is recommended for this probable abnormality."
    else:
        conclusion += " This may indicate unusual operation or potential water loss, but it is not a confirmed leak."
    return conclusion


def add_explanations(data: pd.DataFrame) -> pd.DataFrame:
    """Add one reproducible plain-language explanation to every reading."""
    result = data.copy()
    result["explanation"] = result.apply(_explain_row, axis=1)
    return result
