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

