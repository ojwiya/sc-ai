#!/usr/bin/env python3
"""Verify all dependencies are available."""
import sys

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

errors = []

# Check Python version
if sys.version_info < (3, 11):
    errors.append(f"ERROR: Python 3.11+ required. Found {sys.version_info.major}.{sys.version_info.minor}")

# Check chromadb
try:
    import chromadb
    print(f"chromadb version: {chromadb.__version__}")
except ImportError as e:
    errors.append("ERROR: chromadb is not installed. Run: pip install chromadb")

if errors:
    for err in errors:
        print(err)
    print("\nOVERALL: NOT READY")
    sys.exit(1)

print("\nOVERALL: READY")
sys.exit(0)