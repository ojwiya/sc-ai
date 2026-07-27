#!/usr/bin/env python3
"""
RAG Pipeline for Your Overseas Home property search.
Builds a ChromaDB vector store from scraped property data and supports
natural language queries like "find a 3-bedroom villa in Spain under €500k".
"""

import json
import os
import sys
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent
DATA_FILE = DATA_DIR / "properties_data.json"
CHROMA_DIR = DATA_DIR / "chroma_db"

def format_property_text(p):
    """Format a property into a searchable text chunk for embeddings."""
    currency_map = {"EUR": "€", "GBP": "£", "USD": "$"}
    curr = currency_map.get(p.get('currencyCode', 'EUR'), p.get('currencyCode', '€'))
    
    parts = [
        f"Property: {p.get('title', 'Untitled')}",
        f"Country: {p.get('country_slug', 'Unknown').title()}",
        f"Location: {p.get('locationName', 'Unknown')}",
        f"Price: {curr}{p.get('price', 0):,.0f}",
    ]
    
    if p.get('bedrooms'):
        parts.append(f"Bedrooms: {p['bedrooms']}")
    if p.get('bathrooms'):
        parts.append(f"Bathrooms: {p['bathrooms']}")
    if p.get('buildSize'):
        parts.append(f"Build size: {p['buildSize']} m²")
    if p.get('plotSize'):
        parts.append(f"Plot size: {p['plotSize']} m²")
    if p.get('description'):
        # Clean description - truncate to reasonable length
        desc = p['description'][:800]
        parts.append(f"Description: {desc}")
    
    parts.append(f"Property ID: {p['id']}")
    return "\n".join(parts)


def build_vector_store(properties, collection_name="overseas_properties"):
    """Build ChromaDB vector store from properties."""
    try:
        import chromadb
    except ImportError:
        print("Installing chromadb...")
        os.system(f"{sys.executable} -m pip install chromadb -q")
        import chromadb
    
    from chromadb.config import Settings
    
    print(f"Building vector store with {len(properties)} properties...")
    
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Delete existing collection if recreating
    try:
        client.delete_collection(collection_name)
    except:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Your Overseas Home property listings"}
    )
    
    # Batch insert in chunks
    BATCH_SIZE = 100
    for i in range(0, len(properties), BATCH_SIZE):
        batch = properties[i:i + BATCH_SIZE]
        
        ids = [str(p['id']) for p in batch]
        documents = [format_property_text(p) for p in batch]
        metadatas = [{
            'title': p.get('title', ''),
            'country': p.get('country_slug', ''),
            'location': p.get('locationName', ''),
            'price': p['price'],
            'currency': p.get('currencyCode', 'EUR'),
            'bedrooms': p.get('bedrooms') or 0,
            'bathrooms': p.get('bathrooms') or 0,
            'buildSize': p.get('buildSize') or 0,
            'plotSize': p.get('plotSize') or 0,
            'url': p.get('url', ''),
        } for p in batch]
        
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        if (i + BATCH_SIZE) % 500 == 0 or (i + BATCH_SIZE) >= len(properties):
            print(f"  Inserted {min(i + BATCH_SIZE, len(properties))}/{len(properties)}")
    
    print(f"Vector store built: {collection.count()} documents")
    return collection


def search_properties(query, collection, n_results=5):
    """Search properties using natural language query."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    return results


def format_search_results(results):
    """Format ChromaDB search results for display."""
    output = []
    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        output.append(f"\n--- Result {i+1} (similarity: {1-dist:.3f}) ---")
        output.append(doc[:600])
        if len(doc) > 600:
            output.append("... (truncated)")
    return "\n".join(output)


def main():
    if not DATA_FILE.exists():
        print(f"Data file not found: {DATA_FILE}")
        print("Run the scraper first to generate properties_data.json")
        sys.exit(1)
    
    with open(DATA_FILE) as f:
        data = json.load(f)
    
    properties = data['properties']
    print(f"Loaded {len(properties)} properties from {len(data['country_distribution'])} countries")
    
    # Build or load vector store
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    try:
        collection = client.get_collection("overseas_properties")
        print(f"Loaded existing collection: {collection.count()} docs")
    except:
        collection = build_vector_store(properties)
    
    # Interactive search or command-line query
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        results = search_properties(query, collection, n_results=5)
        print(f"\nSearch: \"{query}\"")
        print(format_search_results(results))
    else:
        # Demo searches
        queries = [
            "3 bedroom villa in Spain near the beach under 500000 euros",
            "cheap countryside house in France with land",
            "luxury apartment in Portugal with sea views",
            "ski property in the French Alps",
            "modern apartment in Dubai",
            "farmhouse in Italy with pool",
            "cheap 2 bed apartment in Cyprus",
        ]
        
        for q in queries:
            results = search_properties(q, collection, n_results=3)
            print(f"\n{'='*60}")
            print(f"QUERY: \"{q}\"")
            print(format_search_results(results))
            print()


if __name__ == "__main__":
    main()