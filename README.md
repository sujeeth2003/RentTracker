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
