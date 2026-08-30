"""Deterministic, feature-based explanations for prioritized readings."""

import pandas as pd


def _explain_row(row: pd.Series) -> str:
    reasons: list[str] = []
    if row["flow_deviation_pct"] >= 35:
        reasons.append("Inlet flow is substantially above the DMA's historical baseline")
    elif row["flow_deviation_pct"] <= -35:
        reasons.append("Inlet flow is substantially below the DMA's historical baseline")
    if row["pressure_deviation_pct"] <= -15:
        reasons.append("Median site pressure is below the DMA's expected range")
    if row["unaccounted_water_pct"] >= 30:
        reasons.append("Inlet volume significantly exceeds outlet volume plus metered consumption")
    if row["consumption_deviation_pct"] >= 35:
        reasons.append("Metered consumption is substantially above the DMA's historical baseline")
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
