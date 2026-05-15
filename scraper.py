import json
import re
import requests
from datetime import datetime, timezone

OUTPUT_FILE = "listings.json"
SOURCE_URL  = "https://www.merrittislandcocoabeachhomes.com/merritt-towers-condo/"
HEADERS     = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def load_existing():
    try:
        with open(OUTPUT_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"listings": []}

def parse_listings(html):
    results = []
    try:
        if "Currently Listed Merritt Towers" not in html:
            print("WARNING: 'Currently Listed Merritt Towers' section not found")
            return []

        section = html.split("Currently Listed Merritt Towers")[1]
        for stopper in ["Merritt Island Island Condos", "Market Reports", "Start Your Search"]:
            if stopper in section:
                section = section.split(stopper)[0]

        prop_urls = re.findall(
            r'href="(https://www\.merrittislandcocoabeachhomes\.com/property/(\d+)/)"',
            section
        )
        print(f"Found {len(prop_urls)} property URLs in section")

        blocks = re.split(
            r'https://www\.merrittislandcocoabeachhomes\.com/property/\d+/',
            section
        )

        for i, (url, mls) in enumerate(prop_urls):
            block = blocks[i] if i < len(blocks) else ""
            text  = re.sub(r'<[^>]+>', ' ', block)
            text  = re.sub(r'\s+', ' ', text).strip()

            price_m = re.search(r'\$([0-9,]+)', text)
            if not price_m:
                continue
            price = int(price_m.group(1).replace(',', ''))
            if price < 50000 or price > 5000000:
                continue

            beds_m  = re.search(r'(\d+)\s*Beds?', text, re.I)
            baths_m = re.search(r'(\d+)\s*Baths?', text, re.I)
            sqft_m  = re.search(r'([0-9,]+)\s*sq\.?\s*ft', text, re.I)
            addr_m  = re.search(r'(\d+)\s*S\.?\s*Sykes\s*Creek', text, re.I)
            unit_m  = re.search(r'Unit\s+([A-Z]?\d+[A-Z]?)', text, re.I)

            bldg = str(addr_m.group(1)) if addr_m else "200"
            unit = unit_m.group(1) if unit_m else "—"

            mls_idx = text.find(mls)
            desc    = text[mls_idx + len(mls) + 5:].strip() if mls_idx > -1 else text[-400:]
            desc    = re.sub(r'^MLS\s*', '', desc, flags=re.I).strip()[:400]

            status = ('Pending' if re.search(r'pending', text, re.I) else
                      'Reduced' if re.search(r'reduced|price\s*cut', text, re.I) else
                      'Active')

            results.append({
                "bldg": bldg, "unit": unit, "price": price,
                "beds":   int(beds_m.group(1))  if beds_m  else 0,
                "baths":  int(baths_m.group(1)) if baths_m else 0,
                "sqft":   int(sqft_m.group(1).replace(',','')) if sqft_m else 0,
                "status": status, "mls": mls, "desc": desc
            })
            print(f"  Parsed: Unit {unit} bldg {bldg} ${price:,} MLS#{mls}")

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
    print(f"Fetching {SOURCE_URL}...")
    try:
        r = requests.get(SOURCE_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        html = r.text
        print(f"Page fetched OK ({len(html)} chars)")
        listings = parse_listings(html)
        if listings:
            print(f"\nTotal: {len(listings)} listings found")
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
