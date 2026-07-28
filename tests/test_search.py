"""Verification harness for the RAG search pipeline."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import chromadb
import pytest

# Ensure scripts/ is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from search import search  # noqa: E402

# Save references for teardown (the function's __globals__ is the module namespace)
_SEARCH_GLOBALS = search.__globals__
_ORIGINAL_CHROMA_DIR = _SEARCH_GLOBALS["CHROMA_DIR"]
_ORIGINAL_COLLECTION_NAME = _SEARCH_GLOBALS["COLLECTION_NAME"]


@pytest.fixture
def chroma_client():
    """Create a temporary ChromaDB client with synthetic property data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        client = chromadb.PersistentClient(path=tmpdir)
        collection = client.create_collection(
            name="test_properties",
            metadata={"description": "test collection",
                      "hnsw:space": "cosine"},
        )

        # 10 synthetic properties across 4 countries
        synthetic = [
            {"id": "prop-1", "title": "Villa in Marbella", "country": "spain",
             "location": "Marbella", "price": 500000, "currency": "EUR",
             "bedrooms": 3, "bathrooms": 2},
            {"id": "prop-2", "title": "Apartment in Barcelona", "country": "spain",
             "location": "Barcelona", "price": 250000, "currency": "EUR",
             "bedrooms": 2, "bathrooms": 1},
            {"id": "prop-3", "title": "Farmhouse in Tuscany", "country": "italy",
             "location": "Tuscany", "price": 350000, "currency": "EUR",
             "bedrooms": 4, "bathrooms": 3},
            {"id": "prop-4", "title": "City flat in Rome", "country": "italy",
             "location": "Rome", "price": 180000, "currency": "EUR",
             "bedrooms": 1, "bathrooms": 1},
            {"id": "prop-5", "title": "Beach house in Algarve", "country": "portugal",
             "location": "Algarve", "price": 400000, "currency": "EUR",
             "bedrooms": 3, "bathrooms": 2},
            {"id": "prop-6", "title": "Studio in Lisbon", "country": "portugal",
             "location": "Lisbon", "price": 120000, "currency": "EUR",
             "bedrooms": 0, "bathrooms": 1},
            {"id": "prop-7", "title": "Chalet in Alps", "country": "france",
             "location": "Chamonix", "price": 800000, "currency": "EUR",
             "bedrooms": 5, "bathrooms": 4},
            {"id": "prop-8", "title": "Cottage in Provence", "country": "france",
             "location": "Provence", "price": 220000, "currency": "EUR",
             "bedrooms": 2, "bathrooms": 1},
            {"id": "prop-9", "title": "Penthouse in Madrid", "country": "spain",
             "location": "Madrid", "price": 950000, "currency": "EUR",
             "bedrooms": 4, "bathrooms": 3},
            {"id": "prop-10", "title": "Ruin in Sicily", "country": "italy",
             "location": "Sicily", "price": 50000, "currency": "EUR",
             "bedrooms": 0, "bathrooms": 0},
        ]

        ids = [p["id"] for p in synthetic]
        documents = [
            f"{p['title']}. Located in {p['location']}, {p['country']}. "
            f"Price: EUR{p['price']:,}. {p['bedrooms']} bedrooms, "
            f"{p['bathrooms']} bathrooms."
            for p in synthetic
        ]
        metadatas = [
            {"title": p["title"], "country": p["country"],
             "location": p["location"], "price": p["price"],
             "currency": p["currency"], "bedrooms": p["bedrooms"],
             "bathrooms": p["bathrooms"]}
            for p in synthetic
        ]

        collection.add(ids=ids, documents=documents, metadatas=metadatas)

        # Monkey-patch the search module globals to use the test collection
        _SEARCH_GLOBALS["CHROMA_DIR"] = Path(tmpdir)
        _SEARCH_GLOBALS["COLLECTION_NAME"] = "test_properties"

        yield client

        # Restore original module globals
        _SEARCH_GLOBALS["CHROMA_DIR"] = _ORIGINAL_CHROMA_DIR
        _SEARCH_GLOBALS["COLLECTION_NAME"] = _ORIGINAL_COLLECTION_NAME


class TestCollection:
    """Tests for the ChromaDB collection."""

    def test_collection_exists(self, chroma_client):
        """Collection should exist after fixture setup."""
        collection = chroma_client.get_collection("test_properties")
        assert collection is not None

    def test_collection_count(self, chroma_client):
        """Collection should contain exactly 10 synthetic properties."""
        collection = chroma_client.get_collection("test_properties")
        assert collection.count() == 10


class TestSearchFunction:
    """Tests for the search() function (primary seam)."""

    def test_search_returns_results(self, chroma_client):
        """search() should return results for a canonical query."""
        results = search("villa in Spain", limit=5)
        assert len(results) > 0
        assert len(results) <= 5

    def test_search_result_keys(self, chroma_client):
        """Each result should have the expected keys."""
        results = search("apartment", limit=1)
        assert len(results) == 1
        r = results[0]
        for key in (
            "title", "price", "currency", "location", "country",
            "bedrooms", "bathrooms", "score",
        ):
            assert key in r, f"Missing key: {key}"

    def test_search_scores_descending(self, chroma_client):
        """Results should be ranked by score descending."""
        results = search("property", limit=5)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True), (
            f"Scores not descending: {scores}"
        )

    def test_country_filter(self, chroma_client):
        """Country filter should restrict results."""
        results = search("property", country="spain", limit=10)
        assert all(r["country"] == "spain" for r in results)
        assert len(results) > 0

    def test_max_price_filter(self, chroma_client):
        """Max price filter should restrict results."""
        results = search("property", max_price=200000, limit=10)
        assert all(r["price"] <= 200000 for r in results)
        assert len(results) > 0

    def test_min_price_filter(self, chroma_client):
        """Min price filter should restrict results."""
        results = search("property", min_price=500000, limit=10)
        assert all(r["price"] >= 500000 for r in results)
        assert len(results) > 0

    def test_bedrooms_filter(self, chroma_client):
        """Bedroom filter should restrict results."""
        results = search("property", min_bedrooms=3, limit=10)
        assert all(r["bedrooms"] >= 3 for r in results)
        assert len(results) > 0

    def test_combined_filters(self, chroma_client):
        """Combined filters should work without crash."""
        results = search(
            "villa", country="spain", max_price=600000,
            min_bedrooms=3, limit=5,
        )
        assert all(r["country"] == "spain" for r in results)
        assert all(r["price"] <= 600000 for r in results)
        assert all(r["bedrooms"] >= 3 for r in results)

    def test_nonsense_query_empty(self, chroma_client):
        """Nonsense query should return only very-low-score results."""
        results = search("asdfghjklzxcvbnmqwerty", limit=5)
        if len(results) > 0:
            # Cosine distance for semantically unrelated text hovers near 1.0,
            # yielding scores near 0. A score < 0.25 indicates no real match.
            assert all(r["score"] < 0.25 for r in results), (
                f"Nonsense query returned high-score results: {results}"
            )

    def test_limit(self, chroma_client):
        """Limit should cap results."""
        results = search("property", limit=3)
        assert len(results) <= 3


class TestCLI:
    """Tests for the CLI wrapper (thin seam)."""

    def test_cli_valid_query(self, chroma_client):
        """CLI should exit 0 on valid query."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "search.py"),
             "villa in Spain", "--limit", "3"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_cli_missing_query(self, chroma_client):
        """CLI should exit non-zero on missing query."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "search.py")],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0

    def test_cli_json_output(self, chroma_client):
        """CLI --json should output valid JSON."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "search.py"),
             "villa", "--json", "--limit", "2"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) <= 2
