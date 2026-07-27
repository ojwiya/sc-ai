#!/usr/bin/env python3
"""
Data normalization and enrichment for Your Overseas Home property data.
Prepares data for RAG consumption with clean, consistent formatting.
"""

import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent
INPUT_FILE = DATA_DIR / "properties_data.json"
OUTPUT_FILE = DATA_DIR / "properties_clean.json"

# Country name normalization 
COUNTRY_MAP = {
    'united-states': 'United States',
    'usa': 'United States',
    'france': 'France',
    'spain': 'Spain',
    'portugal': 'Portugal',
    'italy': 'Italy',
    'greece': 'Greece',
    'cyprus': 'Cyprus',
    'ireland': 'Ireland',
    'australia': 'Australia',
    'new-zealand': 'New Zealand',
    'dubai': 'UAE',
    'uae': 'UAE',
    'malta': 'Malta',
    'switzerland': 'Switzerland',
    'canada': 'Canada',
    'turkey': 'Turkey',
    'germany': 'Germany',
}

# Currency symbols
CURRENCY_SYMBOL = {
    'EUR': '€', 'GBP': '£', 'USD': '$', 'AED': 'د.إ',
    'CHF': 'CHF', 'AUD': 'A$', 'NZD': 'NZ$', 'CAD': 'C$',
}

def normalize_property(p):
    """Normalize and enrich a property record."""
    country_slug = p.get('country_slug', 'unknown')
    country_name = COUNTRY_MAP.get(country_slug, country_slug.title())
    
    currency = p.get('currencyCode', 'EUR')
    curr_symbol = CURRENCY_SYMBOL.get(currency, currency)
    
    # Detect property type from title
    title_lower = p.get('title', '').lower()
    if 'villa' in title_lower:
        prop_type = 'Villa'
    elif 'apartment' in title_lower or 'flat' in title_lower:
        prop_type = 'Apartment'
    elif 'house' in title_lower or 'townhouse' in title_lower:
        prop_type = 'House'
    elif 'land' in title_lower or 'plot' in title_lower:
        prop_type = 'Land'
    elif 'commercial' in title_lower or 'restaurant' in title_lower or 'hotel' in title_lower:
        prop_type = 'Commercial'
    else:
        prop_type = 'Other'
    
    # Price bracket
    price = p.get('price', 0)
    if price < 100000:
        price_bracket = 'Budget (<€100k)'
    elif price < 250000:
        price_bracket = 'Affordable (€100k-€250k)'
    elif price < 500000:
        price_bracket = 'Mid-range (€250k-€500k)'
    elif price < 1000000:
        price_bracket = 'Premium (€500k-€1M)'
    else:
        price_bracket = 'Luxury (>€1M)'
    
    # Clean description
    desc = p.get('description', '')
    # Remove excessive whitespace
    desc = ' '.join(desc.split())
    
    return {
        'id': p['id'],
        'title': p.get('title', ''),
        'property_type': prop_type,
        'country_slug': country_slug,
        'country_name': country_name,
        'location': p.get('locationName', ''),
        'price': price,
        'price_formatted': f"{curr_symbol}{price:,.0f}",
        'currency': currency,
        'eur_price': p.get('eurPrice'),
        'gbp_price': p.get('gbpPrice'),
        'price_bracket': price_bracket,
        'bedrooms': p.get('bedrooms') or 0,
        'bathrooms': p.get('bathrooms') or 0,
        'build_size_m2': p.get('buildSize'),
        'plot_size_m2': p.get('plotSize'),
        'latitude': p.get('latitude'),
        'longitude': p.get('longitude'),
        'description': desc,
        'url': p.get('url', ''),
        'image_count': p.get('image_count', 0),
        'thumbnail_url': p.get('thumbnail_url'),
    }


def main():
    if not INPUT_FILE.exists():
        print(f"Input file not found: {INPUT_FILE}")
        return
    
    with open(INPUT_FILE) as f:
        data = json.load(f)
    
    properties = data['properties']
    print(f"Loaded {len(properties)} properties")
    
    # Normalize
    normalized = [normalize_property(p) for p in properties]
    
    # Stats
    from collections import Counter
    countries = Counter(p['country_name'] for p in normalized)
    types = Counter(p['property_type'] for p in normalized)
    brackets = Counter(p['price_bracket'] for p in normalized)
    
    print("\nCountries:")
    for c, n in countries.most_common():
        print(f"  {c}: {n}")
    
    print("\nProperty types:")
    for t, n in types.most_common():
        print(f"  {t}: {n}")
    
    print("\nPrice brackets:")
    for b, n in brackets.most_common():
        print(f"  {b}: {n}")
    
    # Save
    output = {
        'total': len(normalized),
        'country_distribution': dict(countries.most_common()),
        'property_type_distribution': dict(types.most_common()),
        'price_bracket_distribution': dict(brackets.most_common()),
        'properties': normalized
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()