#!/usr/bin/env python3
"""
Build ChromaDB vector store from scraped property data.
Run once to create the index, then use scripts/search.py to query.

Usage: python3 scripts/build_index.py [--batch-size 200] [--data-file properties_clean.json]
"""
import json, os, sys, argparse, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / 'properties_clean.json'
DEFAULT_CHROMA = ROOT / 'chroma_db'

def format_property_text(p):
    """Format a property into a searchable text chunk for embeddings."""
    currency_map = {"EUR": "€", "GBP": "£", "USD": "$", "CHF": "CHF"}
    curr = currency_map.get(p.get('currencyCode', 'EUR'), p.get('currencyCode', '€'))
    
    parts = [
        p.get('title', 'Untitled'),
        f"Located in {p.get('locationName', 'Unknown')}, {p.get('country_slug', 'Unknown')}",
        f"Price: {curr}{p.get('price', 0):,.0f}",
    ]
    if p.get('bedrooms'):
        parts.append(f"{p['bedrooms']} bedroom{'s' if p['bedrooms'] != 1 else ''}")
    if p.get('bathrooms'):
        parts.append(f"{p['bathrooms']} bathroom{'s' if p['bathrooms'] != 1 else ''}")
    if p.get('buildSize'):
        parts.append(f"Build size: {p['buildSize']} square meters")
    if p.get('plotSize'):
        parts.append(f"Plot size: {p['plotSize']} square meters")
    if p.get('description'):
        parts.append(p['description'][:600])
    
    return ' | '.join(parts)


def main():
    parser = argparse.ArgumentParser(description='Build ChromaDB property index')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for embedding')
    parser.add_argument('--data-file', default=str(DEFAULT_DATA), help='Path to properties_clean.json')
    parser.add_argument('--chroma-dir', default=str(DEFAULT_CHROMA), help='Path to ChromaDB directory')
    parser.add_argument('--collection', default='overseas_properties', help='Collection name')
    args = parser.parse_args()
    
    start_time = time.time()
    
    # Load data
    print(f"Loading {args.data_file}...")
    with open(args.data_file) as f:
        data = json.load(f)
    
    # Handle both array and dict formats
    if isinstance(data, list):
        properties = data
    else:
        properties = data.get('properties', data.get('data', []))
    print(f"Loaded {len(properties)} properties")
    
    # Import chromadb (lazy so check_env catches import issues first)
    import chromadb
    
    # Create client and collection
    client = chromadb.PersistentClient(path=args.chroma_dir)
    try:
        client.delete_collection(args.collection)
        print(f"Deleted existing collection '{args.collection}'")
    except Exception:
        pass
    
    collection = client.create_collection(
        name=args.collection,
        metadata={"description": "Your Overseas Home property listings"}
    )
    
    # Batch insert with malformed record skipping
    total = len(properties)
    indexed = 0
    skipped = 0
    
    for i in range(0, total, args.batch_size):
        batch = properties[i:i + args.batch_size]
        batch_ids = []
        batch_docs = []
        batch_metas = []
        
        for p in batch:
            # Skip malformed records
            if not isinstance(p, dict):
                skipped += 1
                continue
            ref = p.get('reference', p.get('id', ''))
            if not ref:
                skipped += 1
                continue
            
            try:
                batch_ids.append(str(ref))
                batch_docs.append(format_property_text(p))
                batch_metas.append({
                    'title': str(p.get('title', '')),
                    'country': str(p.get('country_slug', p.get('country', ''))),
                    'location': str(p.get('locationName', '')),
                    'price': float(p.get('price', 0)),
                    'currency': str(p.get('currencyCode', 'EUR')),
                    'bedrooms': int(p.get('bedrooms') or 0),
                    'bathrooms': int(p.get('bathrooms') or 0),
                    'buildSize': p.get('buildSize', 0) or 0,
                    'plotSize': p.get('plotSize', 0) or 0,
                })
                indexed += 1
            except Exception as e:
                print(f"  Warning: skipping record {ref}: {e}")
                skipped += 1
        
        if batch_ids:
            collection.add(ids=batch_ids, documents=batch_docs, metadatas=batch_metas)
        
        done = min(i + args.batch_size, total)
        if done % 100 == 0 or done == total:
            elapsed = time.time() - start_time
            print(f"  Processed {done}/{total} ({done*100//total}%) — {indexed} indexed, {skipped} skipped, {elapsed:.0f}s elapsed")
    
    elapsed = time.time() - start_time
    print(f"\nDone. Collection '{args.collection}' has {collection.count()} documents.")
    print(f"Total: {indexed} indexed, {skipped} skipped, {elapsed:.1f}s elapsed")
    print(f"Vector store saved to: {args.chroma_dir}")
    
    # Quick verification
    try:
        results = collection.query(query_texts=["villa in Spain with pool"], n_results=3)
        print(f"\nQuick verification query: 'villa in Spain with pool'")
        for j, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            print(f"  {j+1}. {meta['title']} — {meta['location']} — {meta['currency']}{meta['price']:,.0f}")
    except Exception as e:
        print(f"\nWarning: verification query failed: {e}")


if __name__ == '__main__':
    main()