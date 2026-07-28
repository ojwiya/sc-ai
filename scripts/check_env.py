#!/usr/bin/env python3
"""Verify all dependencies are available."""
import sys, json

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

deps = {
    'chromadb': 'chromadb',
    'json': 'json',
    're': 're',
    'argparse': 'argparse',
}

results = {}
for name, module in deps.items():
    try:
        __import__(module)
        results[name] = 'OK'
        if name == 'chromadb':
            import chromadb
            print(f"chromadb version: {chromadb.__version__}")
    except ImportError as e:
        results[name] = f'MISSING: {e}'

print(json.dumps(results, indent=2))
all_ok = all(v == 'OK' for v in results.values())
print(f"\nOVERALL: {'READY' if all_ok else 'NOT READY'}")
sys.exit(0 if all_ok else 1)