# AquaGuard AI — Real-Data Demo Script

## Opening

Explain that AquaGuard now uses a public September 2023 field dataset from one anonymized monitored DMA. It contains inlet/outlet flow, 15 usable smart-meter sites, pressure, consumption, and 21 controlled hydrant leak tests. It is not live telemetry or a city-wide deployment.

## Command Center

Use **Show highest-risk hour**. Explain inlet volume, outlet volume, metered consumption, the resulting DMA balance, median pressure, and risk category. Point out whether a documented controlled test overlaps the selected hour.

## Meter Sites

Move the hourly selector and inspect individual smart-meter locations. Explain that the points are anonymized measurement sites and that their positions are conceptual rather than geographic.

## DMA Intelligence

Compare inlet volume, outlet volume, and metered consumption. Then show pressure and risk history. Explain that an unexplained balance can also reflect incomplete metering, timing, storage, or measurement uncertainty.

## What-if Scenario Lab

Enter higher inlet flow, lower outlet flow, low metered consumption, lower pressure, and sustained hours. State that this is a transparent rule-based estimate and does not rerun Isolation Forest.

## Model Validation

Explain the real results honestly: Isolation Forest directly covers only 2 of 21 short controlled tests after hourly aggregation, while the combined risk rules reach MONITOR or HIGH RISK for 16 of 21 tests. Do not present this as production accuracy.

## Closing line

“AquaGuard does not declare a leak. It turns imperfect field measurements into an explainable inspection priority, and the real-data results show exactly where the prototype still needs finer time resolution and utility calibration.”
