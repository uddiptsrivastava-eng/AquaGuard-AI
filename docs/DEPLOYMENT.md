# Deployment Readiness

## Current local run

From the AquaGuard folder:

```powershell
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
```

## Recommended hackathon route: Streamlit Community Cloud

Streamlit Community Cloud deploys from a GitHub repository. Before publishing:

1. Confirm the repository contains only synthetic data and no credentials.
2. Push the AquaGuard project to GitHub.
3. Sign in to Streamlit Community Cloud.
4. Choose **Create app** and select the repository and branch.
5. Set the entrypoint to `app.py`.
6. Deploy, then verify every page and the saved validation numbers.

Official instructions: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## Files already prepared

- `app.py` — application entrypoint
- `requirements.txt` — Python dependencies
- `.streamlit/config.toml` — consistent theme and headless server configuration
- `data/processed_water_network.csv` — synthetic processed observations
- `data/synthetic_validation.json` — validation summary

## Pre-deployment checks

```powershell
& ".\.venv\Scripts\python.exe" -m unittest discover -s tests -v
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
```

Confirm that no page contains private information, secrets, real customer consumption, or claims of confirmed leakage.

## Important distinction

Community Cloud is appropriate for a public synthetic hackathon demonstration. A real utility deployment would require private infrastructure, authentication, encrypted telemetry, durable storage, monitoring, audit logs, backups, and security/privacy review.

No external deployment was performed during Stage 4.
