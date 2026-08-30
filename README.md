# AquaGuard AI

AquaGuard AI is a hackathon decision-support prototype that prioritizes unusual water-distribution behaviour for human inspection. It does **not** definitively diagnose leakage or unauthorized consumption.

## Current dataset

This `real-data` branch uses the public **Sewer Network and Smart Water Meter Data for Modelling and Analysis of Water Distribution and Sewer Networks** dataset produced by NTNU/SINTEF and published through the EU Open Research Repository:

- Source: https://doi.org/10.5281/zenodo.14001028
- Source archive: `WDN Data.rar`
- Published archive MD5: `8f4440c2511a01191adac57c43503a29`
- Measurement period: September 2023
- Geography: one anonymized monitored DMA
- Usable smart-meter sites: 15
- Documented controlled hydrant leak tests: 21

The archive contains real field measurements and controlled leak experiments. It is not live telemetry, a 20-zone city dataset, or proof of production detection performance. SWM1 is excluded because the publisher documents possible sensor faults.

## Data preparation

`src/real_data_ingestion.py` converts the public source into three compact files:

- `data/real_water_network.csv` — 719 hourly DMA observations.
- `data/real_meter_sites.csv` — hourly pressure and consumption for 15 anonymized meter sites.
- `data/controlled_leak_events.csv` — 21 publisher-documented controlled test periods.

The raw inlet file contains duplicate timestamps; repeated transmissions are averaged before hourly aggregation. Smart-meter files mix minute-level readings with hourly cumulative values. Consumption is calculated from differences between consecutive hourly cumulative meter readings. Negative differences are treated as meter resets and excluded. Pressure is converted using:

```text
pressure_m_head = pressure_bar × 10.19716213
```

The hourly DMA balance is:

```text
unaccounted_water_m3 = inlet_volume − outlet_volume − metered_consumption
```

This balance can also reflect timing, incomplete metering, storage, sensor uncertainty, or authorized unmetered use; it is not automatically leakage.

## Model and risk scoring

The pipeline creates past-only hourly baselines for inlet flow, pressure, and metered consumption. Isolation Forest analyzes measurements and deviations without receiving `is_controlled_leak` or `leak_event_ids`.

The transparent prototype risk score remains a 0–100 inspection-priority score:

| Signal | Maximum points |
|---|---:|
| Isolation Forest anomaly strength | 35 |
| Positive unaccounted-water signal | 20 |
| Low-pressure deviation | 15 |
| Inlet-flow deviation | 10 |
| Consumption deviation | 10 |
| Persistence across eight hourly readings | 10 |

Categories are `NORMAL` below 40, `MONITOR` from 40 to below 70, and `HIGH RISK` from 70. These are prototype thresholds, not calibrated leak probabilities.

## Controlled-test validation

Current results are intentionally reported without embellishment:

- Hourly observations: 719
- Hours overlapping controlled tests: 14
- Isolation Forest flags: 15
- Controlled-test hours flagged by Isolation Forest: 1
- Precision: 6.7%
- Recall: 7.1%
- F1: 6.9%
- Controlled tests with at least one Isolation Forest flag: 2 of 21
- Controlled tests reaching `MONITOR` or `HIGH RISK` through the combined risk rules: 16 of 21

The short tests last roughly 9–32 minutes while the normalized model works at hourly resolution, which weakens direct Isolation Forest detection. These results demonstrate that replacing synthetic data with real measurements can make performance materially harder. They are retained honestly rather than replaced with fake accuracy.

## Dashboard pages

1. **Command Center** — selected-hour inlet, outlet, consumption, pressure, water balance, risk, controlled-test context, alerts, and What-if Scenario Lab.
2. **Meter Sites** — an interactive overview of 15 anonymized real meter locations. Positions are conceptual because public geography is restricted.
3. **Network Map** — a conceptual sensor topology, not a real pipe map.
4. **DMA Intelligence** — detailed DMA flow-balance, pressure, risk charts, and hourly history.
5. **Alerts** — filterable inspection candidates.
6. **Model Validation** — honest results against the documented controlled tests.

## Setup and run

From the `AquaGuard` folder in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\run_pipeline.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open `http://localhost:8501` if the browser does not open automatically.

Run the tests with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Rebuilding normalized data from the archive

Extract `WDN Data.rar`, then run:

```powershell
.\.venv\Scripts\python.exe src\real_data_ingestion.py "C:\path\to\extracted\WDN Data"
.\.venv\Scripts\python.exe src\run_pipeline.py
```

## Limitations

- One monitored DMA, not a city-wide network.
- Public locations are anonymized.
- Controlled hydrant tests are not naturally occurring hidden leaks.
- Hourly aggregation loses detail from short leak tests.
- Smart-meter coverage is incomplete relative to all possible consumers.
- No live SCADA connection, database, authentication, GIS, or hydraulic simulation.
- Risk scores prioritize investigation and require engineering review.

Supporting demonstration, deployment, and real-world rollout notes remain under `docs/`.
