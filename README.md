# Overseas Property RAG - Your Overseas Home

Scraped property data from [Your Overseas Home](https://www.youroverseashome.com/) with a RAG (Retrieval-Augmented Generation) pipeline for natural language property search.

## Data

11,960 properties scraped from the API across 9 countries:
- Spain: 7,787
- Cyprus: 1,478
- Portugal: 1,060
- France: 692
- Italy: 558
- USA: 184
- Malta: 76
- Switzerland: 70
- Greece: 55

## Files

- `scrape.py` - Main scraper script (API-based)
- `normalize_data.py` - Data normalization and enrichment
- `rag_pipeline.py` - ChromaDB-based RAG search pipeline
- `.gitignore` - Excludes large data files and ChromaDB store

## Setup

```bash
pip install chromadb
```

## Usage

1. Scrape data:
```bash
python3 scrape.py
```

2. Normalize data:
```bash
python3 normalize_data.py
```

3. Build RAG and search:
```bash
python3 rag_pipeline.py "3 bedroom villa in Spain under 500k"
```

## API

The site uses a REST API at `property-portal-api-gw.youroverseashome.com/api/v1/properties/search` with 128,311 total properties.