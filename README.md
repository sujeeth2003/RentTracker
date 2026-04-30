# RentTracker

## Overview

This project is an automated rent monitoring system that tracks apartment pricing data from a public floor-plan API and sends email alerts when prices drop below a defined threshold. It is designed to run periodically using GitHub Actions.

The system helps detect price changes early and avoids duplicate alerts by maintaining state across executions.

## Features
- Fetches real-time floor plan pricing data from an external API
- Extracts the lowest available rent across multiple apartment categories
- Compares prices against a defined threshold
- Sends email notifications when a new lower price is detected
- Prevents duplicate alerts using state tracking
- Fully automated execution using GitHub Actions
## Architecture

### The system consists of:

- Data Source
- A public API providing apartment floor plans and pricing information.
- Processing Layer
- Python script that:
  - Parses JSON data
  - Extracts pricing information
  - Identifies lowest available rent
- Alerting Layer
  - Email notifications sent via SMTP (Gmail)
  - Scheduler
  - GitHub Actions workflow running on a scheduled interval
### Project Structure

    RentTracker/
    │
    ├── tracker.py               # Main script
    ├── requirements.txt         # Dependencies
    ├── state.json               # Local execution state (runtime generated)
    │
    └── .github/
        └── workflows/
            └── run.yml          # GitHub Actions workflow

## Setup Instructions

1. Clone Repository

```
git clone https://github.com/<your-username>/RentTracker.git
cd RentTracker
```

3. Install Dependencies
```pip install -r requirements.txt```
4. Configure Environment Variables

### This project requires the following GitHub Secrets:
```
EMAIL: Your Gmail address
APP_PASSWORD: Gmail app password
```
#### To set them:

Go to
```
Repository → Settings → Secrets and variables → Actions → New repository secret
```
Running Locally

### To test the script manually:
```
python tracker.py
GitHub Actions Automation
```
The project is configured to run automatically using GitHub Actions.

Schedule

### Runs every hour using a cron job:
```
0 * * * *
Workflow
```
## The workflow:

- Sets up Python environment
- Installs dependencies
- Executes tracker script
- Sends email if conditions are met

## Alert Logic

### An email alert is triggered only when:

- Current price is below the defined threshold
- AND the price is lower than the last alerted value

### This ensures:

- No duplicate alerts
- Only meaningful price drops are notified
## Configuration

### Inside tracker.py:
```
URL → API endpoint for floor plan data
THRESHOLD → Minimum price trigger for alerts
```
#### Example:
```
THRESHOLD = 700
State Management
```
### The script maintains a lightweight state file:

state.json

### This stores:

- Lowest price seen
- Last alerted price

This helps prevent repeated alerts for the same price level.

## Limitations
- Depends on availability of external API
- May require header adjustments if API introduces bot protection
- State persistence depends on execution environment
- GitHub Actions may have slight execution delays
## Future Improvements
- Add database storage for historical pricing
- Add visualization dashboard (Streamlit or similar)
- Support multiple apartment listings
- Add Telegram or SMS notifications
- Improve anomaly detection for pricing trends
## License

This project is for educational and personal use.
