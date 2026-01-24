import requests
from bs4 import BeautifulSoup
import json
import re
import datetime
import sys
import io
import unicodedata
import argparse
from pypdf import PdfReader

URL = "https://www.tepco.co.jp/ep/private/fuelcost2/newlist/index-j.html"
OUTPUT_FILE = "tepco_rates.json"

def clean_text(text):
    return text.strip().replace("\n", "").replace("\r", "")

def parse_price(text):
    # Handle ▲ as negative
    is_negative = "▲" in text
    # Remove non-numeric chars except dot
    amount_str = re.sub(r"[^0-9.]", "", text)
    if not amount_str:
        return 0.0
    amount = float(amount_str)
    return -amount if is_negative else amount

def parse_year(text):
    # Extract year, e.g., "2026年" -> 2026
    match = re.search(r"(\d{4})", text)
    if match:
        return int(match.group(1))
    return None

def parse_month(text):
    # Extract month, e.g., "2月分" -> 2
    match = re.search(r"(\d{1,2})", text)
    if match:
        return int(match.group(1))
    return None

def get_standard_s_constants():
    # Base Rate (10A increments)
    unit_price_10a = 311.75
    base_rates = {}
    for ampere in range(10, 61, 10):
        base_rates[f"{ampere}A"] = round(unit_price_10a * (ampere / 10), 2)
    
    return {
        "base_rate_per_10a": unit_price_10a,
        "base_rates": base_rates,
        "usage_rates": [
            {"min": 0, "max": 120, "price": 29.80},
            {"min": 121, "max": 300, "price": 36.40},
            {"min": 301, "max": None, "price": 40.49}
        ]
    }

def check_renewable_energy_pdf(year):
    # Construct URL: https://www.tepco.co.jp/ep/renewable_energy/institution/pdf/YYYYMMDD.pdf
    # Usually May 1st
    url = f"https://www.tepco.co.jp/ep/renewable_energy/institution/pdf/{year}0501.pdf"
    print(f"Checking for Renewable Energy Levy PDF at {url}...")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Parse PDF
            with io.BytesIO(response.content) as f:
                reader = PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
            
            # Normalize text to handle fullwidth characters (e.g., ３．４９)
            text = unicodedata.normalize('NFKC', text)
            
            # Search for the rate
            # Look for patterns like "単価" followed by number and "円"
            # It might be in a table. 
            # Example text might contain: "再生可能エネルギー発電促進賦課金単価 3.49 円"
            # Or "賦課金単価(円/kWh) 3.49"
            
            # Simple regex to find a float near "円" or just search for the specific context
            # Given the sample output "４９電気 .74 2" was bad, but normalization might fix it.
            # Let's try to find a number with decimal point followed by "円"
            # The rate is typically around 1.00 to 5.00
            
            # Regex: Look for number (integer or decimal) followed by optional whitespace and '円'
            # We want to be careful not to pick up other numbers (dates etc)
            # The rate is usually mentioned as "単価"
            
            # Clean up text a bit more
            text = text.replace("\n", "")
            
            match = re.search(r'単価.*?(\d+(\.\d+)?)円', text)
            if not match:
                # Try finding just number if "円" is separated
                # Or look for "3.49" explicitly? No, we want to find new rates.
                # Try broader search: "賦課金" ... number ... "円"
                 match = re.search(r'賦課金.*?(\d+\.\d+)円', text)
            
            if match:
                price = float(match.group(1))
                print(f"Found Renewable Energy Levy for {year}: {price}")
                return price
            else:
                print(f"PDF found but could not extract price from text.")
                # Debug print
                # print(f"Text dump: {text[:200]}")
    except Exception as e:
        print(f"Failed to fetch or parse PDF for {year}: {e}")
    
    return None

def get_renewable_energy_levy(should_scrape_pdf=False):
    # Initial hardcoded values
    levies = [
        {"start": "2024-05", "end": "2025-04", "price": 3.49},
        {"start": "2025-05", "end": "2026-05", "price": 3.98}
    ]
    
    if not should_scrape_pdf:
        return levies
    
    # Check for future years (current year + 1, etc) to see if new rate is published
    current_year = datetime.datetime.now().year
    
    # Check for this year (if after April) and next year.
    # The list covers up to 2026-05.
    
    # Let's check for 2026 (May 2026) and 2027 just in case script runs long term
    years_to_check = [2026, 2027]
    
    for year in years_to_check:
        # Check if we already have it
        already_has = False
        for l in levies:
            if l["start"] == f"{year}-05":
                already_has = True
                break
        
        if not already_has:
            price = check_renewable_energy_pdf(year)
            if price:
                levies.append({
                    "start": f"{year}-05",
                    "end": f"{year+1}-05",
                    "price": price
                })
                
    return levies

def scrape_tepco_rates(html_content=None):
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
    else:
        response = requests.get(URL)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')

    # Find the section "燃料費調整単価（低圧）"
    # We look for the div with id "anker01" as identified in research
    target_div = soup.find('div', id='anker01')
    if not target_div:
        # Fallback by searching for text
        for a in soup.find_all('a'):
            if "燃料費調整単価（低圧）" in a.text:
                target_div = a.find_parent('div', class_='question').find_parent('div', class_='faq-element')
                break
    
    if not target_div:
        raise ValueError("Could not find the 'Fuel cost adjustment unit price (Low voltage)' section.")

    table = target_div.find('table')
    if not table:
        raise ValueError("Could not find the price table.")

    rows = table.find_all('tr')
    fuel_adjustments = []
    
    current_year = None
    
    # Skip headers. Header rows usually contain 'th' or specific text.
    # We iterate and check if it's a data row.
    # Data rows start when we see a year or month.
    
    for row in rows:
        cols = row.find_all('td')
        if not cols:
            continue
            
        # Check if this is a header row (contains "適用年月" or similar)
        row_text = "".join([c.text for c in cols])
        if "適用年月" in row_text or "燃料費調整単価" in row_text or "円/kWh" in row_text:
            continue
            
        # Logic for data rows
        # Case 1: Year, Month, Price1, Price2 (4 cols)
        # Case 2: Month, Price1, Price2 (3 cols)
        
        month = None
        price_col_index = -1 
        
        if len(cols) == 4:
            # Year is in first column
            current_year = parse_year(cols[0].text)
            month = parse_month(cols[1].text)
            price_col_index = 3 # 4th column (index 3) is Standard S
        elif len(cols) == 3:
            # Month is in first column
            month = parse_month(cols[0].text)
            price_col_index = 2 # 3rd column (index 2) is Standard S
        else:
            # Unexpected row format
            continue
            
        if current_year and month:
            price_text = cols[price_col_index].text
            price = parse_price(price_text)
            
            entry = {
                "year": current_year,
                "month": month,
                "date_iso": f"{current_year}-{month:02d}-01",
                "price_kwh": price,
                "area": "Kanto",
                "type": "Low Voltage (Standard S)"
            }
            fuel_adjustments.append(entry)

    return fuel_adjustments

def get_current_rates(fuel_data, levy_data):
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    
    # 1. Find Fuel Adjustment for current month
    fuel_adj = None
    for entry in fuel_data:
        if entry["year"] == current_year and entry["month"] == current_month:
            fuel_adj = entry
            break
            
    # 2. Find Renewable Energy Levy for current month
    # Format "YYYY-MM"
    levy_val = None
    # We need to check if current date is within start and end
    # start/end are "YYYY-MM". Start is inclusive, end is exclusive (usually? or inclusive?)
    # "2024-05" to "2025-04" means May 2024 through April 2025.
    
    current_date_str = f"{current_year}-{current_month:02d}"
    
    for entry in levy_data:
        # Simple string comparison works for YYYY-MM if we range check
        # But let's be more robust.
        # Actually simplest is: Start <= Current <= End? 
        # The data says "2025-05" to "2026-05". Usually rates change in May.
        # So 2024-05 to 2025-04 is one period. 2025-05 to 2026-05 is next.
        # Wait, 2026-05 is listed as END of a period?
        # Re-reading my previous code: 
        # {"start": "2024-05", "end": "2025-04", "price": 3.49},
        # {"start": "2025-05", "end": "2026-05", "price": 3.98}
        
        # If I am in May 2025, matches 2nd entry.
        # If I am in April 2025, matches 1st entry.
        
        # Parse start and end
        start_y, start_m = map(int, entry["start"].split('-'))
        end_y, end_m = map(int, entry["end"].split('-'))
        
        # Construct comparable integers or dates
        # Using YYYYMM integer logic
        curr_val = current_year * 100 + current_month
        start_val = start_y * 100 + start_m
        end_val = end_y * 100 + end_m
        
        # If the range is [Start, End], treating matches.
        # Usually levy is valid UNTIL the next change.
        # The end date in my hardcode seems to represent the last month or the renewal month?
        # 2025-05 to 2026-05... that's 13 months? usually it's 12 months.
        # May to April.
        # Let's assume the helper logic I wrote earlier "f'{year}-05' to f'{year+1}-05'" might be slightly loose.
        # But let's just check if current month falls in the range.
        
        if start_val <= curr_val <= end_val:
            levy_val = entry["price"]
            break

    return {
        "year": current_year,
        "month": current_month,
        "date_iso": today.isoformat(),
        "fuel_adjustment": fuel_adj["price_kwh"] if fuel_adj else None,
        "renewable_energy_levy": levy_val
    }

def main():
    parser = argparse.ArgumentParser(description='Scrape TEPCO rates.')
    parser.add_argument('file', nargs='?', help='Local HTML file to parse (optional)')
    parser.add_argument('--scrape-pdf', action='store_true', help='Enable scraping of Renewable Energy Levy PDF')
    
    args = parser.parse_args()

    try:
        # Check if a file argument is provided (for testing)
        if args.file:
            with open(args.file, 'r', encoding='utf-8') as f:
                html = f.read()
            fuel_data = scrape_tepco_rates(html)
        else:
            fuel_data = scrape_tepco_rates()

        levy_data = get_renewable_energy_levy(should_scrape_pdf=args.scrape_pdf)
        
        data = {
            "current_rates": get_current_rates(fuel_data, levy_data),
            "fuel_adjustment": fuel_data,
            "standard_s": get_standard_s_constants(),
            "renewable_energy_levy": levy_data
        }

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Successfully wrote data to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {e}")
        # Print full traceback for debugging
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
