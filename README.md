# AquaGuard AI

AquaGuard AI is a small hackathon prototype intended to identify unusual water-network behaviour and prioritize urban distribution zones for human inspection. It does **not** claim to definitively detect leaks or unauthorized consumption.

## Current stage

This foundation contains a reproducible synthetic-data generator and its generated CSV. The dataset is illustrative only and does not represent a real utility, city, customer, or sensor network.

It covers 20 zones over 30 days (1–30 January 2026), with one reading every 15 minutes. Normal readings include morning and evening demand peaks, small weekday/weekend differences, flow that generally follows consumption, and moderate pressure changes.

## Dataset columns

| Column | Meaning |
|---|---|
| `timestamp` | Date and time of the reading, at 15-minute intervals |
| `zone_id` | Synthetic distribution-zone identifier (`Z01`–`Z20`) |
| `flow_m3_per_hour` | Simulated inlet flow rate in cubic metres per hour |
| `pressure_m_head` | Simulated pressure expressed as metres of water head |
| `consumption_m3` | Simulated metered consumption during the 15-minute interval, in cubic metres |
| `is_synthetic_anomaly` | `True` only for deliberately altered readings |
| `anomaly_type` | Name of the injected pattern, or `normal` |

## Documented synthetic anomaly periods

Period end times are exclusive, so a period ending at 08:00 contains readings up to 07:45.

| Zone | Start | End | Injected pattern |
|---|---|---|---|
| Z03 | 2026-01-05 02:00 | 2026-01-05 08:00 | Unusually high flow |
| Z07 | 2026-01-10 14:00 | 2026-01-10 20:00 | Unusually low pressure |
| Z11 | 2026-01-15 00:00 | 2026-01-16 00:00 | Flow/consumption divergence |
| Z14 | 2026-01-20 06:00 | 2026-01-20 12:00 | High consumption with little flow response |
| Z18 | 2026-01-24 18:00 | 2026-01-25 06:00 | Sustained high flow and low pressure |
| Z05 | 2026-01-28 09:00 | 2026-01-28 10:00 | Short, sharp flow spike |

These labels are included for later validation and should not be used as evidence that a real leak occurred.

## Setup and generation

From the `AquaGuard` directory:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/data_generator.py
```

The generator always uses random seed `42`, so running it again produces the same `data/water_network.csv` file.

The included `app.py` is deliberately only a placeholder. It can be viewed with `streamlit run app.py`, but the polished dashboard and machine-learning model have not been built.

## Stage 2: anomaly prioritization pipeline

Stage 2 adds feature engineering, historical baselines, unsupervised anomaly detection, transparent risk scoring, explanations, and synthetic validation. It does not add a polished dashboard.

```text
Raw Data
   ↓
Feature Engineering
   ↓
Historical Baselines
   ↓
Isolation Forest
   ↓
Anomaly Signal
   ↓
Risk Scoring
   ↓
Explanation
   ↓
Synthetic Validation
```

### Feature engineering and units

Feature engineering turns raw measurements into values that are easier to compare. `flow_m3_per_hour` is a rate for a whole hour, while `consumption_m3` is a volume measured over 15 minutes. Subtracting them directly would compare different units. The pipeline first calculates:

```text
flow_volume_m3 = flow_m3_per_hour × 0.25
```

It can then calculate unaccounted water using two comparable 15-minute volumes. A negative difference is retained rather than automatically treated as faulty data.

Time features describe the hour, weekday, and weekend. Sine and cosine hour features represent the fact that 23:45 and 00:00 are close together in a daily cycle.

### Historical baselines

Expected flow, consumption, and pressure are expanding averages of **earlier** readings for the same zone and 15-minute time-of-day slot. If that exact slot has no history yet, earlier readings from the zone are used. The first zone reading is bootstrapped to itself because no earlier evidence exists. There are no centered rolling windows, and future readings never influence earlier baselines.

### Isolation Forest

Isolation Forest is an unsupervised algorithm: it learns which combinations of measurements look rare without being told which rows contain injected anomalies. The numerical inputs are standardized, then 200 isolation trees are fitted with random state 42 and a prototype contamination setting of 2%.

Its continuous `model_anomaly_score` is stored with **larger values meaning more abnormal behaviour**. `model_is_anomaly` is its binary flag. Neither output is a confirmed leak diagnosis.

### Hidden synthetic labels

`is_synthetic_anomaly` and `anomaly_type` are synthetic ground truth. They are deliberately excluded from the model's input list. The evaluation module reveals them only after predictions and risk scores have been generated. This prevents the model from being given the answers it is supposed to find.

### AquaGuard prototype risk score

The 0–100 `risk_score` is a prototype prioritization score, **not a calibrated probability of leakage**. Its explicit weights are:

| Signal | Weight |
|---|---:|
| Isolation Forest anomaly strength | 35 |
| Positive unaccounted-water signal | 20 |
| Low-pressure deviation | 15 |
| Absolute flow deviation | 10 |
| Absolute consumption deviation | 10 |
| Persistence across the current and previous seven readings | 10 |

The prototype categories are `NORMAL` (0–39), `MONITOR` (40–69), and `HIGH RISK` (70–100). These thresholds are demonstration choices, not universal water-industry standards. Explanations are deterministic sentences produced from the measured signals; no external AI service is used.

### Synthetic validation and limitations

After processing, predictions are compared with the hidden labels at both reading and event level. Precision asks, “Of the readings flagged, how many were injected anomalies?” Recall asks, “Of the injected anomalies, how many were found?” F1 balances the two. Event detection asks whether at least one reading was found in each of the six documented periods.

These are **synthetic prototype validation results**, not real-world accuracy. The patterns are deliberately generated and may be easier or different from actual leakage, meter error, maintenance, demand changes, sensor drift, or unauthorized use. A real deployment would require utility data, engineering review, local threshold calibration, and field confirmation.

## Run Stage 2

From the `AquaGuard` directory, after installing `requirements.txt`:

```bash
python src/run_pipeline.py
python -m unittest discover -s tests -v
```

The pipeline preserves `data/water_network.csv` and creates:

- `data/processed_water_network.csv` — original columns plus features, model outputs, risk, and explanations
- `data/synthetic_validation.json` — synthetic-only evaluation summary

## Stage 3: Streamlit monitoring dashboard

The local dashboard presents the processed dataset as a professional inspection-prioritization product. It contains five sidebar sections:

1. **Command Center** — current zone status, transparent network KPIs, and priority observations.
2. **City Overview** — five simulated city districts, an adjustable inspection hour, conceptual zone locations, and an interactive inspection panel.
3. **Network Map** — a deterministic conceptual district-metered-area topology. It is not a map of real municipal infrastructure.
4. **Zone Intelligence** — zone selection, current measurements, baseline deviations, explanations, Plotly time-series charts, and an observation table with separate date and time columns.
5. **Alerts** — searchable filters for zone, category, time window, and minimum risk score.
6. **Model Validation** — results read directly from `synthetic_validation.json`, with plain-language precision, recall, and event-detection guidance.

Flow charts compare `flow_volume_m3` with `consumption_m3`, so both series represent cubic metres per 15-minute interval. Hourly flow rate is never plotted as if it were the same unit as interval consumption.

The Command Center includes an hourly timestamp slider. For the selected hour, it aggregates the four 15-minute observations per zone and displays total supplied input volume, total recorded consumption, positive water imbalance, and the latest zone status within that hour. Supplied input is calculated by summing `flow_volume_m3`, not by incorrectly summing the hourly flow-rate column.

The **Show high-risk example** button moves directly to the historical hour containing the dataset's highest risk score; **Return to latest hour** restores the final network snapshot. A What-if Scenario Lab accepts hypothetical flow, consumption, pressure, and persistence inputs. Its output uses the published risk rules with an explicit rule-based anomaly proxy because the saved Isolation Forest is not configured as a live inference service. It is labelled an estimate and does not change either CSV file.

### Network health indicator

The Command Center calculates its current network health indicator as:

```text
network health = 100 − mean latest risk score across all zones
```

This is a transparent prototype summary—not an established water-industry metric. The default position uses the latest available hour; moving the slider displays a historical hourly snapshot, not live telemetry.

### Run the dashboard

From the `AquaGuard` directory:

```bash
streamlit run app.py
```

If the processed files are missing, run `python src/run_pipeline.py` first. The app shows an informative message instead of failing silently.

### Screenshots

_Add Command Center, Network Map, and Zone Intelligence screenshots here before the final hackathon submission._

### Synthetic-data disclaimer

Every dashboard observation is generated from a synthetic 30-day simulation. The interface is not connected to live sensors, does not represent a real city, and does not provide confirmed leak detection. Alerts, anomaly signals, risk scores, network health, and validation metrics are prototype aids for prioritizing human inspection.

Deployment is intentionally outside Stage 3.

## Stage 4: hackathon readiness

The **Implementation Plan** dashboard page adds a guided five-minute demo, a practical real-world utility rollout, and a deployment-readiness summary. Supporting documents are available under `docs/`:

- `DEMO_SCRIPT.md`
- `REAL_WORLD_IMPLEMENTATION.md`
- `DEPLOYMENT.md`

The project is prepared for a public synthetic demonstration but has not been deployed. Review the deployment checklist before connecting GitHub or publishing through Streamlit Community Cloud.
