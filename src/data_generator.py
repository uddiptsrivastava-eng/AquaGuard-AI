"""Generate the synthetic AquaGuard AI water-network dataset.

This script creates illustrative data for a hackathon prototype. The values are
not measurements from a real water utility and must not be treated as such.
"""

from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_SEED = 42
NUMBER_OF_ZONES = 20
NUMBER_OF_DAYS = 30
READING_FREQUENCY = "15min"
START_TIME = "2026-01-01 00:00:00"

# Each entry is one deliberately injected anomalous period. Keeping this list in
# one place makes the synthetic "ground truth" easy to inspect and change.
ANOMALY_PERIODS = [
    {
        "zone_id": "Z03",
        "start": "2026-01-05 02:00:00",
        "end": "2026-01-05 08:00:00",
        "type": "high_flow",
    },
    {
        "zone_id": "Z07",
        "start": "2026-01-10 14:00:00",
        "end": "2026-01-10 20:00:00",
        "type": "low_pressure",
    },
    {
        "zone_id": "Z11",
        "start": "2026-01-15 00:00:00",
        "end": "2026-01-16 00:00:00",
        "type": "flow_consumption_divergence",
    },
    {
        "zone_id": "Z14",
        "start": "2026-01-20 06:00:00",
        "end": "2026-01-20 12:00:00",
        "type": "high_consumption_low_flow",
    },
    {
        "zone_id": "Z18",
        "start": "2026-01-24 18:00:00",
        "end": "2026-01-25 06:00:00",
        "type": "combined_flow_pressure",
    },
    {
        "zone_id": "Z05",
        "start": "2026-01-28 09:00:00",
        "end": "2026-01-28 10:00:00",
        "type": "flow_spike",
    },
]


def _daily_demand_multiplier(hours: np.ndarray) -> np.ndarray:
    """Return a smooth household-demand pattern with morning/evening peaks."""
    morning_peak = 0.75 * np.exp(-0.5 * ((hours - 7.5) / 1.7) ** 2)
    evening_peak = 0.65 * np.exp(-0.5 * ((hours - 19.0) / 2.2) ** 2)
    midday_use = 0.20 * np.exp(-0.5 * ((hours - 13.0) / 3.5) ** 2)
    return 0.45 + morning_peak + evening_peak + midday_use


def generate_dataset() -> pd.DataFrame:
    """Create normal network behaviour, then inject known anomaly periods."""
    rng = np.random.default_rng(RANDOM_SEED)
    timestamps = pd.date_range(
        START_TIME,
        periods=NUMBER_OF_DAYS * 24 * 4,
        freq=READING_FREQUENCY,
    )
    rows: list[pd.DataFrame] = []

    for zone_number in range(1, NUMBER_OF_ZONES + 1):
        zone_id = f"Z{zone_number:02d}"
        zone_size = rng.uniform(0.78, 1.28)
        base_consumption = rng.uniform(18.0, 27.0) * zone_size
        base_pressure = rng.uniform(43.0, 57.0)

        hour = timestamps.hour.to_numpy() + timestamps.minute.to_numpy() / 60
        daily_pattern = _daily_demand_multiplier(hour)
        # Weekend demand is slightly later and a little lower overall.
        weekend = timestamps.dayofweek.to_numpy() >= 5
        weekly_factor = np.where(weekend, 0.93, 1.0)
        consumption = base_consumption * daily_pattern * weekly_factor
        consumption *= rng.normal(1.0, 0.045, len(timestamps))
        consumption = np.clip(consumption, 2.0, None)

        # Flow is an hourly rate, while consumption is volume per 15 minutes.
        # The added baseline represents normal network losses and tank movement.
        flow = consumption * 4.0 * rng.normal(1.08, 0.025, len(timestamps)) + 3.0
        pressure = base_pressure - 0.075 * (flow - flow.mean())
        pressure += 1.4 * np.sin(2 * np.pi * (hour - 2) / 24)
        pressure += rng.normal(0.0, 0.65, len(timestamps))
        pressure = np.clip(pressure, 30.0, 70.0)

        rows.append(
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "zone_id": zone_id,
                    "flow_m3_per_hour": flow,
                    "pressure_m_head": pressure,
                    "consumption_m3": consumption,
                    "is_synthetic_anomaly": False,
                    "anomaly_type": "normal",
                }
            )
        )

    data = pd.concat(rows, ignore_index=True)
    _inject_anomalies(data)

    measurement_columns = ["flow_m3_per_hour", "pressure_m_head", "consumption_m3"]
    data[measurement_columns] = data[measurement_columns].round(3)
    return data.sort_values(["timestamp", "zone_id"], ignore_index=True)


def _inject_anomalies(data: pd.DataFrame) -> None:
    """Modify data in place for the known periods listed above."""
    for event in ANOMALY_PERIODS:
        mask = (
            (data["zone_id"] == event["zone_id"])
            & (data["timestamp"] >= pd.Timestamp(event["start"]))
            & (data["timestamp"] < pd.Timestamp(event["end"]))
        )
        anomaly_type = event["type"]

        if anomaly_type == "high_flow":
            data.loc[mask, "flow_m3_per_hour"] *= 1.75
        elif anomaly_type == "low_pressure":
            data.loc[mask, "pressure_m_head"] -= 16.0
        elif anomaly_type == "flow_consumption_divergence":
            data.loc[mask, "flow_m3_per_hour"] += 48.0
            data.loc[mask, "pressure_m_head"] -= 3.0
        elif anomaly_type == "high_consumption_low_flow":
            data.loc[mask, "consumption_m3"] *= 1.70
            data.loc[mask, "flow_m3_per_hour"] *= 1.08
        elif anomaly_type == "combined_flow_pressure":
            data.loc[mask, "flow_m3_per_hour"] *= 1.55
            data.loc[mask, "pressure_m_head"] -= 12.0
        elif anomaly_type == "flow_spike":
            data.loc[mask, "flow_m3_per_hour"] *= 2.40

        data.loc[mask, "pressure_m_head"] = data.loc[mask, "pressure_m_head"].clip(20.0, 70.0)
        data.loc[mask, "is_synthetic_anomaly"] = True
        data.loc[mask, "anomaly_type"] = anomaly_type


def main() -> None:
    """Generate the CSV next to the project, regardless of current directory."""
    output_path = Path(__file__).resolve().parents[1] / "data" / "water_network.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = generate_dataset()
    data.to_csv(output_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print(f"Created {output_path}")
    print(f"Rows: {len(data):,}; columns: {len(data.columns)}")
    print(f"Anomaly periods: {len(ANOMALY_PERIODS)}; flagged readings: {int(data['is_synthetic_anomaly'].sum()):,}")


if __name__ == "__main__":
    main()
