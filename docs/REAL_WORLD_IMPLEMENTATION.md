# Real-World Implementation Plan

## Objective

Validate whether AquaGuard can produce a useful inspection shortlist from sparse, strategic measurements. The first deployment must remain a decision-support pilot, not an automated leak declaration system.

## Pilot scope

- Select 5–10 district-metered areas with understood boundaries.
- Connect one reliable inlet flow measurement per zone.
- Install pressure sensors at representative or hydraulically sensitive points.
- Use existing smart-meter, periodic-meter, or billing consumption where available.
- Record maintenance, firefighting, valve operations, and known meter faults.

## Data path

1. Sensors and existing meters produce timestamped readings.
2. Utility telemetry or SCADA transports the measurements.
3. Quality checks detect missing values, duplicates, unit errors, clock drift, and sensor failure.
4. Zone-specific historical baselines describe normal time-of-day and day-of-week behaviour.
5. AquaGuard produces anomaly signals, persistence, a prioritization score, and explanations.
6. Control-room staff review the recommendation.
7. Field teams inspect when operationally justified.
8. Confirmed outcomes are recorded for evaluation and later calibration.

## Rollout phases

### Phase 1 — Instrument and validate

Confirm zone boundaries, sensor placement, units, calibration, timestamp alignment, and data ownership.

### Phase 2 — Establish baselines

Collect at least 8–12 weeks of stable observations, including weekdays, weekends, maintenance activity, and demand variation.

### Phase 3 — Shadow pilot

Run AquaGuard beside existing utility workflows for 3–6 months. Do not automate operational actions. Record why each alert was accepted, deferred, or dismissed.

### Phase 4 — Evidence-led expansion

Expand only after the pilot demonstrates operational value. Recalibrate by zone and season, strengthen security and governance, and monitor performance drift.

## Success measures

- Alerts investigated
- Useful finding rate
- Unnecessary inspection rate
- Time from alert to investigation
- Estimated water loss avoided
- Sensor and communication availability
- Staff time saved
- Distribution of alert causes

## Production requirements

Authentication, role-based access, encrypted transport and storage, audit logs, backups, retention policies, customer-consumption privacy, sensor-health monitoring, alert ownership, incident workflows, model/version records, and rollback procedures.

## Key limitation

Real networks contain maintenance, firefighting, legitimate demand changes, storage behaviour, meter errors, sensor drift, and incomplete data. Field confirmation—not synthetic labels—must determine real-world usefulness.
