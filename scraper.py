import json
import re
from datetime import datetime, timezone

OUTPUT_FILE = "listings.json"

def load_existing():
    try:
        with open(OUTPUT_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"listings": []}

def main():
    SOURCE_URL = "https://www.merrittislandcocoabeachhomes.com/merritt-towers-condo/"
    print(f"Fetching {SOURCE_URL} with Playwright...")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page.goto(SOURCE_URL, wait_until="networkidle", timeout=30000)
            try:
                page.wait_for_selector('a[href*="/property/"]', timeout=10000)
                print("Found property links on page!")
            except:
                print("No property links found via selector")
            html = page.content()
            browser.close()

        print(f"\nPage length: {len(html)} chars")
        print(f"Contains 'Currently Listed': {'Currently Listed' in html}")
        print(f"Contains '/property/': {'/property/' in html}")
        print(f"Contains 'MLS': {'MLS' in html}")

        prop_links = re.findall(r'href="([^"]*property[^"]*)"', html, re.I)
        print(f"\nProperty links found: {len(prop_links)}")
        for link in prop_links[:5]:
            print(f"  {link}")

        prices = re.findall(r'\$[\d,]+', html)
        print(f"\nPrices found: {prices[:10]}")

        idx = html.find("Currently Listed")
        if idx > -1:
            print(f"\n--- Around 'Currently Listed' ---")
            print(html[idx:idx+3000])
        else:
            mid = len(html) // 2
            print(f"\n--- Middle of page ---")
            print(html[mid:mid+3000])

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
