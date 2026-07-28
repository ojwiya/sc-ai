# Makefile for Overseas Property RAG

PYTHON ?= python3
CHROMA_DIR := chroma_db

.PHONY: build search test demo clean check-env

check-env:
	$(PYTHON) scripts/check_env.py

build: check-env
	$(PYTHON) scripts/build_index.py

search:
	$(PYTHON) scripts/search.py --limit 5 "3 bedroom villa in Spain with pool"

test:
	$(PYTHON) -m pytest tests/test_search.py -v

demo:
	$(PYTHON) demo.py

clean:
	rm -rf $(CHROMA_DIR)
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
