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

def parse_listings(html):
    results = []
    try:
        section = html.split("Currently Listed Merritt Towers")[1] if "Currently Listed Merritt Towers" in html else html
        pattern = r'href="(https://www\.merrittislandcocoabeachhomes\.com/property/(\d+)/)"[^>]*>([\s\S]*?)</a>'
        matches = re.finditer(pattern, section, re.IGNORECASE)
        for m in matches:
            url  = m.group(1)
            mls  = m.group(2)
            body = re.sub(r'<[^>]+>', ' ', m.group(3))
            body = re.sub(r'\s+', ' ', body).strip()
            price_m = re.search(r'\$([0-9,]+)', body)
            if not price_m:
                continue
            price = int(price_m.group(1).replace(',', ''))
            if price < 50000 or price > 5000000:
                continue
            beds_m  = re.search(r'(\d+)\s*Beds?', body, re.I)
            baths_m = re.search(r'(\d+)\s*Baths?', body, re.I)
            sqft_m  = re.search(r'([0-9,]+)\s*(?:sq\.?\s*ft|sqft)', body, re.I)
            addr_m  = re.search(r'(\d+)\s*S\s*Sykes\s*Creek', body, re.I)
            unit_m  = re.search(r'Unit\s+([A-Z]?\d+[A-Z]?)', body, re.I)
            mls_idx = body.find(mls)
            desc    = body[mls_idx + len(mls) + 4:].strip() if mls_idx > -1 else ''
            desc    = re.sub(r'^MLS\s*', '', desc, flags=re.I).strip()
            status  = 'Pending' if re.search(r'pending', body, re.I) else \
                      'Reduced' if re.search(r'reduced|price\s*cut', body, re.I) else 'Active'
            results.append({
                "bldg":   str(addr_m.group(1)) if addr_m else "200",
                "unit":   unit_m.group(1) if unit_m else "—",
                "price":  price,
                "beds":   int(beds_m.group(1))  if beds_m  else 0,
                "baths":  int(baths_m.group(1)) if baths_m else 0,
                "sqft":   int(sqft_m.group(1).replace(',', '')) if sqft_m else 0,
                "status": status,
                "mls":    mls,
                "desc":   desc[:400]
            })
    except Exception as e:
        print(f"Parse error: {e}")
    return results

def save(listings):
    data = {
        "updated":  datetime.now(timezone.utc).isoformat(),
        "source":   "merrittislandcocoabeachhomes.com",
        "listings": listings
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(listings)} listings to {OUTPUT_FILE}")

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
            except:
                print("Listings selector not found — trying with full page content anyway")
            html = page.content()
            browser.close()
        listings = parse_listings(html)
        if listings:
            print(f"Found {len(listings)} listings")
            save(listings)
        else:
            print("No listings parsed — keeping existing data unchanged")
            existing = load_existing()
            print(f"Existing listings: {len(existing.get('listings', []))}")
    except Exception as e:
        print(f"Playwright fetch failed: {e}")
        print("Keeping existing data unchanged")

if __name__ == "__main__":
    main()
