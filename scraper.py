import requests
import json
import re
from datetime import datetime, timezone

SOURCE_URL = "https://www.merrittislandcocoabeachhomes.com/merritt-towers-condo/"
OUTPUT_FILE = "listings.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

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
            sqft_m  = re.search(r'([0-9,]+)\s*sq\.?\s*ft', body, re.I)
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

def load_existing():
    try:
        with open(OUTPUT_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"listings": []}

def save(listings):
    data = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "source":  "merrittislandcocoabeachhomes.com",
        "listings": listings
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(listings)} listings to {OUTPUT_FILE}")

def main():
    print(f"Fetching {SOURCE_URL}...")
    try:
        response = requests.get(SOURCE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        listings = parse_listings(response.text)
        if listings:
            print(f"Found {len(listings)} listings")
            save(listings)
        else:
            print("No listings parsed — keeping existing data unchanged")
            existing = load_existing()
            print(f"Existing listings: {len(existing.get('listings', []))}")
    except Exception as e:
        print(f"Fetch failed: {e}")
        print("Keeping existing data unchanged")

if __name__ == "__main__":
    main()
