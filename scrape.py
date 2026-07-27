#!/usr/bin/env python3
"""
Scrape property data from Your Overseas Home API.
Usage: python3 scrape.py [start_page=1] [end_page=300]
"""
import urllib.request, json, re, os, time, sys

API = 'https://property-portal-api-gw.youroverseashome.com/api/v1/properties/search'
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'properties_data.json')

start_page = int(sys.argv[1]) if len(sys.argv) > 1 else 1
end_page = int(sys.argv[2]) if len(sys.argv) > 2 else 300

# Load existing data if appending
all_props = []
country_counts = {}
seen_ids = set()
if os.path.exists(OUTPUT_FILE) and start_page > 1:
    with open(OUTPUT_FILE) as f:
        existing = json.load(f)
    all_props = existing['properties']
    for p in all_props:
        country_counts[p['country_slug']] = country_counts.get(p['country_slug'], 0) + 1
        seen_ids.add(p['id'])
    print(f"Loaded {len(all_props)} existing properties")

failed = 0
for page in range(start_page, end_page + 1):
    payload = json.dumps({'page': page, 'size': 4}).encode('utf-8')
    req = urllib.request.Request(API, data=payload, headers={
        'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode('utf-8')
        data = json.loads(raw, strict=False)
    except:
        failed += 1
        if failed > 10:
            print(f"Too many failures at page {page}")
            break
        time.sleep(2)
        continue
    
    failed = 0
    props = data.get('data', {}).get('properties', [])
    if not props:
        print(f"Page {page}: empty, done")
        break
    
    for p in props:
        if p['id'] in seen_ids:
            continue
        seen_ids.add(p['id'])
        url = p.get('url', '')
        m = re.match(r'^/(\S+?)/property-for-sale/', url)
        slug = m.group(1) if m else 'unknown'
        simplified = {
            'id': p['id'], 'title': p.get('title', ''), 'country_slug': slug,
            'locationName': p.get('locationName', ''),
            'price': p['price'], 'currencyCode': p.get('currencyCode'),
            'eurPrice': p.get('eurPrice'), 'gbpPrice': p.get('gbpPrice'),
            'bedrooms': p.get('bedrooms'), 'bathrooms': p.get('bathrooms'),
            'plotSize': p.get('plotSize'), 'buildSize': p.get('buildSize'),
            'latitude': p.get('latitude'), 'longitude': p.get('longitude'),
            'description': p.get('description', ''), 'url': url,
            'image_count': len(p.get('images', [])),
            'thumbnail_url': p['images'][0]['thumbnailUrl'] if p.get('images') else None,
        }
        all_props.append(simplified)
        country_counts[slug] = country_counts.get(slug, 0) + 1
    
    if page % 50 == 0:
        print(f"Pg {page}: {len(all_props)} props")
    time.sleep(0.05)

with open(OUTPUT_FILE, 'w') as f:
    json.dump({
        'total': len(all_props),
        'country_distribution': dict(sorted(country_counts.items(), key=lambda x: -x[1])),
        'properties': all_props
    }, f, ensure_ascii=False)

print(f"\nSaved {len(all_props)} properties")
for c, n in sorted(country_counts.items(), key=lambda x: -x[1]):
    print(f"  {c}: {n}")