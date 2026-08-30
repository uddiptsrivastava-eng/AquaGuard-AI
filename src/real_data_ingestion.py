"""Normalize the public NTNU/SINTEF water-distribution dataset.

The source archive is published at https://doi.org/10.5281/zenodo.14001028.
It represents one monitored DMA during September 2023. Smart-meter files mix
minute-level instantaneous consumption with an hourly cumulative meter value;
the cumulative value occurs at each meter's fixed reporting minute. This module
uses differences between those hourly cumulative readings to obtain consumption.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SOURCE_URL = "https://doi.org/10.5281/zenodo.14001028"
SOURCE_ARCHIVE_MD5 = "8f4440c2511a01191adac57c43503a29"
PRESSURE_METRES_PER_BAR = 10.19716213


def _hourly_flow(path: Path, name: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    data["timestamp"] = pd.to_datetime(data.pop("Timestamp"), errors="raise")
    data[name] = pd.to_numeric(data.pop("Flow (m3/hr)"), errors="coerce")
    # The inlet logger contains repeated timestamps. Averaging duplicates avoids
    # counting repeated transmissions as extra water.
    data = data.groupby("timestamp", as_index=False)[name].mean().set_index("timestamp")
    hourly = data[name].resample("1h").agg(["mean", "count"])
    hourly.columns = [name, f"{name}_samples"]
    return hourly


def _meter_hourly(path: Path) -> pd.DataFrame:
    meter_id = path.stem
    data = pd.read_csv(path)
    data["timestamp"] = pd.to_datetime(data.pop("Timestamp"), errors="raise")
    pressure_col = f"{meter_id}_Pressure"
    flow_col = f"{meter_id}_flow"

    reporting_minute = int(data["timestamp"].iloc[0].minute)
    cumulative = data.loc[data["timestamp"].dt.minute == reporting_minute, ["timestamp", flow_col]].copy()
    cumulative["consumption_m3"] = pd.to_numeric(cumulative[flow_col], errors="coerce").diff() / 1000.0
    # Negative differences indicate a meter reset or invalid cumulative reading.
    cumulative.loc[cumulative["consumption_m3"] < 0, "consumption_m3"] = np.nan
    cumulative["timestamp"] = cumulative["timestamp"].dt.floor("h")
    cumulative = cumulative.groupby("timestamp", as_index=True)["consumption_m3"].last()

    pressure = data.set_index("timestamp")[pressure_col].resample("1h").median()
    result = pd.concat([pressure.rename("pressure_bar"), cumulative], axis=1).reset_index()
    result["pressure_m_head"] = result["pressure_bar"] * PRESSURE_METRES_PER_BAR
    result["meter_id"] = meter_id
    return result[["timestamp", "meter_id", "pressure_bar", "pressure_m_head", "consumption_m3"]]


def _load_events(path: Path) -> pd.DataFrame:
    events = pd.read_csv(path)
    starts, ends = [], []
    for row in events.itertuples(index=False):
        date = pd.to_datetime(row[0], dayfirst=True)
        start = pd.Timestamp(f"{date.date()} {row[2]}")
        end = pd.Timestamp(f"{date.date()} {row[3]}")
        if end <= start:
            end += timedelta(days=1)
        starts.append(start)
        ends.append(end)
    result = pd.DataFrame({
        "leak_event_id": [f"TEST_{number:02d}" for number in range(1, len(events) + 1)],
        "start": starts,
        "end": ends,
        "controlled_leak_flow_m3h": pd.to_numeric(events.iloc[:, 1], errors="raise"),
    })
    return result


def normalize_dataset(source_dir: Path) -> dict:
    """Create compact, auditable CSV files used by the real-data pipeline."""
    inflow = _hourly_flow(source_dir / "inflow.csv", "inflow_m3h")
    outflow = _hourly_flow(source_dir / "outflow.csv", "outflow_m3h")

    meter_frames = []
    for path in sorted((source_dir / "SWM Data").glob("*.csv")):
        if path.stem == "SWM1":  # The publisher documents SWM1 as faulty.
            continue
        meter_frames.append(_meter_hourly(path))
    meters = pd.concat(meter_frames, ignore_index=True)
    meter_summary = meters.groupby("timestamp").agg(
        consumption_m3=("consumption_m3", "sum"),
        meter_coverage=("consumption_m3", "count"),
        pressure_m_head=("pressure_m_head", "median"),
        pressure_site_coverage=("pressure_m_head", "count"),
    )

    network = inflow.join(outflow, how="outer").join(meter_summary, how="outer").reset_index()
    network = network.loc[(network["timestamp"] >= "2023-09-01") & (network["timestamp"] < "2023-10-01")].copy()
    network["zone_id"] = "REAL_DMA_01"
    network["interval_hours"] = 1.0
    network["flow_m3_per_hour"] = network["inflow_m3h"]
    network["flow_volume_m3"] = network["inflow_m3h"]
    network["outflow_volume_m3"] = network["outflow_m3h"]
    network["unaccounted_water_m3"] = (
        network["flow_volume_m3"] - network["outflow_volume_m3"] - network["consumption_m3"]
    )

    events = _load_events(source_dir / "Leak_events.csv")
    network["is_controlled_leak"] = False
    network["leak_event_ids"] = ""
    for event in events.itertuples(index=False):
        interval_end = network["timestamp"] + timedelta(hours=1)
        overlap = (network["timestamp"] < event.end) & (interval_end > event.start)
        network.loc[overlap, "is_controlled_leak"] = True
        network.loc[overlap, "leak_event_ids"] = network.loc[overlap, "leak_event_ids"].map(
            lambda current: ";".join(filter(None, [current, event.leak_event_id]))
        )

    # The first hour has no earlier cumulative meter reading from which to
    # calculate consumption. Keep only hours with broad meter coverage.
    network = network.loc[network["meter_coverage"] >= 12].copy()
    network["leak_event_ids"] = network["leak_event_ids"].replace("", "NONE")

    network_columns = [
        "timestamp", "zone_id", "interval_hours", "flow_m3_per_hour", "flow_volume_m3",
        "outflow_m3h", "outflow_volume_m3", "consumption_m3", "pressure_m_head",
        "unaccounted_water_m3", "meter_coverage", "pressure_site_coverage",
        "inflow_m3h_samples", "outflow_m3h_samples", "is_controlled_leak", "leak_event_ids",
    ]
    network = network[network_columns].sort_values("timestamp")
    meters = meters.sort_values(["timestamp", "meter_id"])

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    network.to_csv(DATA_DIR / "real_water_network.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    meters.to_csv(DATA_DIR / "real_meter_sites.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    events.to_csv(DATA_DIR / "controlled_leak_events.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    manifest = {
        "source": SOURCE_URL,
        "archive_file": "WDN Data.rar",
        "archive_md5": SOURCE_ARCHIVE_MD5,
        "publisher": "NTNU/SINTEF via the EU Open Research Repository (Zenodo)",
        "measurement_period": "September 2023",
        "dma_count": 1,
        "usable_meter_sites": int(meters["meter_id"].nunique()),
        "controlled_leak_tests": int(len(events)),
        "notes": "SWM1 excluded because the publisher documents possible sensor faults.",
    }
    (DATA_DIR / "real_data_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normalize the extracted public WDN dataset.")
    parser.add_argument("source_dir", type=Path, help="Path to the extracted 'WDN Data' folder")
    print(json.dumps(normalize_dataset(parser.parse_args().source_dir), indent=2))
