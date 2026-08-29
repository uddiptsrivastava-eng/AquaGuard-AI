# AquaGuard AI — Five-Minute Hackathon Demo

## Opening (30 seconds)

Urban water utilities cannot place sensors on every pipe. AquaGuard AI uses strategic zone-level flow and pressure measurements plus available consumption data to identify anomalous behaviour and prioritize human inspection. It does not claim to confirm leaks.

## Command Center (45 seconds)

Open **Command Center**. Explain that every displayed value comes from the processed synthetic dataset. Click **Show high-risk example** to move from the latest calm network state to a documented abnormal period. Point out total supplied volume, total consumption, imbalance, zone status, and the transparent network-health formula.

## City and zone investigation (90 seconds)

Open **City Overview**. Set the inspection hour to **24 Jan 2026 · 20:00**, select the South District, then inspect **Z18**. Explain that the map is conceptual.

Open **Zone Intelligence**, select Z18, and choose the seven-day window. Compare supplied flow volume with recorded consumption; then show pressure and risk over time. Emphasize persistence and the deterministic explanation.

## What-if interaction (45 seconds)

Return to Command Center and enter:

- Flow: 250 m³/h
- Consumption: 15 m³ per 15 minutes
- Pressure: 30 m head
- Persistence: 8 of 8 readings

Explain that this is a rule-based scenario estimate, not live Isolation Forest inference or a leak probability.

## Validation (45 seconds)

Open **Model Validation**. Explain precision, recall, and event detection in plain language. State that all six simulated events had at least one model flag, while the low precision produces unnecessary inspection candidates. These are synthetic prototype results, not real-world accuracy.

## Real-world close (45 seconds)

Conclude by proposing a 5–10 DMA pilot with strategic inlet-flow sensors, pressure sensors, existing consumption data, an 8–12 week baseline period, and a 3–6 month shadow pilot. Engineers retain authority; confirmed field outcomes become the evidence for later calibration.

## Closing line

“AquaGuard does not replace utility engineers. It helps them decide where limited inspection resources should go first.”

## Likely judge questions

**Why Isolation Forest?** It can rank unusual behaviour without requiring a large labelled leak dataset.

**Why is precision low?** The prototype favors finding suspicious incidents, so it generates extra inspection candidates. A field pilot is needed to calibrate that trade-off.

**Does 80 mean an 80% leak probability?** No. It is an explicit prioritization score, not a calibrated probability.

**How can this work without sensors everywhere?** Monitor district-metered-area inlets and strategic pressure points, then combine them with available zone consumption data.

**What would you validate first?** Data quality, useful finding rate, false inspection rate, response time, sensor reliability, and estimated water saved.
