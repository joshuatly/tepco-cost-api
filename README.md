# TEPCO Cost API Scraper

This repository contains a tool to scrape electricity rate adjustments from TEPCO (Tokyo Electric Power Company) and expose them as a JSON file. It is designed to be automated via GitHub Actions.

## 📊 Data Output: `tepco_rates.json`

The generated JSON file provides the data you need to calculate electricity costs.

**👉 [Direct Link to JSON Data](https://raw.githubusercontent.com/joshuatly/tepco-cost-api/refs/heads/main/tepco_rates.json)**

### 1. `current_rates` (The Canonical Source)
Use this object to get the rates applicable **right now** (based on the date the script ran). This is likely what you want for a dashboard or calculator.

```json
"current_rates": {
    "year": 2026,
    "month": 1,
    "date_iso": "2026-01-24",
    "fuel_adjustment": -7.72,      // Fuel Cost Adjustment (Yen/kWh)
    "renewable_energy_levy": 3.98  // Renewable Energy Levy (Yen/kWh)
}
```

### 2. `fuel_adjustment`
A list of historical and future fuel adjustment rates scraped from the [TEPCO website](https://www.tepco.co.jp/ep/private/fuelcost2/newlist/index-j.html). It tracks the "Low Voltage (Standard S)" column.

### 3. `standard_s`
Constants for the "Standard S" plan (Base Rates and Usage Tiers). these are hardcoded.

### 4. `renewable_energy_levy`
A list of levy periods.

---

## 🚀 Automation

The scraper runs automatically via **GitHub Actions**.

- **Schedule**: Runs twice a month (on the **1st** and **15th** at 00:00 UTC).
- **On Push**: Not configured to run on push to avoid churn, but runs on schedule.

### Manual Update (On-Demand)
You can trigger the scraper manually at any time:
1. Go to the **Actions** tab in this repository.
2. Select **Scrape TEPCO Rates**.
3. Click **Run workflow**.

### Updating Renewable Energy Levy (PDF Scraping)
The "Renewable Energy Levy" is usually updated once a year (around May). To check for a new rate:
1. Go to **Actions** -> **Scrape TEPCO Rates** -> **Run workflow**.
2. Check the box: **Scrape Renewable Energy Levy PDF**.
3. Click **Run workflow**.
This will attempt to download the official PDF from TEPCO and extract the new rate safely.

---

## 🛠️ Local Usage

To run the script locally:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the scraper**:
   ```bash
   python scrape_tepco.py
   ```
   This updates `tepco_rates.json`.

3. **Run with PDF scraping**:
   ```bash
   python scrape_tepco.py --scrape-pdf
   ```

---

## ✅ How to verify it's working

1. **Check the Badge**: You can add a status badge to this README from the Actions tab.
2. **Check `tepco_rates.json`**:
   - Look at the `current_rates` object at the top.
   - Verify `date_iso` matches the last run date.
3. **Check Action Logs**:
   In the Actions tab, click on a run to see the logs. If `scrape_tepco.py` fails (e.g., TEPCO changes their website layout), the Action will fail and send an email notification to the repo owner.
