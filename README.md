# TEPCO Cost API Scraper / TEPCO電気料金APIスクレイパー

![Scrape TEPCO Rates](https://github.com/joshuatly/tepco-cost-api/actions/workflows/scrape_tepco.yml/badge.svg)

This repository contains a tool to scrape electricity rate adjustments from TEPCO (Tokyo Electric Power Company) and expose them as a JSON file. It is designed to be automated via GitHub Actions.  
このリポジトリには、TEPCO（東京電力）から電気料金の調整額をスクレイピングし、JSONファイルとして公開するツールが含まれています。GitHub Actionsで自動化されるように設計されています。

## 📊 Data Output: `tepco_rates.json` / データ出力: `tepco_rates.json`

The generated JSON file provides the data you need to calculate electricity costs.  
生成されたJSONファイルは、電気料金の計算に必要なデータを提供します。

**👉 [Direct Link to JSON Data / JSONデータへの直接リンク](https://raw.githubusercontent.com/joshuatly/tepco-cost-api/refs/heads/main/tepco_rates.json)**

### 1. `current_rates` (The Canonical Source) / `current_rates` (正本データ)
Use this object to get the rates applicable **right now** (based on the date the script ran). This is likely what you want for a dashboard or calculator.  
現在適用可能な料金（スクリプト実行日基準）を取得するには、このオブジェクトを使用してください。ダッシュボードや計算機での使用に最適です。

```json
"current_rates": {
    "year": 2026,
    "month": 1,
    "date_iso": "2026-01-24",
    "fuel_adjustment": -7.72,      // Fuel Cost Adjustment (Yen/kWh) / 燃料費調整額 (円/kWh)
    "renewable_energy_levy": 3.98  // Renewable Energy Levy (Yen/kWh) / 再エネ賦課金 (円/kWh)
}
```

### 2. `fuel_adjustment` / `fuel_adjustment` (燃料費調整額)
A list of historical and future fuel adjustment rates scraped from the [TEPCO website](https://www.tepco.co.jp/ep/private/fuelcost2/newlist/index-j.html). It tracks the "Low Voltage (Standard S)" column.  
[TEPCOのウェブサイト](https://www.tepco.co.jp/ep/private/fuelcost2/newlist/index-j.html)からスクレイピングされた過去および将来の燃料費調整額のリストです。「低圧（スタンダードS）」の列を追跡しています。

### 3. `standard_s` / `standard_s` (スタンダードSプラン)
Constants for the "Standard S" plan (Base Rates and Usage Tiers). these are hardcoded.  
「スタンダードS」プランの定数（基本料金と従量料金の段階）。これらはハードコードされています。

### 4. `renewable_energy_levy` / `renewable_energy_levy` (再エネ賦課金)
A list of levy periods.  
再エネ賦課金の期間リストです。

---

## 🚀 Automation / 自動化

The scraper runs automatically via **GitHub Actions**.  
スクレイパーは **GitHub Actions** を介して自動的に実行されます。

- **Schedule**: Runs twice a month (on the **1st** and **15th** at 00:00 UTC).  
  **スケジュール**: 月に2回実行されます（**1日**と**15日**の00:00 UTC）。
- **On Push**: Not configured to run on push to avoid churn, but runs on schedule.  
  **プッシュ時**: 無駄な更新を避けるため、プッシュ時には実行されませんが、スケジュール通りに実行されます。

### Manual Update (On-Demand) / 手動更新 (オンデマンド)
You can trigger the scraper manually at any time:  
いつでも手動でスクレイパーをトリガーできます：

1. Go to the **Actions** tab in this repository.  
   このリポジトリの **Actions** タブに移動します。
2. Select **Scrape TEPCO Rates**.  
   **Scrape TEPCO Rates** を選択します。
3. Click **Run workflow**.  
   **Run workflow** をクリックします。

### Updating Renewable Energy Levy (PDF Scraping) / 再エネ賦課金の更新（PDFスクレイピング）
The "Renewable Energy Levy" is usually updated once a year (around May). To check for a new rate:  
「再エネ賦課金」は通常、年に1回（5月頃）更新されます。新しい料金を確認するには：

1. Go to **Actions** -> **Scrape TEPCO Rates** -> **Run workflow**.  
   **Actions** -> **Scrape TEPCO Rates** -> **Run workflow** へ移動します。
2. Check the box: **Scrape Renewable Energy Levy PDF**.  
   **Scrape Renewable Energy Levy PDF** のチェックボックスをオンにします。
3. Click **Run workflow**.  
   **Run workflow** をクリックします。

This will attempt to download the official PDF from TEPCO and extract the new rate safely.  
これにより、TEPCOから公式PDFをダウンロードし、新しい料金を安全に抽出することを試みます。

---

## 🛠️ Local Usage / ローカルでの使用方法

To run the script locally:  
ローカルでスクリプトを実行するには：

1. **Install dependencies** / **依存関係のインストール**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the scraper** / **スクレイパーの実行**:
   ```bash
   python scrape_tepco.py
   ```
   This updates `tepco_rates.json`.  
   これにより `tepco_rates.json` が更新されます。

3. **Run with PDF scraping** / **PDFスクレイピング付きで実行**:
   ```bash
   python scrape_tepco.py --scrape-pdf
   ```

---

## ✅ How to verify it's working / 動作確認方法

1. **Check the Badge**: The status badge at the top of this README indicates if the latest scheduled scrape was successful.  
   **バッジの確認**: このREADMEの上部にあるステータスバッジは、最新のスケジュールされたスクレイピングが成功したかどうかを示しています。
2. **Check `tepco_rates.json`** / **`tepco_rates.json` の確認**:
   - Look at the `current_rates` object at the top.  
     上部の `current_rates` オブジェクトを確認します。
   - Verify `date_iso` matches the last run date.  
     `date_iso` が前回の実行日と一致していることを確認します。
3. **Check Action Logs** / **アクションログの確認**:
   In the Actions tab, click on a run to see the logs. If `scrape_tepco.py` fails (e.g., TEPCO changes their website layout), the Action will fail and send an email notification to the repo owner.  
   Actionsタブで、実行をクリックしてログを確認します。もし `scrape_tepco.py` が失敗した場合（例：TEPCOがウェブサイトのレイアウトを変更した場合など）、Actionは失敗し、リポジトリの所有者にメール通知が送信されます。

---

## ⚠️ Disclaimer / 免責事項

This is an unofficial tool not affiliated with TEPCO; data may be inaccurate so use at your own risk.  
これはTEPCOとは関係のない非公式ツールです。データが不正確な場合があるため、自己責任でご使用ください。
